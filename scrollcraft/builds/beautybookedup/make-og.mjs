import { chromium } from "playwright-core";
import path from "node:path";
import { pathToFileURL } from "node:url";

const root = path.resolve(".");
const browser = await chromium.launch({
  executablePath: "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
  headless: true,
});
try {
  const page = await browser.newPage({ viewport: { width: 1300, height: 2000 }, deviceScaleFactor: 1 });
  await page.goto(pathToFileURL(path.join(root, "og-card.html")).href, { waitUntil: "domcontentloaded" });
  await page.evaluate(() => document.fonts.ready);
  await page.locator("#card-wide").screenshot({ path: "assets/og-image.png" });
  await page.locator("#card-square").screenshot({ path: "assets/og-image-square.png" });
  await page.setViewportSize({ width: 180, height: 180 });
  console.log("wrote assets/og-image.png and assets/og-image-square.png");
} finally {
  await browser.close();
}
