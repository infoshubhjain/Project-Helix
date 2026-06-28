// ** CO-AUTHORED BY CLAUDE CODE ** //

// Wait for the page to fully load before running our code
document.addEventListener("DOMContentLoaded", function () {

  // Get references to HTML elements we'll use
  const browseContainer = document.getElementById("browse-events");
  const searchInput = document.getElementById("search-events");
  const categorySelect = document.getElementById("filter-category");
  const detailModal = document.getElementById("detail-modal");
  const closeButton = document.getElementById("close-detail");
  
  // Advanced filter elements
  const dateFilter = document.getElementById("date-filter");
  const locationFilter = document.getElementById("location-filter");
  const timeFilter = document.getElementById("time-filter");
  const customDateGroup = document.getElementById("custom-date-group");
  const startDateInput = document.getElementById("start-date");
  const endDateInput = document.getElementById("end-date");
  const clearFiltersBtn = document.getElementById("clear-filters");
  const activeFiltersDisplay = document.getElementById("active-filters");

  // Store all events in a simple array
  let allEvents = [];

  // Enhanced pagination variables
  let currentlyDisplayedEvents = []; // Events that match current filter
  let displayedCount = 0; // How many events are currently shown
  const EVENTS_PER_PAGE = 20; // Reduced for better performance
  let isLoading = false; // Prevent duplicate loading
  let hasMoreEvents = true; // Track if more events available
  let totalEventsFound = 0; // Total events matching current filter

  // Intersection Observer for infinite scroll — created once, never recreated per filter
  const intersectionObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting && !isLoading && hasMoreEvents) {
          loadMoreEvents();
        }
      });
    },
    { root: null, rootMargin: '100px', threshold: 0.1 }
  );

  // Fuse.js instance for fuzzy search
  let fuse = null;

  // ========== Enhanced Skeleton loading ==========
  function showSkeleton(container, count = 6) {
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

  function showLoadingSpinner() {
    const spinner = document.createElement('div');
    spinner.className = 'loading-spinner';
    spinner.innerHTML = `
      <div class="spinner"></div>
      <p>Loading more events...</p>
    `;
    return spinner;
  }

  function observeLoadMoreTrigger() {
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (loadMoreBtn && intersectionObserver) {
      intersectionObserver.observe(loadMoreBtn);
    }
  }

  function unobserveLoadMoreTrigger() {
    const loadMoreBtn = document.getElementById('load-more-btn');
    if (loadMoreBtn && intersectionObserver) {
      intersectionObserver.unobserve(loadMoreBtn);
    }
  }

  // ========== STEP 1: Load Events ==========
  async function loadEvents() {
    showSkeleton(browseContainer);
    try {
      // Fetch from static JSON file instead of Firebase
      // The file is committed to the repo by the scraper
      const candidateUrls = [
        new URL('Project/scraped_events.json', window.location.href).toString(),
        new URL('./Project/scraped_events.json', window.location.href).toString(),
      ];

      let response = null;
      let lastError = null;
      for (const url of candidateUrls) {
        try {
          response = await fetch(url, { cache: 'no-store' });
          if (response && response.ok) {
            break;
          }
        } catch (e) {
          lastError = e;
          response = null;
        }
      }

      if (!response) {
        throw lastError || new Error('Failed to fetch events JSON');
      }

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const eventsData = await response.json();

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

      // Initialize Fuse.js for fuzzy search
      fuse = new Fuse(allEvents, {
        keys: ['summary', 'description', 'location'],
        threshold: 0.4, // Lower = stricter matching
        ignoreLocation: true
      });
      console.log('Project Helix: Fuse.js initialized with ' + allEvents.length + ' events.');

      displayEvents(allEvents);
    } catch (error) {
      console.error('Error loading events:', error);
      browseContainer.innerHTML = '<p class="no-events-text">Error loading events. Please try again later.</p>';
    }
  }

  function escapeHtml(str) {
    const d = document.createElement('div');
    d.textContent = String(str == null ? '' : str);
    return d.innerHTML;
  }

  // Map tag name to CSS class for distinct category colors (WCAG-friendly)
  function getTagClass(tag) {
    if (!tag) return 'tag-general';
    const t = tag.toLowerCase();
    if (t.includes('free food')) return 'tag-freefood';
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
    // Normalize common schema variants from different scraper sources
    event.summary = (event.summary || event.title || event.name || 'Untitled Event').toString().trim();
    event.location = (event.location || event.venue || 'Location TBA').toString().trim();
    event.tag = (event.tag || event.category || 'General').toString().trim();
    event.htmlLink = (event.htmlLink || event.link || event.url || '').toString().trim();
    event.description = normalizeDescription(
      event.description || event.desc || event.event_description || event.details || ''
    );

    // Parse ISO datetime strings (e.g., "2025-11-30T14:00:00-06:00")
    if (event.start && typeof event.start === 'string' && event.start.includes('T')) {
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

  function normalizeDescription(rawValue) {
    if (!rawValue) return '';
    const div = document.createElement('div');
    div.innerHTML = String(rawValue);
    return div.textContent.replace(/\s+/g, ' ').trim();
  }

  function buildDescriptionPreview(event) {
    if (!event.description) return 'No description provided by source.';
    if (event.description.length <= 140) return event.description;
    return `${event.description.slice(0, 137)}...`;
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
    allEvents.sort((a, b) => getEventDateTime(a) - getEventDateTime(b));
  }

  // ========== Get Event Date/Time for Comparison ==========
  function getEventDateTime(event) {
    // Prefer the ISO start field set by the scraper
    if (event.start) {
      const d = new Date(event.start);
      if (!isNaN(d.getTime())) return d;
    }

    if (!event.start_date || event.start_date === 'Date TBA') {
      return new Date('9999-12-31');
    }

    const datetime = new Date(event.start_date + ' ' + (event.start_time || '00:00'));
    return isNaN(datetime.getTime()) ? new Date('9999-12-31') : datetime;
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

  // ========== Advanced Filter Functions ==========
  function setupAdvancedFilters() {
    // Date filter change handler
    if (dateFilter) {
      dateFilter.addEventListener('change', () => {
        const value = dateFilter.value;
        if (value === 'custom') {
          customDateGroup.style.display = 'flex';
          // Set default dates to today and next week
          const today = new Date();
          const nextWeek = new Date(today.getTime() + 7 * 24 * 60 * 60 * 1000);
          startDateInput.value = today.toISOString().split('T')[0];
          endDateInput.value = nextWeek.toISOString().split('T')[0];
        } else {
          customDateGroup.style.display = 'none';
        }
        searchEvents();
      });
    }
    
    // Location filter change handler
    if (locationFilter) {
      locationFilter.addEventListener('change', searchEvents);
    }
    
    // Time filter change handler
    if (timeFilter) {
      timeFilter.addEventListener('change', searchEvents);
    }
    
    // Custom date change handlers
    if (startDateInput) {
      startDateInput.addEventListener('change', searchEvents);
    }
    if (endDateInput) {
      endDateInput.addEventListener('change', searchEvents);
    }
    
    // Clear filters button
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener('click', clearAllFilters);
    }
  }
  
  function clearAllFilters() {
    if (searchInput) searchInput.value = '';
    if (categorySelect) categorySelect.value = 'all';
    if (dateFilter) dateFilter.value = 'all';
    if (locationFilter) locationFilter.value = 'all';
    if (timeFilter) timeFilter.value = 'all';
    if (customDateGroup) customDateGroup.style.display = 'none';
    if (startDateInput) startDateInput.value = '';
    if (endDateInput) endDateInput.value = '';
    
    // Clear active filter chips
    if (activeFiltersDisplay) {
      activeFiltersDisplay.innerHTML = '';
    }
    
    // Reset category chips
    setActiveChip('all');
    
    // Search with cleared filters
    searchEvents();
  }
  
  function updateActiveFiltersDisplay() {
    if (!activeFiltersDisplay) return;
    
    const activeFilters = [];
    
    // Check each filter
    if (searchInput.value.trim()) {
      activeFilters.push({ type: 'search', value: searchInput.value.trim() });
    }
    if (categorySelect.value !== 'all') {
      activeFilters.push({ type: 'category', value: categorySelect.value });
    }
    if (dateFilter && dateFilter.value !== 'all') {
      if (dateFilter.value === 'custom') {
        const start = startDateInput ? startDateInput.value : '';
        const end = endDateInput ? endDateInput.value : '';
        activeFilters.push({ type: 'date', value: `${start} to ${end}` });
      } else {
        activeFilters.push({ type: 'date', value: dateFilter.options[dateFilter.selectedIndex].text });
      }
    }
    if (locationFilter && locationFilter.value !== 'all') {
      activeFilters.push({ type: 'location', value: locationFilter.options[locationFilter.selectedIndex].text });
    }
    if (timeFilter && timeFilter.value !== 'all') {
      activeFilters.push({ type: 'time', value: timeFilter.options[timeFilter.selectedIndex].text });
    }
    
    // Display active filters as chips (build via DOM to avoid XSS from searchInput.value)
    activeFiltersDisplay.innerHTML = '';
    if (activeFilters.length > 0) {
      const label = document.createElement('div');
      label.className = 'active-filters-label';
      label.textContent = 'Active filters:';
      activeFiltersDisplay.appendChild(label);
      activeFilters.forEach(filter => {
        const chip = document.createElement('span');
        chip.className = 'active-filter-chip';
        chip.textContent = filter.value;
        activeFiltersDisplay.appendChild(chip);
      });
    }
  }
  
  function filterEventsByAdvancedCriteria(events) {
    return events.filter(event => {
      // Date filtering
      if (!passesDateFilter(event)) return false;
      
      // Location filtering
      if (!passesLocationFilter(event)) return false;
      
      // Time filtering
      if (!passesTimeFilter(event)) return false;
      
      return true;
    });
  }
  
  function passesDateFilter(event) {
    const dateValue = dateFilter ? dateFilter.value : 'all';
    if (dateValue === 'all') return true;
    
    const eventDate = getEventDateTime(event);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    
    switch (dateValue) {
      case 'today':
        return isSameDay(eventDate, today);
      case 'tomorrow':
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);
        return isSameDay(eventDate, tomorrow);
      case 'week':
        const weekEnd = new Date(today);
        weekEnd.setDate(weekEnd.getDate() + 7);
        return eventDate >= today && eventDate <= weekEnd;
      case 'month':
        const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0);
        return eventDate >= today && eventDate <= monthEnd;
      case 'custom':
        if (!startDateInput || !endDateInput) return true;
        const startDate = new Date(startDateInput.value);
        const endDate = new Date(endDateInput.value);
        if (isNaN(startDate) || isNaN(endDate)) return true;
        startDate.setHours(0, 0, 0, 0);
        endDate.setHours(23, 59, 59, 999);
        return eventDate >= startDate && eventDate <= endDate;
      default:
        return true;
    }
  }
  
  function passesLocationFilter(event) {
    const locationValue = locationFilter ? locationFilter.value : 'all';
    if (locationValue === 'all') return true;
    
    const location = (event.location || '').toLowerCase();
    
    switch (locationValue) {
      case 'campus':
        return location.includes('campus') || location.includes('university') || 
               location.includes('hall') || location.includes('building') ||
               location.includes('urbana') || location.includes('champaign');
      case 'downtown':
        return location.includes('downtown') || location.includes('champaign') || 
               location.includes('urbana');
      case 'online':
        return location.includes('online') || location.includes('virtual') || 
               location.includes('zoom') || location.includes('webex');
      case 'union':
        return location.includes('union') || location.includes('student union');
      case 'library':
        return location.includes('library') || location.includes('lib');
      case 'recreation':
        return location.includes('recreation') || location.includes('arc') || 
               location.includes('gym') || location.includes('crce');
      default:
        return true;
    }
  }
  
  function passesTimeFilter(event) {
    const timeValue = timeFilter ? timeFilter.value : 'all';
    if (timeValue === 'all') return true;
    
    const eventDate = getEventDateTime(event);
    const hour = eventDate.getHours();
    
    switch (timeValue) {
      case 'morning':
        return hour >= 6 && hour < 12;
      case 'afternoon':
        return hour >= 12 && hour < 18;
      case 'evening':
        return hour >= 18 && hour < 24;
      case 'night':
        return hour >= 0 && hour < 6;
      default:
        return true;
    }
  }
  
  function isSameDay(date1, date2) {
    return date1.getFullYear() === date2.getFullYear() &&
           date1.getMonth() === date2.getMonth() &&
           date1.getDate() === date2.getDate();
  }

  // ========== STEP 3: Enhanced Display Events ==========
  // Show events as cards on the page with improved pagination
  function displayEvents(events, append = false) {
    // Store the filtered events for pagination
    if (!append) {
      currentlyDisplayedEvents = events;
      displayedCount = 0;
      hasMoreEvents = true;
      totalEventsFound = events.length;
      browseContainer.innerHTML = '';
    }

    // If no events, show a message
    if (events.length === 0) {
      browseContainer.innerHTML = '<p class="no-events-text">No events found</p>';
      return;
    }

    // Calculate how many events to show
    const endIndex = Math.min(displayedCount + EVENTS_PER_PAGE, events.length);
    
    // Show loading spinner for append operations
    if (append && isLoading) {
      const existingSpinner = browseContainer.querySelector('.loading-spinner');
      if (!existingSpinner) {
        browseContainer.appendChild(showLoadingSpinner());
      }
    }

    // Create cards for the next batch of events
    const fragment = document.createDocumentFragment();
    for (let i = displayedCount; i < endIndex; i++) {
      let card = createEventCard(events[i]);
      fragment.appendChild(card);
    }
    
    // Remove loading spinner if exists
    const spinner = browseContainer.querySelector('.loading-spinner');
    if (spinner) {
      spinner.remove();
    }
    
    browseContainer.appendChild(fragment);

    // Update displayed count
    displayedCount = endIndex;

    // Check if there are more events
    hasMoreEvents = displayedCount < events.length;

    // Add or update the "Load More" button
    updateLoadMoreButton();
    
    // Observe the load more trigger
    if (hasMoreEvents) {
      observeLoadMoreTrigger();
    }
  }

  // ========== Enhanced Update Load More Button ==========
  function updateLoadMoreButton() {
    // Remove existing button and observer
    unobserveLoadMoreTrigger();
    const existingButton = document.getElementById('load-more-btn');
    if (existingButton) {
      existingButton.remove();
    }

    // Only show button if there are more events to load
    if (hasMoreEvents) {
      const loadMoreBtn = document.createElement('button');
      loadMoreBtn.id = 'load-more-btn';
      loadMoreBtn.className = 'load-more-btn';
      loadMoreBtn.textContent = `Load More (${currentlyDisplayedEvents.length - displayedCount} remaining)`;
      loadMoreBtn.onclick = loadMoreEvents;
      browseContainer.appendChild(loadMoreBtn);
    } else if (totalEventsFound > EVENTS_PER_PAGE) {
      // Show end of events message
      const endMessage = document.createElement('div');
      endMessage.className = 'end-of-events';
      endMessage.textContent = `Showing all ${totalEventsFound} events`;
      browseContainer.appendChild(endMessage);
    }
  }

  // ========== Enhanced Load More Events ==========
  async function loadMoreEvents() {
    if (isLoading || !hasMoreEvents) return;
    
    isLoading = true;
    
    try {
      displayEvents(currentlyDisplayedEvents, true);
    } catch (error) {
      console.error('Error loading more events:', error);
      showToast('Error', 'Failed to load more events', 'error');
    } finally {
      isLoading = false;
    }
  }

  // ========== STEP 4: Create a Single Event Card (glass style) ==========
  const syncIcon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>';

  function createEventCard(event) {
    let card = document.createElement('div');
    card.className = 'event-card-browse';

    let time = event.start_time;
    if (event.start_time === "12:00 AM" && event.end_time === "11:59 PM") time = "All Day";

    const tag = event.tag || 'General';
    const tagClass = getTagClass(tag); // returns a fixed safe CSS class name
    const dateStr = escapeHtml(event.start_date || 'Date TBA');
    const timeStr = escapeHtml(time || 'Time TBA');
    const locationStr = escapeHtml(event.location || 'Location TBA');
    const title = escapeHtml(event.summary || 'Untitled Event');
    const descriptionPreview = escapeHtml(buildDescriptionPreview(event));

    let html = '<div class="event-card-meta">';
    html += '<span>📅 ' + dateStr + '</span>';
    html += '<span>🕐 ' + timeStr + '</span>';
    html += '</div>';
    html += '<div class="event-card-title">' + title + '</div>';
    html += '<div class="event-card-info"><strong>📍</strong><span>' + locationStr + '</span></div>';
    html += '<p class="event-card-description">' + descriptionPreview + '</p>';
    html += '<div class="event-card-footer">';
    html += '<span class="event-tag ' + tagClass + '">' + escapeHtml(tag) + '</span>';
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
    if (event.start_time === "12:00 AM" && event.end_time === "11:59 PM") {
      document.getElementById('detail-time').textContent = "All Day";
    } else if (event.start_time && event.end_time) {
      document.getElementById('detail-time').textContent = `${event.start_time} - ${event.end_time}`;
    } else if (event.start_time) {
      document.getElementById('detail-time').textContent = event.start_time;
    } else {
      document.getElementById('detail-time').textContent = 'TBA';
    }

    document.getElementById('detail-location').textContent = event.location || 'TBA';
    const detailTag = document.getElementById('detail-tag');
    detailTag.textContent = event.tag || 'General';
    detailTag.className = 'event-tag ' + getTagClass(event.tag);
    document.getElementById('detail-description').textContent =
      normalizeDescription(event.description) || 'No description provided by source.';

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

    if (!event.start) {
      showToast('No Date', 'This event has no date information and cannot be added to your calendar.', 'warning');
      return;
    }

    try {
      const startISO = event.start;
      const endISO = event.end || new Date(new Date(event.start).getTime() + 60 * 60 * 1000).toISOString();

      // Prepare event data for Google Calendar format
      const eventData = {
        summary: event.summary || 'Untitled Event',
        location: event.location || '',
        description: event.description || '',
        start: {
          dateTime: startISO,
          timeZone: 'America/Chicago'
        },
        end: {
          dateTime: endISO,
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

  // ========== Enhanced STEP 7: Search Function ==========
  // Filter events based on search text and advanced criteria
  function searchEvents() {
    let searchText = searchInput.value.trim();
    let selectedCategory = categorySelect.value;
    let filtered = [];

    // Use Fuse.js for fuzzy search if there's search text
    let searchResults = allEvents;
    if (searchText !== '' && fuse) {
      const fuseResults = fuse.search(searchText);
      searchResults = fuseResults.map(result => result.item);
      console.log('Project Helix: Fuzzy search for "' + searchText + '" returned ' + searchResults.length + ' results.');
    }

    // Apply category filter
    for (let i = 0; i < searchResults.length; i++) {
      let event = searchResults[i];

      // Check if event matches selected category
      let matchesCategory = false;
      if (selectedCategory === 'all') {
        matchesCategory = true;
      } else if (event.tag === selectedCategory) {
        matchesCategory = true;
      }

      if (matchesCategory) {
        filtered.push(event);
      }
    }
    
    // Apply advanced filters (date, location, time)
    filtered = filterEventsByAdvancedCriteria(filtered);
    
    // Update active filters display
    updateActiveFiltersDisplay();

    // Display the filtered events
    displayEvents(filtered);
  }

  // ========== STEP 8: Enhanced Event Listeners ==========
  // When user types in search box
  searchInput.addEventListener('input', searchEvents);

  // When user changes category dropdown, sync chips
  categorySelect.addEventListener('change', () => {
    searchEvents();
    setActiveChip(categorySelect.value);
  });

  // When user clicks X to close modal
  closeButton.addEventListener('click', function () {
    detailModal.style.display = 'none';
  });

  // When user clicks outside modal, close it
  detailModal.addEventListener('click', function (event) {
    if (event.target === detailModal) {
      detailModal.style.display = 'none';
    }
  });
  
  // Set up advanced filters
  setupAdvancedFilters();
  
  // Add setActiveChip function for category chips
  function setActiveChip(value) {
    const chips = document.querySelectorAll('.filter-chip');
    chips.forEach(c => {
      c.classList.toggle('active', c.getAttribute('data-category') === value);
    });
  }

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
