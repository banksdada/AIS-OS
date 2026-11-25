import { chromium } from "playwright-core";

const BASE = "http://localhost:4500";
const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});
const errors = [];
const failed = [];
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("requestfailed", (r) => failed.push(r.failure()?.errorText + " " + r.url()));

  await page.goto(BASE + "/index.html", { waitUntil: "domcontentloaded" });
  await page.waitForSelector("html.sc-ready", { timeout: 15000 });
  await page.evaluate(() => document.fonts.ready);
  await page.locator("#plans").scrollIntoViewIfNeeded();
  await page.locator(".plans").screenshot({ path: "lab/plans-check.png" });
  const images = await page.evaluate(() => [...document.images].map((i) => ({
    src: i.getAttribute("src"), ok: i.complete && i.naturalWidth > 0,
  })));
  const broken = images.filter((i) => !i.ok);

  const pages = {};
  for (const name of ["privacy.html", "terms.html", "cookies.html", "blog.html", "legal.html"]) {
    const r = await page.goto(BASE + "/" + name, { waitUntil: "domcontentloaded" });
    pages[name] = { status: r.status(), h1: await page.locator("h1").first().textContent() };
  }

  console.log(JSON.stringify({
    brokenImages: broken,
    pages,
    consoleErrors: errors,
    failedRequests: failed,
    profileImage: images.find((i) => (i.src || "").includes("sharon-profile")),
  }, null, 2));
  process.exit(broken.length || errors.length || failed.length ? 1 : 0);
} finally {
  await browser.close();
}
