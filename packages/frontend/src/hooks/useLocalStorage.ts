export const STORAGE_KEYS = {
  ACCESS_TOKEN: "access_token",
  DRAFT_MESSAGE: "dyvy_draft_message",
} as const;

export function clearLocalStorage() {
  Object.values(STORAGE_KEYS).forEach((key) => {
    localStorage.removeItem(key);
  });
}
