(function () {
  "use strict";

  var reduce = window.matchMedia("(prefers-reduced-motion: reduce)");
  var phone = window.matchMedia("(max-width: 860px)");

  if (window.ScrollCraft) window.ScrollCraft.mount(document.body);

  var diary = document.querySelector(".diary");
  var slots = Array.prototype.slice.call(document.querySelectorAll(".diary__slot"));
  var stamped = Array.prototype.slice.call(document.querySelectorAll("[data-diary-service]"));
  var close = document.getElementById("join");
  var filled = Object.create(null);
  var lastService = "";
  var playing = "-";
  var lastState = "";
  var hold = false;

  var videos = Array.prototype.slice.call(document.querySelectorAll(".cut-video")).map(function (el) {
    return { el: el, active: false };
  });

  var videoObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      var v = videos.find(function (item) { return item.el === entry.target; });
      if (!v) return;
      v.active = entry.isIntersecting && entry.intersectionRatio >= 0.3;
      if (v.active && !reduce.matches) {
        var p = v.el.play();
        if (p && p.catch) p.catch(function () {});
      } else {
        v.el.pause();
      }
    });
  }, { threshold: [0, 0.3, 0.6] });

  videos.forEach(function (v) { videoObserver.observe(v.el); });
  phone.addEventListener("change", function () {
    videos.forEach(function (v) { v.el.load(); });
  });
  reduce.addEventListener("change", function () {
    videos.forEach(function (v) { if (reduce.matches) v.el.pause(); });
  });

  slots.forEach(function (slot) {
    slot.addEventListener("click", function () {
      var target = document.getElementById(slot.dataset.target);
      if (!target) return;
      target.scrollIntoView({ behavior: reduce.matches ? "instant" : "smooth", block: "start" });
    });
  });

  function publish() {
    if (!diary) return;
    var count = Object.keys(filled).length;
    var state = count + "/" + slots.length + "|" + (lastService || "empty") + "|" + playing;
    if (state !== lastState) {
      diary.setAttribute("data-sc-verify-state", state);
      lastState = state;
    }
    var shouldHold = count === slots.length &&
      (reduce.matches || (close && close.getBoundingClientRect().top < innerHeight * 0.6));
    if (shouldHold !== hold) {
      if (shouldHold) diary.setAttribute("data-sc-verify-hold", "true");
      else diary.removeAttribute("data-sc-verify-hold");
      hold = shouldHold;
    }
  }

  function update() {
    stamped.forEach(function (section) {
      if (section.getBoundingClientRect().top > innerHeight * 0.5) return;
      var service = section.dataset.diaryService;
      if (filled[service]) return;
      filled[service] = true;
      lastService = service;
      var slot = slots.find(function (s) { return s.dataset.service === service; });
      if (slot) {
        slot.classList.add("is-filled");
        slot.tabIndex = 0;
        slot.setAttribute("aria-label", service + ", jump to section");
      }
    });
    var visible = videos.filter(function (v) { return v.active; });
    playing = visible.length ? visible[0].el.dataset.scVerifyCut : "-";
    publish();
  }

  var queued = false;
  function onScroll() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () {
      queued = false;
      update();
    });
  }

  addEventListener("scroll", onScroll, { passive: true });
  addEventListener("resize", onScroll);

  var form = document.querySelector("[data-callback-form]");
  if (form) {
    form.addEventListener("submit", function (event) {
      event.preventDefault();
      if (!form.reportValidity()) return;
      var lines = [];
      Array.prototype.forEach.call(form.elements, function (el) {
        if (!el.name || el.disabled || el.type === "submit") return;
        if (el.type === "checkbox") {
          if (el.checked) lines.push(el.name + ": " + (el.value || "Yes"));
        } else if (el.value) {
          lines.push(el.name + ": " + el.value);
        }
      });
      var subject = "Request a call back - Beauty Booked Up";
      window.location.href = "mailto:hello@webawesome.co.uk?subject=" +
        encodeURIComponent(subject) + "&body=" + encodeURIComponent(lines.join("\n"));
    });
  }

  update();
})();
