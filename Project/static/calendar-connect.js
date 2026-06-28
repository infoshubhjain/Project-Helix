// Google Calendar Connection Script

let tokenClient;
let gapiInited = false;
let gisInited = false;

// sessionStorage keys — tab-scoped, cleared on close (more secure than localStorage)
const TOKEN_STORAGE_KEY  = 'google_calendar_token';
const TOKEN_EXPIRY_KEY   = 'google_calendar_token_expiry';

// How many minutes before expiry to trigger a silent refresh
const REFRESH_BEFORE_EXPIRY_MINUTES = 5;

// Max attempts to wait for Google libraries before giving up
const MAX_INIT_RETRIES = 10;
let _initRetries = 0;

// ── Initialisation ──────────────────────────────────────────────────────────

document.addEventListener('DOMContentLoaded', function () {
    console.log('🔄 Starting Google Calendar initialisation…');
    setTimeout(initializeGoogleCalendar, 1000);
});

function initializeGoogleCalendar() {
    // Bail out if credentials are not configured (placeholder values)
    if (typeof GOOGLE_CLIENT_ID === 'undefined' ||
        typeof GOOGLE_API_KEY   === 'undefined' ||
        GOOGLE_CLIENT_ID.includes('YOUR_') ||
        GOOGLE_API_KEY.includes('YOUR_')) {
        console.warn('⚠️ Google API credentials not configured; disabling Google Calendar features');
        disableCalendarConnectUI();
        return;
    }

    // Guard against infinite retry if Google CDN is unreachable (e.g. ad-blocker)
    if (_initRetries >= MAX_INIT_RETRIES) {
        console.warn('⚠️ Google libraries did not load after ' + MAX_INIT_RETRIES + ' attempts; disabling calendar');
        disableCalendarConnectUI();
        return;
    }

    const gapiReady  = typeof gapi !== 'undefined';
    const googleReady = typeof google !== 'undefined' && google.accounts;

    if (!gapiReady || !googleReady) {
        _initRetries++;
        console.log(`⏳ Waiting for Google libraries (attempt ${_initRetries}/${MAX_INIT_RETRIES})…`);
        setTimeout(initializeGoogleCalendar, 1000);
        return;
    }

    gapi.load('client', initGapiClient);
    initGisClient();
}

function disableCalendarConnectUI() {
    const connectBtn = document.getElementById('connect-calendar-btn');
    if (connectBtn) {
        connectBtn.textContent = 'Connect Google Calendar';
        connectBtn.disabled    = true;
        connectBtn.style.opacity = '0.6';
        connectBtn.style.cursor  = 'not-allowed';
        connectBtn.title = 'Google Calendar integration is not configured for this deployment.';
    }
    if (window.showToast) {
        window.showToast(
            'Google Calendar Disabled',
            'Calendar integration is not configured on this site. You can still browse events and export them.',
            'info',
            6000
        );
    }
}

async function initGapiClient() {
    try {
        await gapi.client.init({
            apiKey: GOOGLE_API_KEY,
            discoveryDocs: ['https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest'],
        });
        gapiInited = true;
        console.log('✅ Google API initialised');
        checkIfReady();
    } catch (error) {
        console.error('❌ Error initialising GAPI:', error);
        showNotification('Error initialising Google API. Please check your API key.', 'error');
    }
}

function initGisClient() {
    try {
        tokenClient = google.accounts.oauth2.initTokenClient({
            client_id: GOOGLE_CLIENT_ID,
            scope: 'https://www.googleapis.com/auth/calendar.readonly https://www.googleapis.com/auth/calendar.events',
            callback: '',   // set dynamically per request
            prompt: '',
        });
        gisInited = true;
        console.log('✅ Google Identity Services initialised');
        checkIfReady();
    } catch (error) {
        console.error('❌ Error initialising GIS:', error);
        showNotification('Error initialising Google Sign-In. Please check your Client ID.', 'error');
    }
}

function checkIfReady() {
    if (!gapiInited || !gisInited) return;

    console.log('✅ Google Calendar ready');

    const connectBtn = document.getElementById('connect-calendar-btn');
    if (connectBtn) {
        connectBtn.onclick       = handleConnectClick;
        connectBtn.style.opacity = '1';
        connectBtn.style.cursor  = 'pointer';
    }

    const disconnectBtn = document.getElementById('disconnect-btn');
    if (disconnectBtn) disconnectBtn.onclick = handleDisconnectClick;

    const refreshBtn = document.getElementById('refresh-calendar-btn');
    if (refreshBtn) refreshBtn.onclick = handleRefreshClick;

    restoreTokenFromStorage();
}

// ── Token storage (sessionStorage — cleared when tab closes) ────────────────

function saveTokenToStorage(token) {
    try {
        sessionStorage.setItem(TOKEN_STORAGE_KEY, JSON.stringify(token));
        const expiryTime = Date.now() + (token.expires_in || 3600) * 1000;
        sessionStorage.setItem(TOKEN_EXPIRY_KEY, expiryTime.toString());
        console.log('💾 Token saved to sessionStorage');
    } catch (error) {
        console.error('❌ Error saving token:', error);
    }
}

function restoreTokenFromStorage() {
    try {
        const savedToken = sessionStorage.getItem(TOKEN_STORAGE_KEY);
        const expiryTime = sessionStorage.getItem(TOKEN_EXPIRY_KEY);

        if (!savedToken || !expiryTime) {
            console.log('📭 No saved token found');
            return;
        }

        const now    = Date.now();
        const expiry = parseInt(expiryTime);

        if (now >= expiry) {
            console.log('⏰ Saved token expired, clearing…');
            clearStoredToken();
            return;
        }

        const token = JSON.parse(savedToken);
        gapi.client.setToken(token);
        console.log('✅ Token restored from sessionStorage');

        const timeUntilExpiry = expiry - now;
        console.log(`⏱️ Token expires in ${Math.floor(timeUntilExpiry / 60000)} minutes`);

        scheduleTokenRefresh(timeUntilExpiry);
        onCalendarConnected();
    } catch (error) {
        console.error('❌ Error restoring token:', error);
        clearStoredToken();
    }
}

function clearStoredToken() {
    sessionStorage.removeItem(TOKEN_STORAGE_KEY);
    sessionStorage.removeItem(TOKEN_EXPIRY_KEY);
    console.log('🗑️ Cleared stored token');
}

function scheduleTokenRefresh(timeUntilExpiryMs) {
    const refreshTimeMs = REFRESH_BEFORE_EXPIRY_MINUTES * 60 * 1000;
    if (timeUntilExpiryMs > refreshTimeMs) {
        setTimeout(() => {
            console.log('⏰ Token expiring soon, attempting silent refresh…');
            silentlyRefreshToken();
        }, timeUntilExpiryMs - refreshTimeMs);
    }
}

// ── Token refresh ───────────────────────────────────────────────────────────

function silentlyRefreshToken() {
    if (!tokenClient) {
        console.error('❌ Token client not initialised');
        return;
    }

    tokenClient.callback = async (response) => {
        if (response.error !== undefined) {
            console.error('❌ Silent refresh failed:', response.error);
            showNotification('Your session expired. Please reconnect to Google Calendar.', 'warning');
            clearStoredToken();
            onCalendarDisconnected();
            return;
        }

        console.log('✅ Token silently refreshed');
        saveTokenToStorage(response);
        showNotification('Session refreshed successfully!', 'success');

        const expiryTime      = parseInt(sessionStorage.getItem(TOKEN_EXPIRY_KEY));
        const timeUntilExpiry = expiryTime - Date.now();
        scheduleTokenRefresh(timeUntilExpiry);
    };

    tokenClient.requestAccessToken({ prompt: '' });
}

// ── Button handlers ─────────────────────────────────────────────────────────

function handleRefreshClick() {
    console.log('🔄 Manually refreshing calendars…');
    const mainIframe = document.getElementById('calendar-iframe');
    if (mainIframe && mainIframe.src) mainIframe.src = mainIframe.src;

    const agendaIframe = document.getElementById('today-agenda-iframe');
    if (agendaIframe && agendaIframe.src) agendaIframe.src = agendaIframe.src;

    showNotification('Calendars refreshed!', 'success');
}

function handleConnectClick() {
    if (!gapiInited || !gisInited) {
        showNotification('Google Calendar is still loading. Please wait a moment and try again.', 'warning');
        return;
    }

    tokenClient.callback = async (response) => {
        if (response.error !== undefined) {
            console.error('❌ Auth error:', response);
            showNotification('Failed to connect to Google Calendar. Please try again.', 'error');
            return;
        }

        console.log('✅ Successfully authenticated');
        saveTokenToStorage(response);
        await onCalendarConnected();
    };

    if (gapi.client.getToken() === null) {
        tokenClient.requestAccessToken({ prompt: 'consent' });
    } else {
        tokenClient.requestAccessToken({ prompt: '' });
    }
}

function handleDisconnectClick() {
    const token = gapi.client.getToken();
    if (token !== null) {
        google.accounts.oauth2.revoke(token.access_token, () => {
            console.log('Token revoked');
        });
        gapi.client.setToken(null);
    }
    clearStoredToken();
    onCalendarDisconnected();
}

// ── Connected / Disconnected state ──────────────────────────────────────────

async function onCalendarConnected() {
    try {
        const response  = await gapi.client.calendar.calendarList.list({
            minAccessRole: 'reader',
            showHidden: false,
        });

        const calendars = response.result.items || [];
        if (calendars.length === 0) {
            showNotification('No calendars found in your Google account.', 'warning');
            return;
        }

        const primaryCalendar = calendars.find(cal => cal.primary) || calendars[0];
        const userEmail       = primaryCalendar.id;

        console.log(`📧 Connected as: ${userEmail}`);
        console.log(`📅 Found ${calendars.length} calendars`);

        document.getElementById('connect-calendar-btn').style.display = 'none';
        document.getElementById('connection-status').style.display    = 'inline-block';
        document.getElementById('user-email').textContent             = userEmail;

        const overlay = document.getElementById('calendar-overlay');
        if (overlay) overlay.style.display = 'none';

        const iframe        = document.getElementById('calendar-iframe');
        const userTimezone  = Intl.DateTimeFormat().resolvedOptions().timeZone;

        let iframeSrc = 'https://calendar.google.com/calendar/embed?';
        calendars.forEach(cal => {
            if (cal.selected !== false) {
                iframeSrc += `src=${encodeURIComponent(cal.id)}&`;
                if (cal.backgroundColor) {
                    iframeSrc += `color=${encodeURIComponent(cal.backgroundColor.replace('#', '%23'))}&`;
                }
            }
        });
        iframeSrc += `ctz=${encodeURIComponent(userTimezone)}&mode=MONTH&showTitle=0&showNav=1&showDate=1&showPrint=0&showTabs=1&showCalendars=1`;
        iframe.src = iframeSrc;

        const todayIframe = document.getElementById('today-agenda-iframe');
        if (todayIframe) {
            let agendaSrc = 'https://calendar.google.com/calendar/embed?mode=AGENDA';
            calendars.forEach(cal => {
                if (cal.selected !== false) {
                    agendaSrc += `&src=${encodeURIComponent(cal.id)}`;
                }
            });
            agendaSrc += `&ctz=${encodeURIComponent(userTimezone)}&showTitle=0&showNav=0&showDate=0&showPrint=0&showTabs=0&showCalendars=0&showTz=0`;
            todayIframe.src = agendaSrc;
        }

        showNotification(`Successfully connected ${calendars.length} calendar${calendars.length !== 1 ? 's' : ''}!`, 'success');

    } catch (error) {
        console.error('❌ Error loading calendar:', error);
        showNotification('Error loading calendar. Please try again.', 'error');
    }
}

function onCalendarDisconnected() {
    console.log('🔌 Disconnecting from Google Calendar');

    document.getElementById('connect-calendar-btn').style.display = 'inline-block';
    document.getElementById('connection-status').style.display    = 'none';
    document.getElementById('user-email').textContent             = '';

    const overlay = document.getElementById('calendar-overlay');
    if (overlay) overlay.style.display = 'flex';

    const iframe = document.getElementById('calendar-iframe');
    if (iframe) {
        iframe.src = 'https://calendar.google.com/calendar/embed?src=en.usa%23holiday%40group.v.calendar.google.com&ctz=America/Chicago&mode=MONTH&showTitle=0&showNav=1&showDate=1&showPrint=0&showTabs=0&showCalendars=0';
    }

    const todayIframe = document.getElementById('today-agenda-iframe');
    if (todayIframe) {
        todayIframe.src = 'https://calendar.google.com/calendar/embed?mode=AGENDA&showTitle=0&showNav=0&showDate=0&showPrint=0&showTabs=0&showCalendars=0&showTz=0&height=400&wkst=1&ctz=America/Chicago&src=en.usa%23holiday%40group.v.calendar.google.com';
    }

    const upcomingEvents = document.getElementById('upcoming-events');
    if (upcomingEvents) {
        upcomingEvents.innerHTML = '<p class="no-events-text">Connect your calendar to see upcoming events</p>';
    }

    showNotification('Disconnected from Google Calendar', 'info');
}

// showEventDetails for Google Calendar events (not scraped events)
function showEventDetails(event) {
    const modal = document.getElementById('detail-modal');
    if (!modal) return;

    const start     = event.start.dateTime || event.start.date;
    const startDate = new Date(start);

    const titleEl = document.getElementById('detail-title');
    const dateEl  = document.getElementById('detail-date');
    const timeEl  = document.getElementById('detail-time');
    const locEl   = document.getElementById('detail-location');
    const descEl  = document.getElementById('detail-description');

    if (titleEl) titleEl.textContent = event.summary || 'Untitled Event';
    if (dateEl)  dateEl.textContent  = startDate.toLocaleDateString();
    if (timeEl)  timeEl.textContent  = event.start.dateTime
        ? startDate.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
        : 'All day';
    if (locEl)   locEl.textContent   = event.location || 'No location';
    if (descEl)  descEl.textContent  = event.description || 'No description';

    const link = document.getElementById('detail-link');
    if (link) {
        if (event.htmlLink) {
            link.href          = event.htmlLink;
            link.style.display = 'inline-block';
        } else {
            link.style.display = 'none';
        }
    }

    modal.style.display = 'flex';
}

// ── Helpers ─────────────────────────────────────────────────────────────────

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function showNotification(message, type = 'info') {
    if (window.showToast) {
        const titles = { success: 'Success', warning: 'Warning', error: 'Error', info: 'Info' };
        window.showToast(titles[type] || 'Info', message, type);
        return;
    }
    console.log(`[${type.toUpperCase()}] ${message}`);
}

// ── Public API ───────────────────────────────────────────────────────────────

window.calendarAPI = {
    isConnected: () => {
        try {
            return typeof gapi !== 'undefined' && gapi.client && gapi.client.getToken() !== null;
        } catch (e) {
            return false;
        }
    },
    getToken: () => {
        try {
            return typeof gapi !== 'undefined' && gapi.client ? gapi.client.getToken() : null;
        } catch (e) {
            return null;
        }
    },
    addEvent: async (eventDetails) => {
        if (!window.calendarAPI.isConnected()) {
            throw new Error('Not connected to Google Calendar');
        }
        return await gapi.client.calendar.events.insert({
            calendarId: 'primary',
            resource: eventDetails,
        });
    },
};
