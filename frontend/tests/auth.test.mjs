import test from "node:test";
import assert from "node:assert/strict";

import {
  createSession,
  isSessionActive,
  safeNextPath,
} from "../lib/auth.ts";

function makeToken(claims) {
  const encode = (value) =>
    Buffer.from(JSON.stringify(value)).toString("base64url");
  return `${encode({ alg: "HS256" })}.${encode(claims)}.signature`;
}

test("createSession reads the user and role from the token", () => {
  const token = makeToken({ sub: "user-1", role: "CUSTOMER" });

  assert.deepEqual(createSession(token, 1800, 1000), {
    accessToken: token,
    userId: "user-1",
    role: "CUSTOMER",
    expiresAt: 1801000,
  });
});

test("createSession rejects malformed tokens", () => {
  assert.equal(createSession("not-a-jwt", 1800), null);
  assert.equal(createSession("a.%%%.c", 1800), null);
  assert.equal(createSession(makeToken({ role: "CUSTOMER" }), 1800), null);
});

test("a session stops being active when it expires", () => {
  const session = createSession(
    makeToken({ sub: "user-1", role: "CUSTOMER" }),
    60,
    1000,
  );

  assert.equal(isSessionActive(session, 60999), true);
  assert.equal(isSessionActive(session, 61000), false);
  assert.equal(isSessionActive(null), false);
});

test("safeNextPath keeps same-site paths", () => {
  assert.equal(safeNextPath("/?cart=open"), "/?cart=open");
  assert.equal(safeNextPath("/orders/abc"), "/orders/abc");
});

test("safeNextPath refuses anything that could leave the site", () => {
  assert.equal(safeNextPath("https://evil.example"), "/");
  assert.equal(safeNextPath("//evil.example"), "/");
  assert.equal(safeNextPath("/\\evil.example"), "/");
  assert.equal(safeNextPath(["/a", "/b"]), "/");
  assert.equal(safeNextPath(undefined), "/");
});
