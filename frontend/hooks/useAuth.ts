"use client";

import { useSyncExternalStore } from "react";
import { getSessionSnapshot, subscribeToSession } from "../lib/auth";

const noSubscribe = () => () => {};

/**
 * `ready` is false during prerender and hydration, when the session cannot be
 * read yet; wait for it before treating a null session as signed out.
 */
export function useAuth() {
  const session = useSyncExternalStore(
    subscribeToSession,
    getSessionSnapshot,
    () => null,
  );
  const ready = useSyncExternalStore(noSubscribe, () => true, () => false);
  return { session, ready };
}
