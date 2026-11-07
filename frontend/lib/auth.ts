/**
 * Storefront session: the backend JWT plus the claims the UI needs.
 * The token is kept in sessionStorage so it ends with the tab. Its claims are
 * read for display only; the backend verifies the signature on every request.
 */

export type Session = {
  accessToken: string;
  userId: string;
  role: string;
  expiresAt: number;
};

const STORAGE_KEY = "freshloop:session";

function decodeClaims(token: string): { sub?: unknown; role?: unknown } | null {
  const payload = token.split(".")[1];
  if (!payload) return null;
  try {
    return JSON.parse(atob(payload.replace(/-/g, "+").replace(/_/g, "/")));
  } catch {
    return null;
  }
}

/** Builds a session from a login response; null if the token is malformed. */
export function createSession(
  accessToken: string,
  expiresInSeconds: number,
  now: number = Date.now(),
): Session | null {
  const claims = decodeClaims(accessToken);
  if (typeof claims?.sub !== "string" || typeof claims.role !== "string") {
    return null;
  }
  return {
    accessToken,
    userId: claims.sub,
    role: claims.role,
    expiresAt: now + expiresInSeconds * 1000,
  };
}

export function isSessionActive(
  session: Session | null,
  now: number = Date.now(),
): session is Session {
  return session !== null && session.expiresAt > now;
}

/** Only same-site paths are allowed, so `next` cannot redirect off the site. */
export function safeNextPath(value: unknown): string {
  if (typeof value !== "string") return "/";
  return /^\/(?![/\\])/.test(value) ? value : "/";
}

const listeners = new Set<() => void>();
let cachedRaw: string | null = null;
let cachedSession: Session | null = null;

function readRaw(): string | null {
  try {
    return window.sessionStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function notify() {
  listeners.forEach((listener) => listener());
}

/** Returns a stable reference until the stored session changes or expires. */
export function getSessionSnapshot(): Session | null {
  const raw = readRaw();
  if (raw !== cachedRaw) {
    cachedRaw = raw;
    try {
      cachedSession = raw ? (JSON.parse(raw) as Session) : null;
    } catch {
      cachedSession = null;
    }
  }
  return isSessionActive(cachedSession) ? cachedSession : null;
}

export function saveSession(session: Session) {
  try {
    window.sessionStorage.setItem(STORAGE_KEY, JSON.stringify(session));
  } catch {
    // Without storage the customer simply stays signed out.
  }
  notify();
}

export function clearSession() {
  try {
    window.sessionStorage.removeItem(STORAGE_KEY);
  } catch {
    // Nothing was stored.
  }
  notify();
}

export function subscribeToSession(listener: () => void): () => void {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
