// Language toggle (EN/DE)
(function () {
  var STORAGE_KEY = "musicdrops-lang";

  function setLang(lang) {
    document.body.classList.toggle("lang-de", lang === "de");
    document.querySelectorAll(".lang-toggle button").forEach(function (btn) {
      btn.classList.toggle("active", btn.dataset.lang === lang);
    });
    try {
      localStorage.setItem(STORAGE_KEY, lang);
    } catch (e) {
      // localStorage unavailable — no-op
    }
    document.documentElement.lang = lang;
  }

  function getSavedLang() {
    try {
      return localStorage.getItem(STORAGE_KEY);
    } catch (e) {
      return null;
    }
  }

  // Determine initial language: saved preference > browser language > English
  var saved = getSavedLang();
  var initial = saved || (navigator.language && navigator.language.startsWith("de") ? "de" : "en");
  setLang(initial);

  // Bind toggle buttons
  document.querySelectorAll(".lang-toggle button").forEach(function (btn) {
    btn.addEventListener("click", function () {
      setLang(btn.dataset.lang);
    });
  });

  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.querySelector(".nav-links");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      nav.classList.toggle("open");
    });
  }
})();
