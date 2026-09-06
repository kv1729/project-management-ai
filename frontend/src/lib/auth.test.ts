import {
  AUTH_STORAGE_KEY,
  clearSession,
  hasStoredSession,
  isValidCredentials,
  storeSession,
} from "@/lib/auth";

describe("auth helpers", () => {
  it("accepts only the demo credentials", () => {
    expect(isValidCredentials("user", "password")).toBe(true);
    expect(isValidCredentials("User", "password")).toBe(false);
    expect(isValidCredentials("user", "wrong")).toBe(false);
  });

  it("stores and clears a session", () => {
    const storage = {
      values: {} as Record<string, string>,
      getItem(key: string) {
        return this.values[key] ?? null;
      },
      setItem(key: string, value: string) {
        this.values[key] = value;
      },
      removeItem(key: string) {
        delete this.values[key];
      },
    };

    expect(hasStoredSession(storage)).toBe(false);
    storeSession(storage);
    expect(storage.values[AUTH_STORAGE_KEY]).toBe("true");
    expect(hasStoredSession(storage)).toBe(true);
    clearSession(storage);
    expect(hasStoredSession(storage)).toBe(false);
  });
});