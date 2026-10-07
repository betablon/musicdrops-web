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
