const STORAGE_KEY = "weekend_agent_device_user_id_v1";

export function getDeviceUserId(): string {
  if (typeof window === "undefined") return "phone_user";
  try {
    const existing = window.localStorage.getItem(STORAGE_KEY);
    if (existing?.trim()) return existing;
    const id = `phone_${randomId()}`;
    window.localStorage.setItem(STORAGE_KEY, id);
    return id;
  } catch {
    return "phone_user";
  }
}

function randomId(): string {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi?.randomUUID) {
    return cryptoApi.randomUUID().replace(/-/g, "").slice(0, 16);
  }
  return `${Date.now().toString(36)}${Math.random().toString(36).slice(2, 10)}`;
}
