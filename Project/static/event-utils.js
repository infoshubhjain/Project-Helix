// Pure, framework-free helpers shared by the browser and the Node test suite.
// UMD wrapper: attaches to window.HelixUtils in the browser, exports in Node.
(function (root, factory) {
  if (typeof module === 'object' && module.exports) {
    module.exports = factory();
  } else {
    root.HelixUtils = factory();
  }
})(typeof self !== 'undefined' ? self : this, function () {
  'use strict';

  // Canonical, filterable categories (order = display order of filter chips).
  var CANONICAL_CATEGORIES = [
    'Academic', 'Performances', 'Arts', 'Athletics',
    'Community', 'Entertainment', 'Free Food', 'General'
  ];

  // Escape the five HTML-significant characters. Pure (no DOM) so it is safe
  // for attribute interpolation and testable outside a browser.
  function escapeHtml(value) {
    return String(value == null ? '' : value)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  // Map one raw tag segment to its canonical category.
  function _canonical(segment) {
    var t = String(segment || '').toLowerCase();
    if (t.indexOf('free food') !== -1) return 'Free Food';
    if (t.indexOf('athletic') !== -1 || t.indexOf('sport') !== -1) return 'Athletics';
    if (t.indexOf('academic') !== -1) return 'Academic';
    if (t.indexOf('perform') !== -1) return 'Performances';
    if (t.indexOf('art') !== -1) return 'Arts';
    if (t.indexOf('communit') !== -1) return 'Community';
    if (t.indexOf('entertain') !== -1) return 'Entertainment';
    return 'General';
  }

  // A tag string may be compound, e.g. "Academic, Free Food 🍕".
  // Returns the de-duplicated list of canonical categories it belongs to.
  function getEventCategories(tag) {
    if (!tag) return ['General'];
    var out = [];
    String(tag).split(',').forEach(function (seg) {
      var c = _canonical(seg);
      if (out.indexOf(c) === -1) out.push(c);
    });
    return out.length ? out : ['General'];
  }

  // CSS class for the primary (first) category of a tag.
  function getTagClass(tag) {
    if (!tag) return 'tag-general';
    var t = String(tag).toLowerCase();
    if (t.indexOf('free food') !== -1) return 'tag-freefood';
    if (t.indexOf('athletic') !== -1 || t.indexOf('sport') !== -1) return 'tag-athletics';
    if (t.indexOf('academic') !== -1) return 'tag-academic';
    if (t.indexOf('perform') !== -1) return 'tag-performances';
    if (t.indexOf('art') !== -1) return 'tag-arts';
    if (t.indexOf('communit') !== -1) return 'tag-community';
    if (t.indexOf('entertain') !== -1) return 'tag-entertainment';
    return 'tag-general';
  }

  var MONTH_NAMES = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
  ];

  // "Month Day, Year" (e.g. "July 5, 2026").
  function formatDate(date) {
    return MONTH_NAMES[date.getMonth()] + ' ' + date.getDate() + ', ' + date.getFullYear();
  }

  // "H:MM AM/PM" (e.g. "5:30 PM").
  function formatTime(date) {
    var hours = date.getHours();
    var minutes = String(date.getMinutes()).padStart(2, '0');
    var ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12 || 12;
    return hours + ':' + minutes + ' ' + ampm;
  }

  return {
    CANONICAL_CATEGORIES: CANONICAL_CATEGORIES,
    escapeHtml: escapeHtml,
    getEventCategories: getEventCategories,
    getTagClass: getTagClass,
    formatDate: formatDate,
    formatTime: formatTime
  };
});
