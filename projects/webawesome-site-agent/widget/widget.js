(function () {
  "use strict";
  if (window.__waaLoaded) return;
  window.__waaLoaded = true;

  var cfg = window.WebAwesomeAgentConfig || {};
  var API = (cfg.apiBase || "https://agent.webawesome.co.uk").replace(/\/+$/, "");

  var css = "" +
    ".waa-bubble{position:fixed;right:20px;bottom:20px;z-index:2147483000;border:0;border-radius:24px;padding:14px 20px;font:600 15px/1 system-ui,sans-serif;background:#111;color:#fff;cursor:pointer;box-shadow:0 8px 24px rgba(0,0,0,.25)}" +
    ".waa-panel{position:fixed;right:20px;bottom:76px;width:min(380px,calc(100vw - 32px));height:min(560px,calc(100vh - 120px));z-index:2147483000;display:none;flex-direction:column;background:#fff;color:#111;border-radius:16px;box-shadow:0 16px 48px rgba(0,0,0,.3);overflow:hidden;font:14px/1.45 system-ui,sans-serif}" +
    ".waa-panel.open{display:flex}" +
    ".waa-head{display:flex;justify-content:space-between;align-items:center;padding:12px 14px;background:#111;color:#fff;font-weight:600}" +
    ".waa-head button{background:none;border:0;color:#fff;font-size:18px;cursor:pointer}" +
    ".waa-log{flex:1;overflow:auto;padding:12px;display:flex;flex-direction:column;gap:8px}" +
    ".waa-msg{max-width:85%;padding:8px 11px;border-radius:12px;white-space:pre-wrap}" +
    ".waa-bot{background:#f2f2f2;align-self:flex-start}" +
    ".waa-user{background:#111;color:#fff;align-self:flex-end}" +
    ".waa-actions{display:flex;gap:8px;flex-wrap:wrap}" +
    ".waa-chip{border:1px solid #ccc;background:#fff;border-radius:14px;padding:6px 10px;font:inherit;cursor:pointer}" +
    ".waa-form{display:flex;gap:6px;padding:10px;border-top:1px solid #eee}" +
    ".waa-form input{flex:1;border:1px solid #ccc;border-radius:10px;padding:8px 10px;font:inherit}" +
    ".waa-form button{border:0;border-radius:10px;padding:8px 12px;background:#111;color:#fff;font:inherit;cursor:pointer}" +
    ".waa-slot{display:block;width:100%;text-align:left;border:1px solid #ccc;background:#fff;border-radius:10px;padding:7px 10px;margin:2px 0;font:inherit;cursor:pointer}" +
    ".waa-small{font-size:12px;color:#666}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  function el(tag, cls, text) {
    var node = document.createElement(tag);
    if (cls) node.className = cls;
    if (text != null) node.textContent = text;
    return node;
  }

  var bubble = el("button", "waa-bubble", cfg.label || "Ask");
  var panel = el("div", "waa-panel");
  var head = el("div", "waa-head");
  head.appendChild(el("span", null, cfg.title || "Webby · WebAwesome"));
  var close = el("button", null, "\u00d7");
  close.setAttribute("aria-label", "Close");
  head.appendChild(close);
  var log = el("div", "waa-log");
  var form = el("form", "waa-form");
  var input = el("input", null);
  input.placeholder = cfg.placeholder || "Ask about services or book a call";
  input.setAttribute("aria-label", "Message");
  var send = el("button", null, "Send");
  send.type = "submit";
  form.appendChild(input);
  form.appendChild(send);
  panel.appendChild(head);
  panel.appendChild(log);
  panel.appendChild(form);
  document.body.appendChild(bubble);
  document.body.appendChild(panel);

  function add(role, text) {
    var node = el("div", "waa-msg " + (role === "user" ? "waa-user" : "waa-bot"), text);
    log.appendChild(node);
    log.scrollTop = log.scrollHeight;
    return node;
  }

  function post(path, body) {
    return fetch(API + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body)
    }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (data) {
        return { ok: r.ok, status: r.status, data: data };
      });
    });
  }

  function renderSlots(slots) {
    if (!slots || !slots.length) return;
    var wrap = el("div");
    wrap.appendChild(el("div", "waa-small", "Next free discovery slots (UK time):"));
    slots.forEach(function (slot) {
      var b = el("button", "waa-slot", slot.label);
      b.type = "button";
      b.addEventListener("click", function () { askBooking(slot); });
      wrap.appendChild(b);
    });
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
  }

  function askBooking(slot) {
    var wrap = el("div");
    wrap.appendChild(el("div", "waa-small", "Book " + slot.label + ". Name and email:"));
    var name = el("input"); name.placeholder = "Name";
    var email = el("input"); email.placeholder = "Email"; email.type = "email";
    var go = el("button", "waa-slot", "Confirm booking");
    go.type = "button";
    [name, email].forEach(function (i) {
      i.style.cssText = "display:block;width:100%;margin:4px 0;padding:7px 9px;border:1px solid #ccc;border-radius:9px;font:inherit";
      wrap.appendChild(i);
    });
    wrap.appendChild(go);
    log.appendChild(wrap);
    log.scrollTop = log.scrollHeight;
    go.addEventListener("click", function () {
      if (!name.value.trim() || email.value.indexOf("@") < 0) {
        add("bot", "Please add your name and a valid email.");
        return;
      }
      go.disabled = true;
      post("/book", { name: name.value.trim(), email: email.value.trim(), starts_at: slot.starts_at })
        .then(function (res) {
          if (res.ok) {
            add("bot", "Booked: " + (res.data.label || slot.label) + ". A confirmation email is on its way.");
            wrap.remove();
          } else if (res.status === 409) {
            add("bot", "That slot was just taken. Here are the next ones.");
            renderSlots((res.data.detail && res.data.detail.slots) || []);
          } else {
            add("bot", "Sorry, booking failed. Please try another slot or ask for a human.");
            go.disabled = false;
          }
        })
        .catch(function () {
          add("bot", "Network error. Please try again.");
          go.disabled = false;
        });
    });
  }

  function renderActions() {
    var wrap = el("div", "waa-actions");
    var book = el("button", "waa-chip", "Book a call");
    book.type = "button";
    var human = el("button", "waa-chip", "Talk to a human");
    human.type = "button";
    wrap.appendChild(book);
    wrap.appendChild(human);
    log.appendChild(wrap);

    book.addEventListener("click", function () {
      fetch(API + "/slots?limit=3")
        .then(function (r) { return r.json(); })
        .then(function (d) { renderSlots(d.slots || []); })
        .catch(function () { add("bot", "Could not load slots right now."); });
    });

    human.addEventListener("click", function () {
      var wrap2 = el("div");
      var name = el("input"); name.placeholder = "Name";
      var email = el("input"); email.placeholder = "Email"; email.type = "email";
      var q = el("input"); q.placeholder = "Your question";
      var go = el("button", "waa-slot", "Send to Banks");
      go.type = "button";
      [name, email, q].forEach(function (i) {
        i.style.cssText = "display:block;width:100%;margin:4px 0;padding:7px 9px;border:1px solid #ccc;border-radius:9px;font:inherit";
        wrap2.appendChild(i);
      });
      wrap2.appendChild(go);
      log.appendChild(wrap2);
      log.scrollTop = log.scrollHeight;
      go.addEventListener("click", function () {
        post("/lead", { name: name.value.trim(), email: email.value.trim(), question: q.value.trim() })
          .then(function (res) {
            if (res.ok) {
              add("bot", "Thanks, Banks will reply by email within one working day.");
              wrap2.remove();
            } else {
              add("bot", "Please add your name, a valid email and a question.");
            }
          })
          .catch(function () { add("bot", "Network error. Please try again."); });
      });
    });
  }

  function sendMessage(text) {
    add("user", text);
    post("/chat", { message: text })
      .then(function (res) {
        if (!res.ok) {
          add("bot", "Sorry, something went wrong. Try again or ask for a human.");
          return;
        }
        add("bot", res.data.reply || "Sorry, I could not answer that.");
        renderSlots(res.data.slots || []);
      })
      .catch(function () { add("bot", "Network error. Please try again."); });
  }

  bubble.addEventListener("click", function () {
    var open = panel.classList.toggle("open");
    if (open) {
      if (!log.childElementCount) {
        add("bot", cfg.greeting || "Hi, I'm Webby. Ask me about our services and AI audits, or I can show you the next free discovery slots.");
        renderActions();
      }
      input.focus();
    }
  });
  close.addEventListener("click", function () { panel.classList.remove("open"); });
  form.addEventListener("submit", function (e) {
    e.preventDefault();
    var text = input.value.trim();
    if (!text) return;
    input.value = "";
    sendMessage(text);
  });
})();
