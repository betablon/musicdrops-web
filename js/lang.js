// MusicDrops — site interactions
// Language toggle, mobile nav, header state
(function () {
  var STORAGE_KEY = "musicdrops-lang";

  // ---------- Language ----------
  function setLang(lang) {
    document.body.classList.toggle("lang-de", lang === "de");
    document.querySelectorAll(".lang-toggle button").forEach(function (btn) {
      var on = btn.dataset.lang === lang;
      btn.classList.toggle("active", on);
      btn.setAttribute("aria-pressed", on ? "true" : "false");
    });
    try { localStorage.setItem(STORAGE_KEY, lang); } catch (e) { /* no-op */ }
    document.documentElement.lang = lang;
  }
  function getSavedLang() {
    try { return localStorage.getItem(STORAGE_KEY); } catch (e) { return null; }
  }

  var saved = getSavedLang();
  var initial = saved || (navigator.language && navigator.language.toLowerCase().startsWith("de") ? "de" : "en");
  setLang(initial);

  document.querySelectorAll(".lang-toggle button").forEach(function (btn) {
    btn.addEventListener("click", function () { setLang(btn.dataset.lang); });
  });

  // ---------- Mobile nav ----------
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav-links");
  if (toggle && nav) {
    var setOpen = function (open) {
      nav.classList.toggle("open", open);
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    };
    toggle.addEventListener("click", function () { setOpen(!nav.classList.contains("open")); });
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () { setOpen(false); });
    });
    document.addEventListener("keydown", function (e) {
      if (e.key === "Escape" && nav.classList.contains("open")) { setOpen(false); toggle.focus(); }
    });
  }

  // ---------- Notification mockups: wording relative to today ----------
  // scripts/update_notifications.py writes real releases with their date;
  // this turns that date into "now", "yesterday" or "Coming tomorrow".
  var today = new Date();
  today.setHours(0, 0, 0, 0);
  document.querySelectorAll(".notif[data-date]").forEach(function (n) {
    var p = n.dataset.date.split("-");
    var days = Math.round((new Date(+p[0], p[1] - 1, +p[2]) - today) / 864e5);
    var set = function (sel, en, de) {
      var el = n.querySelector(sel);
      if (!el) return;
      el.querySelector('[lang="en"]').textContent = en;
      el.querySelector('[lang="de"]').textContent = de;
    };
    if (n.dataset.notif === "just" || days <= 0) {
      var ago = Math.max(0, -days);
      set(".notif__title", "Just dropped", "Gerade erschienen");
      // A weekday reads as "this week"; past six days, name the date instead.
      var weekday = function (lang) {
        return new Date(+p[0], p[1] - 1, +p[2]).toLocaleDateString(lang,
          ago > 6 ? { month: "short", day: "numeric" } : { weekday: "short" });
      };
      set(".notif__time",
        ago === 0 ? "now" : ago === 1 ? "yesterday" : weekday("en"),
        ago === 0 ? "jetzt" : ago === 1 ? "gestern" : weekday("de"));
    } else if (days === 1) {
      set(".notif__title", "Coming tomorrow", "Erscheint morgen");
    }
  });

  // ---------- Header hairline once scrolled ----------
  var header = document.querySelector(".site-header");
  if (header) {
    var updateHeader = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 4);
    };
    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
  }
})();
