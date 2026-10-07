// MusicDrops — site interactions
// Language and theme toggles, mobile nav, header state
(function () {
  var STORAGE_KEY = "musicdrops-lang";

  // ---------- Theme: the system's, unless the visitor picked the other one ----------
  // A choice is kept (in localStorage, like the language) only while it differs
  // from the system; switching back to match the system forgets it. The inline
  // script in each page's <head> applies a kept choice before the first paint.
  var THEME_KEY = "musicdrops-theme";
  var root = document.documentElement;
  var systemDark = window.matchMedia ? window.matchMedia("(prefers-color-scheme: dark)") : null;
  var themeMetas = document.querySelectorAll('meta[name="theme-color"]');
  var themeMetaDefaults = Array.prototype.map.call(themeMetas, function (m) { return m.content; });
  function systemTheme() { return systemDark && systemDark.matches ? "dark" : "light"; }
  function currentTheme() { return root.dataset.theme || systemTheme(); }
  function updateThemeUI() {
    var dark = currentTheme() === "dark";
    var de = document.body.classList.contains("lang-de");
    document.querySelectorAll(".theme-toggle").forEach(function (btn) {
      btn.classList.toggle("is-dark", dark);
      btn.setAttribute("aria-label", dark
        ? (de ? "Zum hellen Modus wechseln" : "Switch to light mode")
        : (de ? "Zum dunklen Modus wechseln" : "Switch to dark mode"));
      btn.title = btn.getAttribute("aria-label");
    });
    // The browser chrome follows the page, not the system, once a theme is picked.
    themeMetas.forEach(function (m, i) {
      m.content = root.dataset.theme ? (dark ? "#0f0e0d" : "#fbfaf6") : themeMetaDefaults[i];
    });
  }
  function setTheme(theme) {
    if (theme === systemTheme()) {
      delete root.dataset.theme;
      try { localStorage.removeItem(THEME_KEY); } catch (e) { /* no-op */ }
    } else {
      root.dataset.theme = theme;
      try { localStorage.setItem(THEME_KEY, theme); } catch (e) { /* no-op */ }
    }
    updateThemeUI();
  }
  document.querySelectorAll(".theme-toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var next = currentTheme() === "dark" ? "light" : "dark";
      // Crossfade the whole page where the browser can; otherwise switch at once.
      var calm = window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      if (!document.startViewTransition || calm) { setTheme(next); return; }
      // If the browser can't animate (a hidden tab, say), it skips the fade
      // but still runs the switch; don't report that as an error.
      var fade = document.startViewTransition(function () { setTheme(next); });
      fade.ready.catch(function () {});
      fade.finished.catch(function () {});
    });
  });
  if (systemDark) {
    var onSystemChange = function () {
      // A kept choice that now matches the system is no longer a choice.
      if (root.dataset.theme === systemTheme()) setTheme(systemTheme()); else updateThemeUI();
    };
    if (systemDark.addEventListener) systemDark.addEventListener("change", onSystemChange);
    else if (systemDark.addListener) systemDark.addListener(onSystemChange);
  }

  // ---------- Language: English at /, German at /de/ ----------
  // Every page is in one language and EN/DE link between the two. A pick is
  // remembered, so the inline script in <head> can send later visits to it.
  // 404.html answers for every missing address, so it reads its language
  // from the path and switches its own text.
  if (document.querySelector(".not-found") && /^\/de\//.test(location.pathname)) {
    document.body.classList.add("lang-de");
    root.lang = "de";
    document.querySelectorAll(".lang-toggle a").forEach(function (a) {
      var on = a.dataset.lang === "de";
      a.classList.toggle("active", on);
      if (on) a.setAttribute("aria-current", "true"); else a.removeAttribute("aria-current");
    });
  }
  document.querySelectorAll(".lang-toggle a").forEach(function (a) {
    a.addEventListener("click", function () {
      try { localStorage.setItem(STORAGE_KEY, a.dataset.lang); } catch (e) { /* no-op */ }
    });
  });
  updateThemeUI();

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
      // German pages carry only the German text, English ones both.
      var enEl = el.querySelector('[lang="en"]'), deEl = el.querySelector('[lang="de"]');
      if (enEl) enEl.textContent = en;
      if (deEl) deEl.textContent = de;
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

  // ---------- Prices in the visitor's currency ----------
  // The App Store's live prices (checked 2026-10-07), by storefront currency.
  // Anywhere else sees dollars; the copy around them says the App Store shows yours.
  var PRICES = {
    USD: { monthly: 1.99, yearly: 12.99, lifetime: 39.99 },
    EUR: { monthly: 1.99, yearly: 14.99, lifetime: 44.99 },
    GBP: { monthly: 1.99, yearly: 12.99, lifetime: 39.99 },
    CAD: { monthly: 2.99, yearly: 17.99, lifetime: 49.99 },
    AUD: { monthly: 2.99, yearly: 19.99, lifetime: 59.99 },
    CHF: { monthly: 2, yearly: 10, lifetime: 35 }
  };
  var EUROZONE = /^(AT|BE|CY|DE|EE|ES|FI|FR|GR|HR|IE|IT|LT|LU|LV|MT|NL|PT|SI|SK)$/;
  var REGION_CURRENCY = { GB: "GBP", CA: "CAD", AU: "AUD", CH: "CHF", LI: "CHF" };
  // The visitor's country, from the first browser language that names one,
  // else from a bare language that mostly means one country.
  var BARE_LANGUAGE = { de: "DE", fr: "FR", it: "IT", es: "ES", nl: "NL", fi: "FI", el: "GR", ja: "JP" };
  var region = (function () {
    var langs = navigator.languages && navigator.languages.length ? navigator.languages : [navigator.language || "en"];
    for (var i = 0; i < langs.length; i++) {
      var r = langs[i].split("-")[1];
      if (r && /^[a-z]{2}$/i.test(r)) return r.toUpperCase();
    }
    return BARE_LANGUAGE[langs[0].split("-")[0].toLowerCase()] || null;
  })();
  var currency = !region ? "USD" : EUROZONE.test(region) ? "EUR" : REGION_CURRENCY[region] || "USD";
  document.querySelectorAll("[data-price]").forEach(function (el) {
    var amount = PRICES[currency][el.dataset.price];
    var holder = el.closest("[lang]");
    if (amount == null || !holder) return;
    try {
      el.textContent = new Intl.NumberFormat(holder.lang, { style: "currency", currency: currency }).format(amount);
    } catch (e) { /* keep the price written in the page */ }
  });

  // ---------- App Store links: the visitor's own storefront ----------
  // apps.apple.com sends country-less links to the US store, so name the country.
  if (region) {
    document.querySelectorAll('a[href^="https://apps.apple.com/us/app/"]').forEach(function (a) {
      a.href = a.href.replace("/us/app/", "/" + region.toLowerCase() + "/app/");
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
