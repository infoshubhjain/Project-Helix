// ** MANUAL EVENT PARSING HANDLER ** //
// Integration for the manual event parsing feature

document.addEventListener('DOMContentLoaded', function() {
    // Parse modal elements
    const parseModal = document.getElementById('parse-modal');
    const closeParseModalBtn = document.getElementById('close-parse-modal');
    const eventTextInput = document.getElementById('event-text-input');
    const parseEventsBtn = document.getElementById('parse-events-btn');
    const clearParseBtn = document.getElementById('clear-parse-btn');
    const parsedEventsPreview = document.getElementById('parsed-events-preview');
    const parsedEventsList = document.getElementById('parsed-events-list');
    const addAllParsedBtn = document.getElementById('add-all-parsed-btn');
    const cancelParseBtn = document.getElementById('cancel-parse-btn');
    
    // Options
    const autoDetectLocationCheckbox = document.getElementById('auto-detect-location');
    const defaultDurationCheckbox = document.getElementById('default-duration');
    
    let parsedEvents = [];
    let eventParser = null;
    
    // Initialize parser when script loads
    if (window.ManualEventParser) {
        eventParser = new window.ManualEventParser();
    }
    
    // Close parse modal handlers
    if (closeParseModalBtn) {
        closeParseModalBtn.addEventListener('click', () => {
            closeParseModal();
        });
    }
    
    if (cancelParseBtn) {
        cancelParseBtn.addEventListener('click', () => {
            closeParseModal();
        });
    }
    
    // Close modal when clicking outside
    if (parseModal) {
        parseModal.addEventListener('click', (e) => {
            if (e.target === parseModal) {
                closeParseModal();
            }
        });
    }
    
    // Parse events button handler
    if (parseEventsBtn) {
        parseEventsBtn.addEventListener('click', parseEventsFromText);
    }
    
    // Clear button handler
    if (clearParseBtn) {
        clearParseBtn.addEventListener('click', clearParseInput);
    }
    
    // Add all parsed events handler
    if (addAllParsedBtn) {
        addAllParsedBtn.addEventListener('click', addAllParsedEvents);
    }
    
    function parseEventsFromText() {
        const text = eventTextInput.value.trim();
        
        if (!text) {
            showToast('No Text', 'Please enter some event text to parse', 'warning');
            return;
        }
        
        if (!eventParser) {
            showToast('Parser Error', 'Event parser not loaded', 'error');
            return;
        }
        
        try {
            // Get parsing options
            const options = {
                autoDetectLocation: autoDetectLocationCheckbox.checked,
                defaultDuration: defaultDurationCheckbox.checked
            };
            
            // Parse events
            parsedEvents = eventParser.parseEvents(text, options);
            
            if (parsedEvents.length === 0) {
                showToast('No Events Found', 'No events could be detected in the text. Try a different format.', 'warning');
                return;
            }
            
            // Display parsed events
            displayParsedEvents(parsedEvents);
            
            showToast('Events Found', `${parsedEvents.length} event${parsedEvents.length !== 1 ? 's' : ''} detected`, 'success');
            
        } catch (error) {
            console.error('Error parsing events:', error);
            showToast('Parse Error', 'Failed to parse events. Please check your text format.', 'error');
        }
    }
    
    function displayParsedEvents(events) {
        parsedEventsList.innerHTML = '';
        
        events.forEach((event, index) => {
            const eventCard = createParsedEventCard(event, index);
            parsedEventsList.appendChild(eventCard);
        });
        
        // Show preview section
        parsedEventsPreview.style.display = 'block';
        
        // Scroll to preview
        parsedEventsPreview.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
    
    function createParsedEventCard(event, index) {
        const card = document.createElement('div');
        card.className = 'parsed-event-card';
        
        // Format date and time
        const startDate = new Date(event.start);
        const endDate = new Date(event.end);
        
        const dateStr = startDate.toLocaleDateString('en-US', { 
            weekday: 'long', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        });
        
        const startTimeStr = startDate.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit', 
            hour12: true 
        });
        
        const endTimeStr = endDate.toLocaleTimeString('en-US', { 
            hour: 'numeric', 
            minute: '2-digit', 
            hour12: true 
        });
        
        // Confidence indicator
        const confidenceClass = event.confidence >= 80 ? 'high' : 
                               event.confidence >= 60 ? 'medium' : 'low';
        const confidenceText = event.confidence >= 80 ? 'High' : 
                              event.confidence >= 60 ? 'Medium' : 'Low';
        
        card.innerHTML = `
            <div class="parsed-event-header">
                <div class="parsed-event-title">${escapeHtml(event.title)}</div>
                <div class="parsed-event-confidence confidence-${confidenceClass}\">
                    ${confidenceText} Confidence
                </div>
            </div>
            <div class="parsed-event-details">
                <div class="parsed-event-datetime">
                    <span class=\"event-icon\">📅</span>
                    <span>${dateStr}</span>
                    <span class=\"event-icon\">🕐</span>
                    <span>${startTimeStr} - ${endTimeStr}</span>
                </div>
                ${event.location ? `
                    <div class=\"parsed-event-location\">
                        <span class=\"event-icon\">📍</span>
                        <span>${escapeHtml(event.location)}</span>
                    </div>
                ` : ''}
                <div class="parsed-event-description">
                    <span class=\"event-icon\">📝</span>
                    <span>${escapeHtml(event.description)}</span>
                </div>
            </div>
            <div class="parsed-event-actions">
                <button class="add-single-event-btn" data-index="${index}">
                    + Add This Event
                </button>
                <button class="edit-event-btn" data-index="${index}">
                    ✏️ Edit
                </button>
            </div>
        `;
        
        // Add event listeners
        const addSingleBtn = card.querySelector('.add-single-event-btn');
        const editBtn = card.querySelector('.edit-event-btn');
        
        addSingleBtn.addEventListener('click', () => addSingleEvent(event, index));
        editBtn.addEventListener('click', () => editParsedEvent(event, index));
        
        return card;
    }
    
    async function addSingleEvent(event, index) {
        try {
            await addEventToCalendar(event);
            
            // Remove the added event from the list
            parsedEvents.splice(index, 1);
            
            if (parsedEvents.length === 0) {
                closeParseModal();
                showToast('All Events Added', 'All parsed events have been added to your calendar', 'success');
            } else {
                displayParsedEvents(parsedEvents);
                showToast('Event Added', 'Event has been added to your calendar', 'success');
            }
            
        } catch (error) {
            console.error('Error adding event:', error);
            showToast('Error', 'Failed to add event to calendar', 'error');
        }
    }
    
    async function addAllParsedEvents() {
        if (parsedEvents.length === 0) return;
        
        try {
            let successCount = 0;
            let errorCount = 0;
            
            for (const event of parsedEvents) {
                try {
                    await addEventToCalendar(event);
                    successCount++;
                } catch (error) {
                    console.error('Error adding event:', error);
                    errorCount++;
                }
            }
            
            closeParseModal();
            
            if (errorCount === 0) {
                showToast('All Events Added', `${successCount} event${successCount !== 1 ? 's' : ''} added to your calendar`, 'success');
            } else {
                showToast('Partial Success', `${successCount} event${successCount !== 1 ? 's' : ''} added, ${errorCount} failed`, 'warning');
            }
            
        } catch (error) {
            console.error('Error adding events:', error);
            showToast('Error', 'Failed to add events to calendar', 'error');
        }
    }
    
    async function addEventToCalendar(event) {
        // Check if connected to Google Calendar
        if (!window.calendarAPI || !window.calendarAPI.isConnected()) {
            throw new Error('Not connected to Google Calendar');
        }
        
        // Prepare event data for Google Calendar format
        const eventData = {
            summary: event.title,
            location: event.location || '',
            description: event.description || '',
            start: {
                dateTime: event.start.toISOString(),
                timeZone: 'America/Chicago'
            },
            end: {
                dateTime: event.end.toISOString(),
                timeZone: 'America/Chicago'
            }
        };
        
        // Call the Google Calendar API
        const response = await window.calendarAPI.addEvent(eventData);
        
        if (!response) {
            throw new Error('Failed to add event to Google Calendar');
        }
        
        return response;
    }
    
    function editParsedEvent(event, index) {
        // Fill the regular add event form with parsed data
        document.getElementById('event-title').value = event.title;
        document.getElementById('event-location').value = event.location || '';
        document.getElementById('event-description').value = event.description || '';
        
        // Format datetime-local input
        const startDate = new Date(event.start);
        const dateTimeLocal = startDate.toISOString().slice(0, 16);
        document.getElementById('event-date').value = dateTimeLocal;
        
        // Close parse modal and open add event modal
        closeParseModal();
        document.getElementById('event-modal').style.display = 'flex';
        
        showToast('Edit Event', 'Review the event details and click Save to add to calendar', 'info');
    }
    
    function clearParseInput() {
        eventTextInput.value = '';
        parsedEventsPreview.style.display = 'none';
        parsedEvents = [];
    }
    
    function closeParseModal() {
        if (parseModal) {
            parseModal.style.display = 'none';
        }
        clearParseInput();
    }
    
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
});
