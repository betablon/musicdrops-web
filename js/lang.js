// MusicDrops — site interactions
// Language toggle, mobile nav, scroll reveal, header state, feature cursor glow
(function () {
  var STORAGE_KEY = "musicdrops-lang";

  // ---------- Language ----------
  function setLang(lang) {
    document.body.classList.toggle("lang-de", lang === "de");
    document.querySelectorAll(".lang-toggle button").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.lang === lang);
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
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
    // Close on nav link click (mobile)
    nav.querySelectorAll("a").forEach(function (a) {
      a.addEventListener("click", function () {
        if (nav.classList.contains("open")) {
          nav.classList.remove("open");
          toggle.setAttribute("aria-expanded", "false");
        }
      });
    });
  }

  // ---------- Header scrolled state ----------
  var header = document.querySelector(".site-header");
  if (header) {
    var updateHeader = function () {
      header.classList.toggle("is-scrolled", window.scrollY > 10);
    };
    updateHeader();
    window.addEventListener("scroll", updateHeader, { passive: true });
  }

  // ---------- Scroll reveal ----------
  var prefersReduced = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var revealables = document.querySelectorAll(".reveal");

  if (prefersReduced || !("IntersectionObserver" in window)) {
    revealables.forEach(function (el) { el.classList.add("is-visible"); });
  } else {
    // Stagger siblings within the same parent for a subtle cascade
    var parentIndex = new WeakMap();
    revealables.forEach(function (el) {
      var p = el.parentElement;
      var i = parentIndex.get(p) || 0;
      parentIndex.set(p, i + 1);
      // Only cascade feature-grid cards and multi-sibling revealers
      if (p && (p.classList.contains("features-grid") || p.classList.contains("showcase"))) {
        el.style.setProperty("--reveal-delay", (i * 60) + "ms");
      }
    });

    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add("is-visible");
          io.unobserve(entry.target);
        }
      });
    }, { rootMargin: "0px 0px -8% 0px", threshold: 0.08 });
    revealables.forEach(function (el) { io.observe(el); });
  }

  // ---------- Feature card cursor glow ----------
  if (!prefersReduced) {
    document.querySelectorAll(".feat").forEach(function (card) {
      card.addEventListener("pointermove", function (e) {
        var r = card.getBoundingClientRect();
        card.style.setProperty("--mx", (e.clientX - r.left) + "px");
        card.style.setProperty("--my", (e.clientY - r.top) + "px");
      });
    });
  }

  // ---------- Year in footer (if any) ----------
  var y = new Date().getFullYear();
  document.querySelectorAll("[data-year]").forEach(function (el) { el.textContent = y; });
})();
