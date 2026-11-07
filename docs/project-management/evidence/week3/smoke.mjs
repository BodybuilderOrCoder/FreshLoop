// End-to-end smoke test: real browser, real FastAPI, real PostgreSQL (test DB).
import { chromium } from "playwright-core";
import { execFileSync } from "node:child_process";
import { mkdirSync, writeFileSync } from "node:fs";

const [run = "1", outDir = "."] = process.argv.slice(2);
const WEB = "http://localhost:3000";
const API = "http://localhost:8000";
const PASSWORD = "Smoke-test-pass-1";
const stamp = Date.now();
let phoneCounter = 0;
const uniquePhone = () => `09${String(stamp + (phoneCounter += 1)).slice(-8)}`;
mkdirSync(outDir, { recursive: true });

const results = [];
const check = (id, ok, note = "") => {
  results.push({ id, ok: Boolean(ok), note: String(note) });
  console.log(`${ok ? "PASS" : "FAIL"} ${id} ${note}`);
};
const step = async (id, fn) => {
  try {
    await fn();
  } catch (error) {
    check(id, false, `exception: ${String(error.message).split("\n")[0]}`);
  }
};

const sql = (query) =>
  execFileSync("docker", ["exec", "freshloop-postgres", "psql", "-U", "freshloop_user",
    "-d", "freshloop_test_db", "-Atc", query], { encoding: "utf8" }).trim();

const json = async (path, options = {}) => {
  const response = await fetch(`${API}${path}`, options);
  return { status: response.status, body: await response.json().catch(() => null) };
};
const money = (text) => Number(text.replace(/[^\d]/g, ""));

const signUp = async (email) => {
  await json("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password: PASSWORD, name: "Smoke Staff", phone: uniquePhone() }),
  });
};
const signIn = async (email) => (await json("/api/auth/login", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ email, password: PASSWORD }),
})).body.access_token;

const staffEmail = `smoke.staff.${stamp}@example.com`;
await signUp(staffEmail);
sql(`UPDATE users SET role='STAFF' WHERE email='${staffEmail}'`);
const staffToken = await signIn(staffEmail);

const warehouses = (await json("/api/warehouses")).body;
const hub = warehouses.find((item) => item.code === "HUB-01") ?? warehouses[0];
const other = warehouses.find((item) => item.warehouse_id !== hub.warehouse_id);
const stockOf = async (productId, warehouseId = hub.warehouse_id) => {
  for (let skip = 0; ; skip += 100) {
    const page = (await json(`/api/warehouses/${warehouseId}/products?skip=${skip}&limit=100`)).body;
    const found = page.find((item) => item.product_id === productId);
    if (found || page.length < 100) return found;
  }
};
const patchStock = (productId, delta) => json(
  `/api/warehouses/${hub.warehouse_id}/products/${productId}/stock`,
  {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${staffToken}`,
      "Idempotency-Key": `smoke-${stamp}-${Math.random()}`,
    },
    body: JSON.stringify({ quantity_delta: delta }),
  },
);

const browser = await chromium.launch({ channel: "msedge", headless: true });
const context = await browser.newContext({ viewport: { width: 1366, height: 860 } });
const page = await context.newPage();
const consoleErrors = [];
page.on("pageerror", (error) => consoleErrors.push(String(error)));

const addFirstProduct = async () => {
  const card = page.locator(".product-card").filter({ has: page.getByRole("button", { name: /add/i }) })
    .filter({ hasNot: page.locator(".qty-control") }).nth(2);
  await card.scrollIntoViewIfNeeded();
  const name = (await card.locator("h3").innerText()).trim();
  const href = await card.locator("h3 a").getAttribute("href");
  await card.locator(".product-bottom button").first().click();
  return { name, productId: href.split("/").pop() };
};
const openCheckout = async () => {
  await page.locator(".cart-button").click();
  await page.getByRole("button", { name: /Continue to checkout/ }).click();
};

// --- Catalog, cart, sign-in gate ---------------------------------------------
await page.goto(WEB);
await page.waitForSelector(".product-card", { timeout: 20000 });
check("CAT-1 catalog loads from API", await page.locator(".product-card").count() > 0);
check("QR-1 signed-out Quick Reorder prompt",
  (await page.locator(".reorder-note").innerText()).includes("Sign in"));
check("LIVE-1 live indicator", await page.getByText("Live stock updates on").isVisible()
  .catch(() => false) || await page.waitForSelector("text=Live stock updates on", { timeout: 8000 }).then(() => true));
check("FEE-1 no delivery fee copy", !(await page.locator("body").innerText()).toLowerCase().includes("free delivery"));

const first = await addFirstProduct();
await openCheckout();
check("AUTH-1 checkout asks for sign-in when signed out",
  await page.getByRole("link", { name: "Sign in to continue" }).isVisible());
await page.screenshot({ path: `${outDir}/01-checkout-signed-out.png` });

await page.getByRole("link", { name: "Sign in to continue" }).click();
await page.waitForURL(/\/login/);

await page.locator('input[type="email"]').fill(`nobody.${stamp}@example.com`);
await page.locator('input[type="password"]').fill("wrong-password");
await page.getByRole("button", { name: "Sign in", exact: true }).click();
await page.locator(".journey-error, .checkout-error").first().waitFor();
check("AUTH-2 wrong password shows error",
  (await page.locator(".journey-error, .checkout-error").first().innerText()).includes("Invalid email or password"));

const email = `smoke.customer.${stamp}@example.com`;
await page.getByRole("button", { name: /Create an account/ }).click();
await page.getByLabel("Full name").fill("Smoke Customer");
await page.getByLabel("Phone number").fill(uniquePhone());
await page.locator('input[type="email"]').fill(email);
await page.locator('input[type="password"]').fill(PASSWORD);
await page.screenshot({ path: `${outDir}/02-register.png` });
await page.getByRole("button", { name: "Create account" }).click();
await page.waitForURL((url) => !url.pathname.startsWith("/login"), { timeout: 15000 });
await page.waitForSelector(".cart-drawer", { timeout: 15000 });
check("AUTH-3 register signs in and reopens the cart", true, page.url());
check("AUTH-4 sign-in returns to checkout with the cart intact",
  await page.getByRole("button", { name: "Place order" }).isVisible()
  && Object.keys(JSON.parse(await page.evaluate(() => sessionStorage.getItem("freshloop:cart")))).length === 1);
check("AUTH-5 header shows Sign out", await page.getByText("Sign out").count() === 1);

// --- Checkout -----------------------------------------------------------------
const stockBefore = await stockOf(first.productId);
const cartTotal = money(await page.locator(".checkout-final strong").innerText());
await page.getByRole("button", { name: "Place order" }).click();
check("CHK-1 empty address is rejected",
  (await page.locator(".journey-error, .checkout-error").first().innerText()).includes("delivery address"));
await page.getByPlaceholder(/delivery address/i).fill("12 Nguyen Hue, District 1");
await page.screenshot({ path: `${outDir}/03-checkout.png` });

await page.route("**/api/orders", (route) => route.abort(), { times: 1 });
await page.getByRole("button", { name: "Place order" }).click();
await page.getByText(/Cannot connect to the backend/).waitFor();
check("CHK-2 network failure keeps the cart and shows an error",
  await page.getByPlaceholder(/delivery address/i).isVisible());

await page.getByRole("button", { name: "Place order" }).dblclick();
await page.waitForURL(/\/orders\/.+placed=1/, { timeout: 15000 });
await page.waitForSelector(".journey-total");
const orderId = page.url().match(/orders\/([^?]+)/)[1];
const orderTotal = money(await page.locator(".journey-total").innerText());
check("CHK-3 confirmation shows persisted order",
  await page.getByText(/has been placed/).isVisible(), await page.getByRole("heading", { name: /^Order / }).innerText());
check("CHK-4 cart total equals server total", cartTotal === orderTotal, `${cartTotal} vs ${orderTotal}`);
check("CHK-5 double submit created exactly one order",
  sql(`SELECT count(*) FROM orders o JOIN users u ON u.user_id=o.user_id WHERE u.email='${email}'`) === "1");
check("CHK-6 order row matches page",
  Number(sql(`SELECT total_amount FROM orders WHERE order_id='${orderId}'`)) === orderTotal);
check("CHK-7 stock reserved",
  (await stockOf(first.productId)).reserved_quantity === stockBefore.reserved_quantity + 1
  && (await stockOf(first.productId)).available_stock === stockBefore.available_stock - 1);
check("CHK-8 cart cleared after success",
  await page.evaluate(() => sessionStorage.getItem("freshloop:cart")) === "{}");
await page.screenshot({ path: `${outDir}/04-order-confirmation.png`, fullPage: true });

await page.reload();
await page.waitForSelector(".journey-total");
check("ORD-1 order page reloads from the server", true);
await page.getByRole("button", { name: "Refresh status" }).click();
check("ORD-2 refresh keeps the order", await page.locator(".journey-table").isVisible());

// --- Quick Reorder -------------------------------------------------------------
const rec = await json(`/api/recommendations/${orderId}?warehouse_id=${hub.warehouse_id}`);
await page.goto(WEB);
await page.waitForSelector(".product-card");
await page.waitForFunction(() => document.querySelector(".reorder-note")?.textContent?.includes("not connected"), null, { timeout: 8000 })
  .then(() => check("QR-2 honest fallback while the endpoint is missing", rec.status === 404, `API ${rec.status}`))
  .catch(() => check("QR-2 honest fallback while the endpoint is missing", false));

// Contract rendering only: the response below is mocked, not a real recommendation.
const sample = (await json(`/api/warehouses/${hub.warehouse_id}/products?limit=12`)).body;
const inStock = sample.filter((item) => item.available_stock > 0);
let recHeaders = null;
await page.route("**/api/recommendations/**", async (route) => {
  recHeaders = route.request().headers();
  await route.fulfill({
    status: 200,
    contentType: "application/json",
    headers: { "Access-Control-Allow-Origin": WEB, "Access-Control-Allow-Credentials": "true" },
    body: JSON.stringify({ cache_status: "MISS", items: [
      { product_id: "00000000-0000-0000-0000-000000000000", score: 9, rank: 1, source: "personal" },
      ...inStock.slice(0, 10).map((item, index) => ({
        product_id: item.product_id, score: 1 - index / 20, rank: index + 2, source: "personal",
      })),
    ] }),
  });
});
await page.reload();
await page.waitForSelector(".reorder-row", { timeout: 8000 });
check("QR-3 mocked contract: unknown IDs dropped, order kept",
  await page.locator(".reorder-row").count() === 10
  && (await page.locator(".reorder-row strong").first().innerText()).length > 0);
check("QR-4 request carries the customer's token",
  (recHeaders?.authorization ?? "").startsWith("Bearer "));
await page.locator("#reorder").scrollIntoViewIfNeeded();
await page.screenshot({ path: `${outDir}/05-quick-reorder-mocked.png` });
await page.unroute("**/api/recommendations/**");

// --- Real-time stock ----------------------------------------------------------
await page.goto(`${WEB}/product/${first.productId}`);
await page.waitForSelector(".journey-stock:has-text('available')");
const delays = [];
for (let index = 0; index < 5; index += 1) {
  const expected = (await stockOf(first.productId)).available_stock - 1;
  await page.waitForTimeout(700 + index * 250);
  const startedAt = Date.now();
  const patched = await patchStock(first.productId, -1);
  await page.waitForSelector(`.journey-stock:has-text('${expected} available')`, { timeout: 8000 });
  delays.push(Date.now() - startedAt);
  if (patched.status !== 200) check("LIVE-2 staff PATCH", false, patched.status);
}
check("LIVE-2 staff stock change appears without reload", delays.length === 5, `${delays.join(", ")} ms`);

const blocked = await json(
  `/api/warehouses/${hub.warehouse_id}/products/${first.productId}/stock`,
  {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${await page.evaluate(() => JSON.parse(sessionStorage.getItem("freshloop:session")).accessToken)}`,
      "Idempotency-Key": `smoke-${stamp}-customer`,
    },
    body: JSON.stringify({ quantity_delta: -1 }),
  },
);
check("SEC-1 customer cannot change stock", blocked.status === 403, blocked.status);

// --- Warehouse persists, insufficient stock, expired session --------------------
await page.goto(WEB);
await page.waitForSelector(".product-card");
await page.locator("#warehouse-selector").selectOption(other.warehouse_id);
await page.waitForSelector(`text=Stock location: ${other.code}`);
await page.waitForSelector(".product-card");
await page.goto(`${WEB}/favorites`);
await page.goto(WEB);
await page.waitForSelector(`text=Stock location: ${other.code}`);
check("WH-1 warehouse selection survives navigation", true, other.code);
await page.locator("#warehouse-selector").selectOption(hub.warehouse_id);
await page.waitForSelector(`text=Stock location: ${hub.code}`);
await page.waitForSelector(".product-card");

await page.route("**/inventory/events", (route) => route.abort());
await page.reload();
await page.waitForSelector(".product-card");
const scarce = await addFirstProduct();
await openCheckout();
await page.getByPlaceholder(/delivery address/i).fill("12 Nguyen Hue, District 1");
const scarceStock = await stockOf(scarce.productId);
await patchStock(scarce.productId, -scarceStock.available_stock);
await page.getByRole("button", { name: "Place order" }).click();
await page.locator(".journey-error, .checkout-error").first().waitFor();
const stockError = await page.locator(".journey-error, .checkout-error").first().innerText();
check("CHK-9 insufficient stock (409) is shown, cart kept",
  /stock/i.test(stockError) && await page.getByRole("button", { name: "Place order" }).isVisible(), stockError);
check("CHK-10 retry as a new attempt is offered",
  await page.getByRole("button", { name: /new checkout attempt/ }).isVisible());
await page.screenshot({ path: `${outDir}/06-insufficient-stock.png` });
await patchStock(scarce.productId, scarceStock.available_stock);
await page.unroute("**/inventory/events");

await page.evaluate(() => {
  const session = JSON.parse(sessionStorage.getItem("freshloop:session"));
  sessionStorage.setItem("freshloop:session", JSON.stringify({ ...session, accessToken: "bad.token.value" }));
});
await page.goto(`${WEB}/orders/${orderId}`);
await page.getByText("Sign in to view this order.").waitFor();
check("AUTH-6 rejected token falls back to sign-in", true);

await page.getByRole("link", { name: "Sign in", exact: true }).click();
await page.waitForURL(/\/login/);
await page.locator('input[type="email"]').fill(email);
await page.locator('input[type="password"]').fill(PASSWORD);
await page.getByRole("button", { name: "Sign in", exact: true }).click();
await page.waitForURL(new RegExp(`/orders/${orderId}`));
await page.waitForSelector(".journey-total");
check("AUTH-7 sign-in returns to the order", true);

// A different customer must not read this order.
const strangerEmail = `smoke.stranger.${stamp}@example.com`;
await signUp(strangerEmail);
const strangerToken = await signIn(strangerEmail);
const stranger = await json(`/api/orders/${orderId}`, { headers: { Authorization: `Bearer ${strangerToken}` } });
check("SEC-2 another customer cannot read the order", stranger.status === 404, stranger.status);

await page.goto(WEB);
await page.getByText("Sign out").click();
await page.waitForSelector("text=Sign in");
check("AUTH-8 sign-out clears the session",
  await page.evaluate(() => sessionStorage.getItem("freshloop:session")) === null);

// --- Cart across client-side navigation -----------------------------------------
await page.evaluate(() => sessionStorage.removeItem("freshloop:cart"));
await page.goto(WEB);
await page.waitForSelector(".product-card");
const cards = page.locator(".product-card").filter({ hasNot: page.locator(".qty-control") });
await cards.nth(0).locator(".product-bottom button").first().click();
await page.waitForFunction(() => sessionStorage.getItem("freshloop:cart")?.includes(":1"));
await cards.nth(1).locator("h3 a").click();
await page.waitForSelector(".journey-stock:visible:has-text('available')");
await page.getByRole("button", { name: "Add to cart" }).click();
await page.getByRole("link", { name: /Go to cart/ }).click();
await page.waitForSelector(".cart-drawer", { timeout: 8000 });
await page.waitForTimeout(600);
const storedCart = Object.keys(JSON.parse(await page.evaluate(() => sessionStorage.getItem("freshloop:cart"))));
check("CART-NAV items added on two pages both stay in the cart",
  storedCart.length === 2 && await page.locator(".cart-drawer .cart-row").count() === 2,
  `stored ${storedCart.length}, shown ${await page.locator(".cart-drawer .cart-row").count()}`);

// --- Responsive ---------------------------------------------------------------
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(WEB);
await page.waitForSelector(".product-card");
const overflow = async () => page.evaluate(
  () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
);
check("UI-1 home: no horizontal overflow at 390 px", await overflow() <= 0, await overflow());
await page.screenshot({ path: `${outDir}/07-mobile-home.png` });
await page.setViewportSize({ width: 360, height: 780 });
await page.waitForTimeout(200);
check("UI-1b home: no horizontal overflow at 360 px", await overflow() <= 0, await overflow());
await page.setViewportSize({ width: 390, height: 844 });
await page.goto(`${WEB}/login`);
await page.waitForSelector(".auth-form");
check("UI-2 login: no horizontal overflow at 390 px", await overflow() <= 0, await overflow());
await page.screenshot({ path: `${outDir}/08-mobile-login.png` });
await page.goto(`${WEB}/product/${first.productId}`);
await page.waitForSelector(".journey-stock");
check("UI-3 product: no horizontal overflow at 390 px", await overflow() <= 0, await overflow());

check("JS-1 no uncaught browser errors", consoleErrors.length === 0, consoleErrors.slice(0, 2).join(" | "));
await browser.close();

const failed = results.filter((item) => !item.ok);
writeFileSync(`${outDir}/results.json`, JSON.stringify({ run, delays, results }, null, 2));
console.log(`\nRUN ${run}: ${results.length - failed.length}/${results.length} passed; SSE delays ms: ${delays.join(", ")}`);
process.exit(failed.length ? 1 : 0);
