import { chromium } from "playwright";
import { mkdirSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const outDir = join(root, "docs", "demo", "raw");
mkdirSync(outDir, { recursive: true });

const FILM_MS = 97_000;

const browser = await chromium.launch({
  headless: true,
  args: ["--autoplay-policy=no-user-gesture-required"],
});
const context = await browser.newContext({
  viewport: { width: 1920, height: 1080 },
  deviceScaleFactor: 1,
  recordVideo: { dir: outDir, size: { width: 1920, height: 1080 } },
});
const page = await context.newPage();
await page.goto("http://127.0.0.1:8000/?film=1", { waitUntil: "networkidle", timeout: 60_000 });
await page.waitForTimeout(FILM_MS);
await context.close();
await browser.close();
console.log("Recorded to", outDir);
