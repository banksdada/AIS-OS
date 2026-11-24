import { chromium } from "playwright-core";

const URL = process.env.SITE_URL || "http://localhost:4500";
const CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome";
const results = [];

function check(name, ok, detail) {
  results.push({ name, ok, detail });
  if (!ok) console.error(`FAIL ${name}: ${detail}`);
}

const browser = await chromium.launch({ executablePath: CHROME, headless: true });
try {
  const ctx = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const page = await ctx.newPage();
  await page.goto(URL, { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(600);

  const initial = await page.evaluate(() => ({
    state: document.querySelector(".diary").getAttribute("data-sc-verify-state"),
    hold: document.querySelector(".diary").hasAttribute("data-sc-verify-hold"),
    tabIndexes: [...document.querySelectorAll(".diary__slot")].map((s) => s.tabIndex),
  }));
  check("R1 no early stamps", /^0\/6\|empty\|/.test(initial.state), initial.state);
  check("R5 no hold at top", !initial.hold, "hold present at top");
  check("R2 empty slots not focusable", initial.tabIndexes.every((t) => t === -1), JSON.stringify(initial.tabIndexes));

  await page.evaluate(() => document.getElementById("bookings").scrollIntoView({ behavior: "instant" }));
  await page.waitForTimeout(500);
  const mid = await page.evaluate(() => document.querySelector(".diary").getAttribute("data-sc-verify-state"));
  const midCount = parseInt(mid.split("/")[0], 10);
  check("R1 stamps on passing half viewport", midCount >= 2, mid);

  await page.evaluate(() => scrollTo({ top: document.body.scrollHeight, behavior: "instant" }));
  await page.waitForTimeout(700);
  const end = await page.evaluate(() => ({
    state: document.querySelector(".diary").getAttribute("data-sc-verify-state"),
    hold: document.querySelector(".diary").hasAttribute("data-sc-verify-hold"),
    slots: [...document.querySelectorAll(".diary__slot")].map((s) => ({
      tab: s.tabIndex, label: s.getAttribute("aria-label"), filled: s.classList.contains("is-filled"),
    })),
    form: {
      action: document.querySelector("[data-callback-form]").getAttribute("action"),
      required: ["cb-name", "cb-business", "cb-phone"].every((id) => document.getElementById(id).required),
      consent: document.querySelector("input[name='Consent']").required,
    },
  }));
  check("R1 all six stamp at close", /^6\/6\|/.test(end.state), end.state);
  check("R3 state published", /6\/6\|AI tools\|/.test(end.state), end.state);
  check("R5 hold at close", end.hold, "hold missing at close");
  check("R2 filled slots focusable and labelled", end.slots.every((s) => s.tab === 0 && s.label && s.filled), JSON.stringify(end.slots));
  check("R7 form has safe action and required fields", end.form.action.startsWith("mailto:") && end.form.required && end.form.consent, JSON.stringify(end.form));

  await page.click('.diary__slot[data-service="Website"]');
  await page.waitForTimeout(1400);
  const jumped = await page.evaluate(() => {
    const top = document.getElementById("website").getBoundingClientRect().top;
    return Math.abs(top) < 140;
  });
  check("R4 slot click jumps to section", jumped, "did not land near #website");

  await ctx.close();

  const reduced = await browser.newContext({ viewport: { width: 1440, height: 900 }, reducedMotion: "reduce" });
  const rp = await reduced.newPage();
  await rp.goto(URL, { waitUntil: "domcontentloaded" });
  await rp.evaluate(() => document.getElementById("bookings").scrollIntoView({ behavior: "instant" }));
  await rp.waitForTimeout(600);
  const paused = await rp.evaluate(() => [...document.querySelectorAll(".cut-video")].every((v) => v.paused));
  check("R6 reduced motion pauses video", paused, "a video played under reduced motion");
  await reduced.close();

  const normal = await browser.newContext({ viewport: { width: 1440, height: 900 } });
  const np = await normal.newPage();
  await np.goto(URL, { waitUntil: "domcontentloaded" });
  await np.evaluate(() => document.getElementById("bookings").scrollIntoView({ behavior: "instant" }));
  await np.waitForTimeout(900);
  const playing = await np.evaluate(() => [...document.querySelectorAll(".cut-video")].some((v) => !v.paused));
  check("R6 visible video plays", playing, "no video played while visible");
  await normal.close();
} finally {
  await browser.close();
}

const failed = results.filter((r) => !r.ok);
console.log(JSON.stringify({ total: results.length, passed: results.length - failed.length, failed: failed.map((f) => f.name) }));
process.exit(failed.length ? 1 : 0);
