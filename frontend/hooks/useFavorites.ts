"use client";

import { useMemo, useSyncExternalStore } from "react";

const STORAGE_KEY = "freshloop-favorites";
const CHANGE_EVENT = "freshloop-favorites-change";

// Dùng trong phiên hiện tại nếu localStorage không sử dụng được.
let memorySnapshot = "[]";
let memoryOnly = false;

function parseFavorites(raw: string | null): number[] {
  try {
    const saved: unknown = JSON.parse(raw ?? "[]");

    if (!Array.isArray(saved)) return [];

    return [
      ...new Set(
        saved.filter(
          (id): id is number =>
            typeof id === "number" && Number.isInteger(id)
        )
      ),
    ];
  } catch {
    return [];
  }
}

function getSnapshot(): string {
  if (memoryOnly) return memorySnapshot;

  try {
    memorySnapshot = window.localStorage.getItem(STORAGE_KEY) ?? "[]";
  } catch {
    memoryOnly = true;
  }

  return memorySnapshot;
}

function getServerSnapshot(): null {
  return null;
}

function subscribe(onStoreChange: () => void) {
  // Nhận thay đổi localStorage từ tab khác.
  const handleStorage = (event: StorageEvent) => {
    if (memoryOnly) return;

    try {
      if (
        event.storageArea === window.localStorage &&
        (event.key === STORAGE_KEY || event.key === null)
      ) {
        onStoreChange();
      }
    } catch {
      // Không truy cập được storage thì giữ dữ liệu trong phiên.
    }
  };

  // Nhận thay đổi từ các component trong cùng tab.
  window.addEventListener(CHANGE_EVENT, onStoreChange);
  window.addEventListener("storage", handleStorage);

  return () => {
    window.removeEventListener(CHANGE_EVENT, onStoreChange);
    window.removeEventListener("storage", handleStorage);
  };
}

function toggleFavorite(id: number) {
  // Đọc dữ liệu mới nhất trước khi cập nhật.
  const current = parseFavorites(getSnapshot());

  const next = current.includes(id)
    ? current.filter((productId) => productId !== id)
    : [...current, id];

  memorySnapshot = JSON.stringify(next);

  if (!memoryOnly) {
    try {
      window.localStorage.setItem(STORAGE_KEY, memorySnapshot);
    } catch {
      memoryOnly = true;
    }
  }

  window.dispatchEvent(new Event(CHANGE_EVENT));
}

export function useFavorites() {
  const snapshot = useSyncExternalStore(
    subscribe,
    getSnapshot,
    getServerSnapshot
  );

  const favorites = useMemo(
    () => parseFavorites(snapshot),
    [snapshot]
  );

  return {
    favorites,
    favoritesLoaded: snapshot !== null,
    toggleFavorite,
  };
}