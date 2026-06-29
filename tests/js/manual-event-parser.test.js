// Tests for the manual event parser — run with: node --test tests/js/*.test.js
const { test } = require('node:test');
const assert = require('node:assert');

// The parser attaches itself to window; provide a stub so we can require it in Node.
global.window = {};
require('../../Project/static/manual-event-parser.js');
const ManualEventParser = global.window.ManualEventParser;

const parser = new ManualEventParser();
const OPT = { autoDetectLocation: true };

function parseOne(text) {
  const events = parser.parseEvents(text, OPT);
  return events[0] || null;
}

test('time range keeps the start time (shared meridiem)', () => {
  const e = parseOne('Hackathon Friday 7-9pm in Siebel Center');
  assert.ok(e);
  assert.strictEqual(new Date(e.start).getHours(), 19);
  assert.strictEqual(new Date(e.end).getHours(), 21);
});

test('time range with spaces and explicit pm', () => {
  const e = parseOne('Club meeting Saturday 2-3 pm at the Union');
  assert.strictEqual(new Date(e.start).getHours(), 14);
  assert.strictEqual(new Date(e.end).getHours(), 15);
});

test('"march" does NOT match the "arc" location key', () => {
  const e = parseOne('Networking event March 5th at 6pm');
  assert.strictEqual(e.location, '');
});

test('"satisfaction" does NOT match Saturday', () => {
  const e = parseOne('Seminar on satisfaction surveys March 20 at 1pm');
  // March 20 2026 is a Friday; if "sat" wrongly matched it would land on a Saturday
  assert.strictEqual(new Date(e.start).getDay(), 5);
});

test('generic "in <phrase>" is not treated as a location without a venue keyword', () => {
  const e = parseOne('Workshop in Python programming March 10 at 4pm');
  assert.strictEqual(e.location, '');
  assert.match(e.title, /Python programming/);
});

test('room number keeps its "Room" prefix', () => {
  const e = parseOne('Office hours March 16th 10-11 AM in Room 123');
  assert.strictEqual(e.location, 'Room 123');
});

test('known UIUC venue + room number combine', () => {
  const e = parseOne('Meeting with Professor Smith on Tuesday, March 15th at 2:30 PM in Room 243 of the Engineering Building');
  assert.strictEqual(e.location, 'Engineering Hall, Room 243');
  assert.strictEqual(new Date(e.start).getHours(), 14);
  assert.strictEqual(new Date(e.start).getMinutes(), 30);
});

test('title is cleaned of date, time, weekday and venue text', () => {
  assert.strictEqual(parseOne('Talk at Siebel Center March 12 3pm').title, 'Talk');
  assert.strictEqual(parseOne('Hackathon Friday 7-9pm in Siebel Center').title, 'Hackathon');
});

test('abbreviations like "Dr." do not split one event into many', () => {
  const events = parser.parseEvents('Study session with Dr. Smith March 4th at 5pm', OPT);
  assert.strictEqual(events.length, 1);
});

test('newline-separated lines produce multiple events', () => {
  const text = 'Study group Monday March 14th at 5pm in Grainger Library\nParty Friday March 18th at 8 PM at the Union';
  const events = parser.parseEvents(text, OPT);
  assert.strictEqual(events.length, 2);
});

test('single time gets a default one-hour duration', () => {
  const e = parseOne('Lecture March 10 at 4pm');
  assert.strictEqual(new Date(e.start).getHours(), 16);
  assert.strictEqual(new Date(e.end).getHours(), 17);
});

test('noon and midnight convert correctly', () => {
  assert.strictEqual(new Date(parseOne('Lunch March 10 at 12pm').start).getHours(), 12);
  assert.strictEqual(new Date(parseOne('Vigil March 10 at 12am').start).getHours(), 0);
});
