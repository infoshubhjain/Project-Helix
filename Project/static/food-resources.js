// Food Resource List — renders Project/food_resources.json, the curated table
// that scrape.py emits from Project/food_resources.py. The panel is a directory,
// not an event feed: it includes appointment-only pantries and reference links
// that deliberately produce no dated events.
(function () {
  "use strict";

  var escapeHtml = (window.EventUtils && window.EventUtils.escapeHtml) || function (s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  };

  // Escaping keeps a URL inside its attribute but does not stop a javascript:
  // scheme from running, so links are whitelisted to http(s) before rendering.
  function safeUrl(url) {
    return /^https?:\/\//i.test(String(url || "")) ? String(url) : "";
  }

  var openBtn = document.getElementById("food-resources-btn");
  var modal = document.getElementById("food-modal");
  var closeBtn = document.getElementById("close-food-modal");
  var listEl = document.getElementById("food-list");
  var searchEl = document.getElementById("food-search");
  var scopeEl = document.getElementById("food-scope");
  var addAllBtn = document.getElementById("food-add-all-btn");
  var addAllNote = document.getElementById("food-add-all-note");
  if (!openBtn || !modal || !listEl) return;

  var resources = null; // fetched once, on first open

  function card(r) {
    // A phone number is optional; only render the row when there is one.
    var phone = r.phone
      ? '<div class="food-card-phone"><a href="tel:' + escapeHtml(r.phone.replace(/[^0-9+]/g, "")) +
        '">' + escapeHtml(r.phone) + "</a></div>"
      : "";
    // Who can walk in matters as much as when: being turned away after a
    // 40-minute walk is the failure this panel exists to prevent.
    var eligibility = r.eligibility
      ? '<div class="food-card-who">👤 ' + escapeHtml(r.eligibility) + "</div>"
      : "";
    var distance = r.walk_min != null
      ? '<span class="food-dist-chip' + (r.walk_min > 30 ? " food-dist-far" : "") + '">' +
        escapeHtml(r.distance_mi + " mi · " + r.walk_min + " min walk") + "</span>"
      : "";
    return (
      '<article class="food-card">' +
      '<div class="food-card-head">' +
      '<h4>' + escapeHtml(r.name) + "</h4>" +
      '<span class="food-scope-chip">' + escapeHtml(r.scope) + "</span>" +
      "</div>" +
      '<div class="food-card-when">🕒 ' + escapeHtml(r.recurrence) + "</div>" +
      '<div class="food-card-where">📍 ' + escapeHtml(r.location) + " " + distance + "</div>" +
      eligibility +
      "<p>" + escapeHtml(r.description) + "</p>" +
      phone +
      (safeUrl(r.link)
        ? '<a class="food-card-link" href="' + escapeHtml(safeUrl(r.link)) +
          '" target="_blank" rel="noopener noreferrer">More info →</a>'
        : "") +
      "</article>"
    );
  }

  // The resources passing the current search + scope filters. Shared by the
  // list and by "add all", so the button can never add something off-screen.
  function visible() {
    if (!resources) return [];
    var q = (searchEl && searchEl.value || "").trim().toLowerCase();
    var scope = (scopeEl && scopeEl.value) || "all";
    return resources.filter(function (r) {
      if (scope !== "all" && r.scope !== scope) return false;
      if (!q) return true;
      return (r.name + " " + r.location + " " + r.description + " " + r.recurrence +
              " " + (r.eligibility || ""))
        .toLowerCase().indexOf(q) !== -1;
    }).sort(function (a, b) {
      // Nearest first — the practical question is "where can I walk to now".
      // Entries with no fixed location (online, county-wide) sort last.
      var da = a.walk_min == null ? Infinity : a.walk_min;
      var db = b.walk_min == null ? Infinity : b.walk_min;
      return da - db;
    });
  }

  function render() {
    if (!resources) return;
    var shown = visible();
    syncAddAllButton();
    listEl.innerHTML = shown.length
      ? '<div class="food-count">' + shown.length + " resource" + (shown.length === 1 ? "" : "s") +
        "</div>" + shown.map(card).join("")
      : '<p class="food-empty">No resources match that search.</p>';
  }

  function load() {
    if (resources) { render(); return; }
    fetch("Project/food_resources.json", { cache: "no-store" })
      .then(function (r) {
        if (!r.ok) throw new Error("HTTP " + r.status);
        return r.json();
      })
      .then(function (data) {
        resources = Array.isArray(data) ? data : [];
        render();
      })
      .catch(function (err) {
        // Fail loudly in the panel: a silent empty list would read as "no food
        // resources exist", which is the opposite of the truth.
        console.error("Food resources failed to load:", err);
        listEl.innerHTML =
          '<p class="food-empty">Could not load the resource list. ' +
          'See <a href="https://scs.illinois.edu/free-food-resources-campus-and-community" ' +
          'target="_blank" rel="noopener noreferrer">the campus list</a> instead.</p>';
      });
  }

  // ---- Add all to Google Calendar ----------------------------------------
  // Each resource contributes recurring RRULE events (one per recurrence rule)
  // rather than one row per occurrence, so "add all" is ~37 API calls and the
  // user's calendar stays readable.

  function toast(title, msg, kind) {
    if (window.showToast) window.showToast(title, msg, kind || "info");
    else console.log(title + ": " + msg);
  }

  function calendarPayload(resource, entry) {
    var detail = resource.recurrence + "\n" + resource.description;
    if (resource.phone) detail += "\nPhone: " + resource.phone;
    if (safeUrl(resource.link)) detail += "\n" + safeUrl(resource.link);
    return {
      summary: "🍕 " + resource.name,
      location: resource.location,
      description: detail + "\n\nHours change — confirm before you go. Added from Project Helix.",
      start: { dateTime: entry.start, timeZone: "America/Chicago" },
      end: { dateTime: entry.end, timeZone: "America/Chicago" },
      recurrence: [entry.rrule],
      reminders: { useDefault: false, overrides: [] }
    };
  }

  // Resources currently passing the filters, paired with their calendar entries.
  function addableFromView() {
    var jobs = [];
    visible().forEach(function (r) {
      (r.calendar || []).forEach(function (entry) {
        jobs.push({ resource: r, entry: entry });
      });
    });
    return jobs;
  }

  function syncAddAllButton() {
    if (!addAllBtn) return;
    var jobs = addableFromView();
    addAllBtn.disabled = jobs.length === 0;
    addAllBtn.textContent = "+ Add all to Google Calendar";
    if (addAllNote) {
      // Directory-only entries have no dependable time, so they are never added.
      var skipped = visible().length - visible().filter(function (r) {
        return (r.calendar || []).length;
      }).length;
      addAllNote.textContent = jobs.length
        ? jobs.length + " recurring event" + (jobs.length === 1 ? "" : "s") +
          (skipped ? " · " + skipped + " listing-only, not added" : "")
        : "Nothing here can be added to a calendar.";
    }
  }

  async function addAll() {
    if (!window.calendarAPI || !window.calendarAPI.isConnected()) {
      toast("Not Connected", "Connect your Google Calendar first, then try again.", "warning");
      return;
    }
    var jobs = addableFromView();
    if (!jobs.length) return;

    // Writing dozens of recurring events to someone's real calendar is not
    // easily undone, so it is always confirmed — and the count is the filtered
    // count, which is what the user can actually see on screen.
    var msg = "Add " + jobs.length + " recurring events to your Google Calendar?\n\n" +
      "These are the " + visible().length + " resources currently shown. " +
      "Each becomes one repeating event you can delete later.";
    if (!window.confirm(msg)) return;

    addAllBtn.disabled = true;
    var ok = 0, failed = 0;
    for (var i = 0; i < jobs.length; i++) {
      addAllBtn.textContent = "Adding " + (i + 1) + " of " + jobs.length + "…";
      try {
        await window.calendarAPI.addEvent(calendarPayload(jobs[i].resource, jobs[i].entry));
        ok++;
      } catch (err) {
        failed++;
        console.error("Failed to add", jobs[i].resource.name, err);
      }
    }
    syncAddAllButton();
    if (window.calendarAPI.refresh) window.calendarAPI.refresh();

    if (failed && !ok) {
      toast("Nothing Added", "All " + failed + " events failed. Check your connection and try again.", "error");
    } else if (failed) {
      toast("Partly Added", ok + " added, " + failed + " failed. Re-run to retry the rest.", "warning");
    } else {
      toast("Added to Calendar", ok + " recurring food resources are now on your calendar.", "success");
    }
  }

  function open() { modal.style.display = "flex"; load(); }
  function close() { modal.style.display = "none"; }

  openBtn.addEventListener("click", open);
  if (closeBtn) closeBtn.addEventListener("click", close);
  if (addAllBtn) addAllBtn.addEventListener("click", addAll);
  if (searchEl) searchEl.addEventListener("input", render);
  if (scopeEl) scopeEl.addEventListener("change", render);
  modal.addEventListener("click", function (e) { if (e.target === modal) close(); });
  document.addEventListener("keydown", function (e) {
    if (e.key === "Escape" && modal.style.display === "flex") close();
  });
})();
