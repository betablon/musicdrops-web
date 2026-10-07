// MusicDrops: the language switch animation.
// EN/DE are links between /x/ and /de/x/. Where the browser can do cross-document
// view transitions, the other language spreads from the button like a drop hitting
// water (css: html.lang-drop, .lang-ripple). Any other navigation stays plain.
// Loaded in <head> so it is listening before the new page first renders.
(function () {
  function isSwitch(a, b) { return a === "/de" + b || b === "/de" + a; }
  function path(url) { try { return new URL(url).pathname; } catch (e) { return ""; } }

  // Leaving: only a language switch gets a transition.
  addEventListener("pageswap", function (e) {
    if (!e.viewTransition) return;
    var to = e.activation && e.activation.entry && e.activation.entry.url;
    // Without the Navigation API (Safari) there is no target here; the new page decides.
    if (to && !isSwitch(location.pathname, path(to))) e.viewTransition.skipTransition();
  });

  // Arriving: start the ripple where EN/DE sits (the header is the same on both pages).
  addEventListener("pagereveal", function (e) {
    var vt = e.viewTransition;
    if (!vt) return;
    var from = (window.navigation && navigation.activation && navigation.activation.from &&
      navigation.activation.from.url) || document.referrer;
    if (!from || !isSwitch(path(from), location.pathname)) { vt.skipTransition(); return; }

    var el = document.querySelector(".lang-toggle a.active");
    var r = el && el.getBoundingClientRect();
    if (!r || !r.width) { // phones: EN/DE is inside the closed menu, so use the menu button
      el = document.querySelector(".nav-toggle");
      r = el && el.getBoundingClientRect();
    }
    var x = r && r.width ? r.left + r.width / 2 : innerWidth - 40;
    var y = r && r.width ? r.top + r.height / 2 : 30;
    var reach = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y));

    var root = document.documentElement;
    root.style.setProperty("--drop-x", x + "px");
    root.style.setProperty("--drop-y", y + "px");
    root.style.setProperty("--drop-r", Math.ceil(reach) + "px");
    root.classList.add("lang-drop");
    var ripple = document.createElement("div");
    ripple.className = "lang-ripple";
    ripple.setAttribute("aria-hidden", "true");
    (document.body || root).appendChild(ripple);
    var done = function () {
      root.classList.remove("lang-drop");
      ripple.remove();
    };
    vt.finished.then(done, done);
  });
})();
