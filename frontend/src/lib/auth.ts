export const DEMO_USERNAME = "user";
export const DEMO_PASSWORD = "password";
export const AUTH_STORAGE_KEY = "kanban-studio-authenticated";
export const AUTH_TOKEN_STORAGE_KEY = "kanban-studio-access-token";

export const isValidCredentials = (username: string, password: string) =>
  username === DEMO_USERNAME && password === DEMO_PASSWORD;

export const hasStoredSession = (storage: Pick<Storage, "getItem">) =>
  storage.getItem(AUTH_STORAGE_KEY) === "true";

export const storeSession = (storage: Pick<Storage, "setItem">) => {
  storage.setItem(AUTH_STORAGE_KEY, "true");
};

export const clearSession = (storage: Pick<Storage, "removeItem">) => {
  storage.removeItem(AUTH_STORAGE_KEY);
  storage.removeItem(AUTH_TOKEN_STORAGE_KEY);
};

export const storeAccessToken = (
  storage: Pick<Storage, "setItem">,
  token: string
) => {
  storage.setItem(AUTH_TOKEN_STORAGE_KEY, token);
  storeSession(storage);
};

export const getAccessToken = (storage: Pick<Storage, "getItem">) =>
  storage.getItem(AUTH_TOKEN_STORAGE_KEY);