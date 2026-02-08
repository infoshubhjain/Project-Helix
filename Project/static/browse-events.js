// ** CO-AUTHORED BY CLAUDE CODE ** //

// Initialize Firebase
// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-app.js";
import { getDatabase, ref, get } from "https://www.gstatic.com/firebasejs/12.6.0/firebase-database.js";
// Import export functions
import { exportToICal, exportToCSV } from './export.js';

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
apiKey: "AIzaSyAKfE_dl9zp5U_BVaqOmsdbjKjb-2KOlFA",
authDomain: "eventflowdatabase.firebaseapp.com",
databaseURL: "https://eventflowdatabase-default-rtdb.firebaseio.com",
projectId: "eventflowdatabase",
storageBucket: "eventflowdatabase.firebasestorage.app",
messagingSenderId: "611561258590",
appId: "1:611561258590:web:16a4d352f06bdbbfad3ecf",
measurementId: "G-0C45LS13MN"
};

  // Initialize Firebase
const app = initializeApp(firebaseConfig);
const db = getDatabase(app);

// Wait for the page to fully load before running our code
document.addEventListener("DOMContentLoaded", function() {

  // Get references to HTML elements we'll use
  const browseContainer = document.getElementById("browse-events");
  const searchInput = document.getElementById("search-events");
  const categorySelect = document.getElementById("filter-category");
  const detailModal = document.getElementById("detail-modal");
  const closeButton = document.getElementById("close-detail");

  // Store all events in a simple array
  let allEvents = [];

  // Pagination variables
  let currentlyDisplayedEvents = []; // Events that match current filter
  let displayedCount = 0; // How many events are currently shown
  const EVENTS_PER_PAGE = 30; // Show 30 events at a time

  // ========== Skeleton loading ==========
  function showSkeleton(container) {
    const count = 6;
    let html = '';
    for (let i = 0; i < count; i++) {
      html += `
        <div class="skeleton-card">
          <div class="skeleton skeleton-line short"></div>
          <div class="skeleton skeleton-line title"></div>
          <div class="skeleton skeleton-line"></div>
          <div class="skeleton skeleton-line"></div>
          <div class="skeleton-footer">
            <div class="skeleton skeleton-tag"></div>
            <div class="skeleton skeleton-btn"></div>
          </div>
        </div>`;
    }
    container.innerHTML = html;
  }

  // ========== STEP 1: Load Events ==========
  async function loadEvents() {
    showSkeleton(browseContainer);
    try {
        const eventsRef = ref(db, "scraped_events");
        const snapshot = await get(eventsRef);
        
        let eventsData = null;
        if (snapshot.exists()) {
            eventsData =  snapshot.val();
        }

        if (!eventsData || Object.keys(eventsData).length === 0) {
            browseContainer.innerHTML = '<p class="no-events-text">No events available</p>';
            return;
        }

        for (let id in eventsData) {
            let event = eventsData[id];
            event.id = id;
            event = parseEventData(event);
            if (isEventInPast(event)) continue;
            allEvents.push(event);
        }

        sortEventsByTime();
        setupCategories();
        displayEvents(allEvents);
    } catch (error) {
        console.error('Error loading events:', error);
        browseContainer.innerHTML = '<p class="no-events-text">Error loading events. Please try again.</p>';
    }
  }

  // Map tag name to CSS class for distinct category colors (WCAG-friendly)
  function getTagClass(tag) {
    if (!tag) return 'tag-general';
    const t = tag.toLowerCase();
    if (t.includes('athletic')) return 'tag-athletics';
    if (t.includes('academic')) return 'tag-academic';
    if (t.includes('art')) return 'tag-arts';
    if (t.includes('sport')) return 'tag-sports';
    if (t.includes('entertainment')) return 'tag-entertainment';
    return 'tag-general';
  }

  // ========== Parse Event Data ==========
  // Convert scraper format to display format
  function parseEventData(event) {
    // Parse ISO datetime strings (e.g., "2025-11-30T14:00:00-06:00")
    if (event.start && event.start.includes('T')) {
      const startDate = new Date(event.start);
      event.start_date = formatDate(startDate);
      event.start_time = formatTime(startDate);
    }

    if (event.end && event.end.includes('T')) {
      const endDate = new Date(event.end);
      event.end_date = formatDate(endDate);
      event.end_time = formatTime(endDate);
    }

    return event;
  }

  // ========== Format Date Helper ==========
  function formatDate(date) {
    // Returns "Month Day, Year" format (e.g., "November 30, 2025")
    const monthNames = [
      "January", "February", "March", "April", "May", "June",
      "July", "August", "September", "October", "November", "December"
    ];
    const month = monthNames[date.getMonth()];
    const day = date.getDate();
    const year = date.getFullYear();
    return `${month} ${day}, ${year}`;
  }

  // ========== Format Time Helper ==========
  function formatTime(date) {
    // Returns "HH:MM AM/PM" format
    let hours = date.getHours();
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12; // Convert to 12-hour format
    return `${hours}:${minutes} ${ampm}`;
  }

  // ========== Sort Events by Date/Time ==========
  function sortEventsByTime() {
    // Simple bubble sort to order events by date and time
    for (let i = 0; i < allEvents.length; i++) {
      for (let j = 0; j < allEvents.length - 1 - i; j++) {
        let event1 = allEvents[j];
        let event2 = allEvents[j + 1];

        // Compare dates and times
        let datetime1 = getEventDateTime(event1);
        let datetime2 = getEventDateTime(event2);

        // If event1 should come after event2, swap them
        if (datetime1 > datetime2) {
          allEvents[j] = event2;
          allEvents[j + 1] = event1;
        }
      }
    }
  }

  // ========== Get Event Date/Time for Comparison ==========
  function getEventDateTime(event) {
    // If no date, put it at the end
    if (!event.start_date || event.start_date === 'Date TBA') {
      return new Date('9999-12-31'); // Far future date
    }

    // Combine date and time into a full datetime string
    let dateStr = event.start_date;
    let timeStr = event.start_time || '00:00';

    // Create a Date object for comparison
    let datetime = new Date(dateStr + ' ' + timeStr);

    // If invalid date, put at end
    if (isNaN(datetime.getTime())) {
      return new Date('9999-12-31');
    }

    return datetime;
  }

  // ========== Check if Event is in the Past ==========
  function isEventInPast(event) {
    // Get today's date at midnight
    let today = new Date();
    today.setHours(0, 0, 0, 0);

    // Get event date
    let eventDate = getEventDateTime(event);

    // Return true if event is before today
    return eventDate < today;
  }

  // ========== STEP 2: Setup Category Filter (dropdown + chips) ==========
  function setupCategories() {
    let categories = [];
    for (let i = 0; i < allEvents.length; i++) {
      let tag = allEvents[i].tag;
      if (tag && !categories.includes(tag)) categories.push(tag);
    }
    categories.sort();

    // Dropdown
    for (let i = 0; i < categories.length; i++) {
      let option = document.createElement('option');
      option.value = categories[i];
      option.textContent = categories[i];
      categorySelect.appendChild(option);
    }

    // Horizontal filter chips
    const chipsContainer = document.getElementById('filter-chips');
    if (!chipsContainer) return;

    const allChip = document.createElement('button');
    allChip.type = 'button';
    allChip.className = 'filter-chip active';
    allChip.textContent = 'All';
    allChip.setAttribute('data-category', 'all');
    allChip.addEventListener('click', () => {
      categorySelect.value = 'all';
      searchEvents();
      setActiveChip('all');
    });
    chipsContainer.appendChild(allChip);

    categories.forEach(cat => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'filter-chip';
      chip.textContent = cat;
      chip.setAttribute('data-category', cat);
      chip.addEventListener('click', () => {
        categorySelect.value = cat;
        searchEvents();
        setActiveChip(cat);
      });
      chipsContainer.appendChild(chip);
    });
  }

  function setActiveChip(value) {
    const chips = document.querySelectorAll('.filter-chip');
    chips.forEach(c => {
      c.classList.toggle('active', c.getAttribute('data-category') === value);
    });
  }

  // ========== STEP 3: Display Events ==========
  // Show events as cards on the page with pagination
  function displayEvents(events, append = false) {
    // Store the filtered events for pagination
    if (!append) {
      currentlyDisplayedEvents = events;
      displayedCount = 0;
      browseContainer.innerHTML = ''; // Clear existing cards
    }

    // If no events, show a message
    if (events.length === 0) {
      browseContainer.innerHTML = '<p class="no-events-text">No events found</p>';
      return;
    }

    // Calculate how many events to show
    const endIndex = Math.min(displayedCount + EVENTS_PER_PAGE, events.length);

    // Create cards for the next batch of events
    for (let i = displayedCount; i < endIndex; i++) {
      let card = createEventCard(events[i]);
      browseContainer.appendChild(card);
    }

    // Update displayed count
    displayedCount = endIndex;

    // Add or update the "Load More" button
    updateLoadMoreButton();
  }

  // ========== Update Load More Button ==========
  function updateLoadMoreButton() {
    // Remove existing button if present
    const existingButton = document.getElementById('load-more-btn');
    if (existingButton) {
      existingButton.remove();
    }

    // Only show button if there are more events to load
    if (displayedCount < currentlyDisplayedEvents.length) {
      const loadMoreBtn = document.createElement('button');
      loadMoreBtn.id = 'load-more-btn';
      loadMoreBtn.className = 'load-more-btn';
      loadMoreBtn.textContent = `Load More (${currentlyDisplayedEvents.length - displayedCount} remaining)`;
      loadMoreBtn.onclick = loadMoreEvents;
      browseContainer.appendChild(loadMoreBtn);
    }
  }

  // ========== Load More Events ==========
  function loadMoreEvents() {
    displayEvents(currentlyDisplayedEvents, true);
  }

  // ========== STEP 4: Create a Single Event Card (glass style) ==========
  const syncIcon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>';

  function createEventCard(event) {
    let card = document.createElement('div');
    card.className = 'event-card-browse';

    let time = event.start_time;
    if (event.start_time == "12:00 AM" && event.end_time == "11:59 PM") time = "All Day";

    const tag = event.tag || 'General';
    const tagClass = getTagClass(tag);
    const dateStr = event.start_date || 'Date TBA';
    const timeStr = time || 'Time TBA';
    const locationStr = event.location || 'Location TBA';
    const title = (event.summary || 'Untitled Event').replace(/</g, '&lt;').replace(/>/g, '&gt;');

    let html = '<div class="event-card-meta">';
    html += '<span>📅 ' + dateStr + '</span>';
    html += '<span>🕐 ' + timeStr + '</span>';
    html += '</div>';
    html += '<div class="event-card-title">' + title + '</div>';
    html += '<div class="event-card-info"><strong>📍</strong><span>' + locationStr + '</span></div>';
    html += '<div class="event-card-footer">';
    html += '<span class="event-tag ' + tagClass + '">' + tag.replace(/</g, '&lt;') + '</span>';
    html += '<div class="card-actions">';
    html += '<button type="button" class="show-more-btn">Details</button>';
    html += '<button type="button" class="add-to-calendar-btn" title="Add to Google Calendar">' + syncIcon + '</button>';
    html += '</div></div>';

    card.innerHTML = html;

    card.querySelector('.show-more-btn').onclick = (e) => { e.stopPropagation(); showEventDetails(event); };
    card.querySelector('.add-to-calendar-btn').onclick = (e) => { e.stopPropagation(); addToCalendar(event); };

    return card;
  }

  // ========== STEP 5: Show Event Details in Modal ==========
  function showEventDetails(event) {
    // Fill in the modal with event information
    document.getElementById('detail-title').textContent = event.summary || 'Untitled Event';
    document.getElementById('detail-date').textContent = event.start_date || 'TBA';

    // Set time value to 'All Day' if the event lasts the whole day; else make it time listed in the event data
    if (event.start_time == "12:00 AM" && event.end_time == "11:59 PM") {
        document.getElementById('detail-time').textContent = "All Day";
    } else {
        document.getElementById('detail-time').textContent = (event.start_time || '') + ' - ' + (event.end_time || '');
    }

    document.getElementById('detail-location').textContent = event.location || 'TBA';
    const detailTag = document.getElementById('detail-tag');
    detailTag.textContent = event.tag || 'General';
    detailTag.className = 'event-tag ' + getTagClass(event.tag);
    document.getElementById('detail-description').textContent = event.description || 'No description available.';

    // Set the event link if it exists
    let linkElement = document.getElementById('detail-link');
    if (event.htmlLink) {
      linkElement.href = event.htmlLink;
      linkElement.style.display = 'inline-block';
    } else {
      linkElement.style.display = 'none';
    }

    // Show the modal
    detailModal.style.display = 'flex';
  }

  // ========== STEP 6: Add to Calendar ==========
  async function addToCalendar(event) {
    // Check if user is connected to Google Calendar
    if (!window.calendarAPI || !window.calendarAPI.isConnected()) {
      showToast('Not Connected', 'Please connect your Google Calendar first!', 'warning');
      return;
    }

    try {
      // Prepare event data for Google Calendar format
      const eventData = {
        summary: event.summary || 'Untitled Event',
        location: event.location || '',
        description: event.description || '',
        start: {
          dateTime: event.start,
          timeZone: 'America/Chicago'
        },
        end: {
          dateTime: event.end,
          timeZone: 'America/Chicago'
        }
      };

      // Call the Flask backend to add event
      const response = await window.calendarAPI.addEvent(eventData)
      if (response) {
        showToast('Event Added', `"${event.summary}" was added to your Google Calendar`, 'success');

        // Refresh the calendar iframes to show the new event
        refreshCalendars();
      } else {
        showToast('Failed', 'Could not add event to calendar', 'error');
      }

    } catch (error) {
      console.error('Error adding event to calendar:', error);
      showToast('Error', 'Failed to add event to calendar. Please try again.', 'error');
    }
  }

  // ========== Refresh Calendar Iframes ==========
  function refreshCalendars() {
    // Refresh main calendar iframe
    const mainIframe = document.getElementById('calendar-iframe');
    if (mainIframe && mainIframe.src) {
      mainIframe.src = mainIframe.src; // Force reload by resetting src
    }

    // Refresh today's agenda iframe
    const agendaIframe = document.getElementById('today-agenda-iframe');
    if (agendaIframe && agendaIframe.src) {
      agendaIframe.src = agendaIframe.src; // Force reload by resetting src
    }

    console.log('📅 Calendars refreshed');
  }

  // ========== STEP 7: Search Function ==========
  // Filter events based on search text
  function searchEvents() {
    let searchText = searchInput.value.toLowerCase();
    let selectedCategory = categorySelect.value;
    let filtered = [];

    // Go through all events
    for (let i = 0; i < allEvents.length; i++) {
      let event = allEvents[i];

      // Check if event matches search text
      let matchesSearch = false;
      if (searchText === '') {
        matchesSearch = true; // Empty search matches everything
      } else if (event.summary && event.summary.toLowerCase().includes(searchText)) {
        matchesSearch = true;
      } else if (event.description && event.description.toLowerCase().includes(searchText)) {
        matchesSearch = true;
      } else if (event.location && event.location.toLowerCase().includes(searchText)) {
        matchesSearch = true;
      }

      // Check if event matches selected category
      let matchesCategory = false;
      if (selectedCategory === 'all') {
        matchesCategory = true;
      } else if (event.tag === selectedCategory) {
        matchesCategory = true;
      }

      // If both match, add to filtered list
      if (matchesSearch && matchesCategory) {
        filtered.push(event);
      }
    }

    // Display the filtered events
    displayEvents(filtered);
  }

  // ========== STEP 8: Event Listeners ==========
  // When user types in search box
  searchInput.addEventListener('input', searchEvents);

  // When user changes category dropdown, sync chips
  categorySelect.addEventListener('change', () => {
    searchEvents();
    setActiveChip(categorySelect.value);
  });

  // When user clicks X to close modal
  closeButton.addEventListener('click', function() {
    detailModal.style.display = 'none';
  });

  // When user clicks outside modal, close it
  detailModal.addEventListener('click', function(event) {
    if (event.target === detailModal) {
      detailModal.style.display = 'none';
    }
  });

  // ========== EXPORT FUNCTIONALITY ==========
  // Export to iCal button
  const exportICalBtn = document.getElementById('export-ical-btn');
  if (exportICalBtn) {
    exportICalBtn.addEventListener('click', () => {
      exportToICal(currentlyDisplayedEvents.length > 0 ? currentlyDisplayedEvents : allEvents);
    });
  }

  // Export to CSV button
  const exportCSVBtn = document.getElementById('export-csv-btn');
  if (exportCSVBtn) {
    exportCSVBtn.addEventListener('click', () => {
      exportToCSV(currentlyDisplayedEvents.length > 0 ? currentlyDisplayedEvents : allEvents);
    });
  }

  // ========== START THE APP ==========
  loadEvents();
});