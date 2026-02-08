document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("event-modal");
  const detailModal = document.getElementById("detail-modal");

  // Set up Add Event button
  const addEventBtn = document.getElementById("add-event");
  if (addEventBtn) {
    addEventBtn.addEventListener("click", () => {
      modal.style.display = "flex";
    });
  }

  // Close modal buttons
  const closeModalBtn = document.getElementById("close-modal");
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      modal.style.display = "none";
      clearEventForm();
    });
  }

  const closeAddEventBtn = document.getElementById("close-add-event");
  if (closeAddEventBtn) {
    closeAddEventBtn.addEventListener("click", () => {
      modal.style.display = "none";
      clearEventForm();
    });
  }

  // Close detail modal
  const closeDetailBtn = document.getElementById("close-detail");
  if (closeDetailBtn) {
    closeDetailBtn.addEventListener("click", () => {
      detailModal.style.display = "none";
    });
  }

  // Close modals when clicking outside
  window.addEventListener("click", (e) => {
    if (e.target === modal) {
      modal.style.display = "none";
      clearEventForm();
    }
    if (e.target === detailModal) {
      detailModal.style.display = "none";
    }
  });

  // Save Event button
  const saveEventBtn = document.getElementById("save-event");
  if (saveEventBtn) {
    saveEventBtn.addEventListener("click", async () => {
      await handleSaveEvent();
    });
  }

  // Set minimum datetime to now
  const eventDateInput = document.getElementById("event-date");
  if (eventDateInput) {
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    eventDateInput.min = now.toISOString().slice(0, 16);
  }
});

async function handleSaveEvent() {
  const title = document.getElementById("event-title").value.trim();
  const datetime = document.getElementById("event-date").value;
  const location = document.getElementById("event-location").value.trim();
  const description = document.getElementById("event-description")?.value.trim() || "";

  // Validation
  if (!title) {
    showToast("Missing Title", "Please enter an event title", "warning");
    return;
  }

  if (!datetime) {
    showToast("Missing Date", "Please select a date and time", "warning");
    return;
  }

  const startDate = new Date(datetime);
  const endDate = new Date(startDate.getTime() + 60 * 60 * 1000); // +1 hour default

  // Check if connected to Google Calendar
  if (window.calendarAPI && window.calendarAPI.isConnected()) {
    try {
      // Add event directly to Google Calendar
      const event = {
        'summary': title,
        'location': location,
        'description': description,
        'start': {
          'dateTime': startDate.toISOString(),
          'timeZone': Intl.DateTimeFormat().resolvedOptions().timeZone
        },
        'end': {
          'dateTime': endDate.toISOString(),
          'timeZone': Intl.DateTimeFormat().resolvedOptions().timeZone
        }
      };

      await window.calendarAPI.addEvent(event);

      showToast("Event Added", "Event successfully added to your Google Calendar", "success");

      // Refresh the events display
      if (typeof loadUserEvents === 'function') {
        await loadUserEvents();
      }

      // Close modal and clear form
      document.getElementById("event-modal").style.display = "none";
      clearEventForm();

    } catch (error) {
      console.error("Error adding event:", error);
      showToast("Error", "Failed to add event. Please try again.", "error");
    }
  } else {
    // Not connected - open Google Calendar with pre-filled data
    const googleCalendarUrl = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(title)}&dates=${formatGoogleDate(startDate)}/${formatGoogleDate(endDate)}&location=${encodeURIComponent(location)}&details=${encodeURIComponent(description)}`;

    window.open(googleCalendarUrl, '_blank');

    showToast("Opening Google Calendar", "Please connect your calendar for automatic syncing!", "info", 4000);

    document.getElementById("event-modal").style.display = "none";
    clearEventForm();
  }
}

function clearEventForm() {
  document.getElementById("event-title").value = "";
  document.getElementById("event-date").value = "";
  document.getElementById("event-location").value = "";
  const descField = document.getElementById("event-description");
  if (descField) {
    descField.value = "";
  }
}

// Helper function to format date for Google Calendar URL
function formatGoogleDate(date) {
  return date.toISOString().replace(/-|:|\.\d+/g, '');
}

// Update current date display
function updateCurrentDate() {
  const dateElement = document.getElementById('current-date');
  if (dateElement) {
    const options = { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' };
    dateElement.textContent = new Date().toLocaleDateString('en-US', options);
  }
}

// Initialize current date
updateCurrentDate();

// Update date every minute
setInterval(updateCurrentDate, 60000);

// ========== DARK MODE TOGGLE ==========
// Initialize dark mode from localStorage
function initDarkMode() {
  const darkMode = localStorage.getItem('darkMode');

  // Only apply dark mode if user has explicitly enabled it
  // Default to light mode for all users
  if (darkMode === 'enabled') {
    document.body.classList.add('dark-mode');
    updateDarkModeButton(true);
  }
}

// Toggle dark mode
function toggleDarkMode() {
  const isDark = document.body.classList.toggle('dark-mode');
  localStorage.setItem('darkMode', isDark ? 'enabled' : 'disabled');
  updateDarkModeButton(isDark);

  // Show toast notification
  showToast(
    isDark ? 'Dark Mode On' : 'Light Mode On',
    `Switched to ${isDark ? 'dark' : 'light'} mode`,
    'info',
    2000
  );
}

// Update theme toggle appearance (single navbar toggle)
function updateDarkModeButton(isDark) {
  const btn = document.getElementById('theme-toggle');
  if (btn) {
    btn.setAttribute('aria-label', isDark ? 'Switch to light mode' : 'Switch to dark mode');
    btn.title = isDark ? 'Switch to light mode' : 'Switch to dark mode';
  }
}

// Set up theme toggle (navbar)
document.addEventListener('DOMContentLoaded', () => {
  initDarkMode();
  const themeToggle = document.getElementById('theme-toggle');
  if (themeToggle) {
    themeToggle.addEventListener('click', toggleDarkMode);
  }
});

// Make showToast available globally
window.showToast = showToast;

// ========== ENHANCED TOAST NOTIFICATION SYSTEM ==========
function showToast(title, message, type = 'info', duration = 4000) {
  const container = document.getElementById('toast-container');

  // Create toast element
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;

  // Icon based on type
  const icons = {
    success: '✅',
    error: '❌',
    warning: '⚠️',
    info: 'ℹ️'
  };

  toast.innerHTML = `
    <span class="toast-icon">${icons[type] || icons.info}</span>
    <div class="toast-content">
      <div class="toast-title">${title}</div>
      ${message ? `<div class="toast-message">${message}</div>` : ''}
    </div>
    <button class="toast-close">×</button>
  `;

  // Add to container
  container.appendChild(toast);

  // Close button handler
  const closeBtn = toast.querySelector('.toast-close');
  closeBtn.addEventListener('click', () => {
    removeToast(toast);
  });

  // Auto remove after duration
  if (duration > 0) {
    setTimeout(() => {
      removeToast(toast);
    }, duration);
  }
}

function removeToast(toast) {
  toast.classList.add('fade-out');
  setTimeout(() => {
    toast.remove();
  }, 300);
}

// Notification helper
function showNotification(message, type = 'info') {
  console.log(`[${type.toUpperCase()}] ${message}`);

  // Create toast notification
  const container = document.getElementById('toast-container');
  if (!container) return;

  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;

  container.appendChild(toast);

  // Show toast
  setTimeout(() => toast.classList.add('show'), 10);

  // Auto-hide after 4 seconds
  setTimeout(() => {
    toast.classList.remove('show');
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}
