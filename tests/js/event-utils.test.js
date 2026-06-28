// Frontend unit tests — run with: node --test tests/js
const { test } = require('node:test');
const assert = require('node:assert');
const U = require('../../Project/static/event-utils.js');

test('escapeHtml escapes all five significant characters', () => {
  assert.strictEqual(U.escapeHtml(`<a href="x" onclick='y'>&`), '&lt;a href=&quot;x&quot; onclick=&#39;y&#39;&gt;&amp;');
});

test('escapeHtml handles null/undefined', () => {
  assert.strictEqual(U.escapeHtml(null), '');
  assert.strictEqual(U.escapeHtml(undefined), '');
});

test('getEventCategories splits compound tags', () => {
  assert.deepStrictEqual(U.getEventCategories('Academic, Free Food 🍕'), ['Academic', 'Free Food']);
});

test('getEventCategories maps Free Performances to Performances', () => {
  assert.deepStrictEqual(U.getEventCategories('Free Performances'), ['Performances']);
});

test('getEventCategories falls back to General', () => {
  assert.deepStrictEqual(U.getEventCategories(''), ['General']);
  assert.deepStrictEqual(U.getEventCategories('Whatever'), ['General']);
});

test('getEventCategories dedupes repeated canonical categories', () => {
  assert.deepStrictEqual(U.getEventCategories('Arts, Art Show'), ['Arts']);
});

test('getTagClass returns canonical CSS classes', () => {
  assert.strictEqual(U.getTagClass('Athletics'), 'tag-athletics');
  assert.strictEqual(U.getTagClass('Academic'), 'tag-academic');
  // Free Food takes colour priority so the orange highlight always shows
  assert.strictEqual(U.getTagClass('Academic, Free Food 🍕'), 'tag-freefood');
  assert.strictEqual(U.getTagClass('Free Food 🍕'), 'tag-freefood');
  assert.strictEqual(U.getTagClass('Performances'), 'tag-performances');
  assert.strictEqual(U.getTagClass('Community'), 'tag-community');
  assert.strictEqual(U.getTagClass('Entertainment'), 'tag-entertainment');
  assert.strictEqual(U.getTagClass(''), 'tag-general');
});

test('formatDate renders Month Day, Year', () => {
  // Construct in local time to avoid TZ ambiguity
  assert.strictEqual(U.formatDate(new Date(2026, 6, 5)), 'July 5, 2026');
});

test('formatTime renders 12-hour clock with AM/PM', () => {
  assert.strictEqual(U.formatTime(new Date(2026, 6, 5, 17, 30)), '5:30 PM');
  assert.strictEqual(U.formatTime(new Date(2026, 6, 5, 0, 5)), '12:05 AM');
  assert.strictEqual(U.formatTime(new Date(2026, 6, 5, 12, 0)), '12:00 PM');
});
