// ** EVENT EXPORT FUNCTIONALITY ** //
// Export events to iCal (.ics) and CSV formats

/**
 * Export filtered events to iCal format
 * @param {Array} events - Array of event objects to export
 */
function exportToICal(events) {
  if (!events || events.length === 0) {
    _exportShowToast('No Events', 'No events available to export', 'warning');
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
  _exportShowToast('Export Complete', `Exported ${events.length} event${events.length !== 1 ? 's' : ''} to iCal format`, 'success');
}

/**
 * Create iCal event entry
 * @param {Object} event - Event object
 * @returns {string} iCal formatted event
 */
function createICalEvent(event) {
  const dtstart = formatICalDate(event.start);
  const dtstamp = formatICalDate(new Date().toISOString());

  // Skip events with no valid start date
  if (!dtstart || !dtstamp) return '';

  const dtend = formatICalDate(event.end) || dtstart;
  const uid = `${event.id || generateUID()}@projecthelix.uiuc`;

  const lines = [
    'BEGIN:VEVENT',
    `UID:${uid}`,
    `DTSTAMP:${dtstamp}`,
    `DTSTART:${dtstart}`,
    `DTEND:${dtend}`,
    `SUMMARY:${escapeICalText(event.summary || 'Untitled Event')}`,
  ];

  const description = escapeICalText(event.description || '');
  const location = escapeICalText(event.location || '');
  const url = (event.htmlLink || '').replace(/[\r\n]/g, ''); // no CRLF → no iCal property injection
  if (description) lines.push(`DESCRIPTION:${description}`);
  if (location) lines.push(`LOCATION:${location}`);
  if (url) lines.push(`URL:${url}`);
  if (event.tag) lines.push(`CATEGORIES:${escapeICalText(event.tag)}`);
  lines.push('STATUS:CONFIRMED', 'SEQUENCE:0', 'END:VEVENT', '');

  return lines.map(foldICalLine).join('\r\n');
}

/**
 * Format ISO date string to iCal format
 * @param {string} isoDate - ISO 8601 date string
 * @returns {string} iCal formatted date
 */
function formatICalDate(isoDate) {
  if (!isoDate) return null;

  const date = new Date(isoDate);
  if (isNaN(date.getTime())) return null;

  const year = date.getUTCFullYear();
  const month = String(date.getUTCMonth() + 1).padStart(2, '0');
  const day = String(date.getUTCDate()).padStart(2, '0');
  const hours = String(date.getUTCHours()).padStart(2, '0');
  const minutes = String(date.getUTCMinutes()).padStart(2, '0');
  const seconds = String(date.getUTCSeconds()).padStart(2, '0');

  return `${year}${month}${day}T${hours}${minutes}${seconds}Z`;
}

// Fold iCal property lines at 75 octets per RFC 5545
function foldICalLine(line) {
  const bytes = new TextEncoder().encode(line);
  if (bytes.length <= 75) return line;
  const parts = [];
  let start = 0;
  while (start < bytes.length) {
    const end = start === 0 ? 75 : start + 74;
    parts.push(new TextDecoder().decode(bytes.slice(start, end)));
    start = end;
  }
  return parts.join('\r\n ');
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
function exportToCSV(events) {
  if (!events || events.length === 0) {
    _exportShowToast('No Events', 'No events available to export', 'warning');
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

  // Combine headers and rows — RFC 4180 requires CRLF
  const csvContent = [
    headers.join(','),
    ...rows.map(row => row.join(','))
  ].join('\r\n');

  // Create and download the file
  downloadFile(csvContent, 'uiuc-events.csv', 'text/csv');
  _exportShowToast('Export Complete', `Exported ${events.length} event${events.length !== 1 ? 's' : ''} to CSV format`, 'success');
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

  // Neutralize spreadsheet formula injection (=, +, -, @ leaders execute in Excel)
  if (/^[=+\-@]/.test(text)) {
    text = "'" + text;
  }

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

// Use the global showToast defined in script.js; fall back to console if not yet loaded
function _exportShowToast(title, message, type, duration) {
  if (window.showToast) {
    window.showToast(title, message, type, duration);
  } else {
    console.log(`Toast: ${title} - ${message}`);
  }
}

// Also make functions available globally for other scripts
window.exportToICal = exportToICal;
window.exportToCSV = exportToCSV;
