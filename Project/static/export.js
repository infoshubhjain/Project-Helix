// ** EVENT EXPORT FUNCTIONALITY ** //
// Export events to iCal (.ics) and CSV formats

/**
 * Export filtered events to iCal format
 * @param {Array} events - Array of event objects to export
 */
export function exportToICal(events) {
  if (!events || events.length === 0) {
    showToast('No Events', 'No events available to export', 'warning');
    return;
  }

  // Create iCal file content
  let icalContent = [
    'BEGIN:VCALENDAR',
    'VERSION:2.0',
    'PRODID:-//Project Helix//UIUC Events//EN',
    'CALSCALE:GREGORIAN',
    'METHOD:PUBLISH',
    'X-WR-CALNAME:UIUC Events Export',
    'X-WR-TIMEZONE:America/Chicago',
    ''
  ].join('\r\n');

  // Add each event
  events.forEach(event => {
    icalContent += createICalEvent(event);
  });

  // Close the calendar
  icalContent += 'END:VCALENDAR\r\n';

  // Create and download the file
  downloadFile(icalContent, 'uiuc-events.ics', 'text/calendar');
  showToast('Export Complete', `Exported ${events.length} event${events.length !== 1 ? 's' : ''} to iCal format`, 'success');
}

/**
 * Create iCal event entry
 * @param {Object} event - Event object
 * @returns {string} iCal formatted event
 */
function createICalEvent(event) {
  // Generate unique ID
  const uid = `${event.id || generateUID()}@projecthelix.uiuc`;

  // Format dates to iCal format (YYYYMMDDTHHmmssZ)
  const dtstart = formatICalDate(event.start);
  const dtend = formatICalDate(event.end);
  const dtstamp = formatICalDate(new Date().toISOString());

  // Escape special characters in text fields
  const summary = escapeICalText(event.summary || 'Untitled Event');
  const description = escapeICalText(event.description || '');
  const location = escapeICalText(event.location || '');
  const url = event.htmlLink || '';

  return [
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART:${dtstart}`,
    `DTEND:${dtend}`,
    `SUMMARY:${summary}`,
    description ? `DESCRIPTION:${description}` : '',
    location ? `LOCATION:${location}` : '',
    url ? `URL:${url}` : '',
    event.tag ? `CATEGORIES:${event.tag}` : '',
    'STATUS:CONFIRMED',
    'SEQUENCE:0',
    'END:VEVENT',
    ''
  ].filter(line => line !== '').join('\r\n');
}

/**
 * Format ISO date string to iCal format
 * @param {string} isoDate - ISO 8601 date string
 * @returns {string} iCal formatted date
 */
function formatICalDate(isoDate) {
  if (!isoDate) return '';

  const date = new Date(isoDate);
  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  const seconds = String(date.getUTCSeconds()).padStart(2, '0');

  return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

/**
 * Escape special characters for iCal format
 * @param {string} text - Text to escape
 * @returns {string} Escaped text
 */
function escapeICalText(text) {
  if (!text) return '';
  return text
    .replace(/\\/g, '\\\\')
    .replace(/;/g, '\\;')
    .replace(/,/g, '\\,')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '');
}

/**
 * Generate a unique ID
 * @returns {string} Unique identifier
 */
function generateUID() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2);
}

/**
 * Export filtered events to CSV format
 * @param {Array} events - Array of event objects to export
 */
export function exportToCSV(events) {
  if (!events || events.length === 0) {
    showToast('No Events', 'No events available to export', 'warning');
    return;
  }

  // CSV headers
  const headers = [
    'Title',
    'Start Date',
    'Start Time',
    'End Date',
    'End Time',
    'Location',
    'Category',
    'Description',
    'Event Link'
  ];

  // Create CSV rows
  const rows = events.map(event => {
    return [
      escapeCSV(event.summary || ''),
      escapeCSV(event.start_date || ''),
      escapeCSV(event.start_time || ''),
      escapeCSV(event.end_date || event.start_date || ''),
      escapeCSV(event.end_time || ''),
      escapeCSV(event.location || ''),
      escapeCSV(event.tag || ''),
      escapeCSV(event.description || ''),
      escapeCSV(event.htmlLink || '')
    ];
  });

  // Combine headers and rows
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\n');

  // Create and download the file
  downloadFile(csvContent, 'uiuc-events.csv', 'text/csv');
  showToast('Export Complete', `Exported ${events.length} event${events.length !== 1 ? 's' : ''} to CSV format`, 'success');
}

/**
 * Escape special characters for CSV format
 * @param {string} text - Text to escape
 * @returns {string} Escaped and quoted text
 */
function escapeCSV(text) {
  if (!text) return '""';

  // Convert to string if not already
  text = String(text);

  // If text contains comma, quote, or newline, wrap in quotes and escape quotes
  if (text.includes(',') || text.includes('"') || text.includes('\n')) {
    text = '"' + text.replace(/"/g, '""') + '"';
  } else {
    text = '"' + text + '"';
  }

  return text;
}

/**
 * Download a file with the given content
 * @param {string} content - File content
 * @param {string} filename - Name of the file
 * @param {string} mimeType - MIME type of the file
 */
function downloadFile(content, filename, mimeType) {
  const blob = new Blob([content], { type: mimeType });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}

// Make showToast available (will be defined in script.js)
function showToast(title, message, type, duration) {
  if (window.showToast) {
    window.showToast(title, message, type, duration);
  } else {
    console.log(`Toast: ${title} - ${message}`);
  }
}
