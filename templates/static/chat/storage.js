// Settings and drafts of this device. localStorage can be missing or throw (private windows, blocked site data):
// every access is wrapped, and the page works with an in-memory fallback.

export function createStorage(backend) {
  const memory = new Map();
  return {
    get(key, fallback = null) {
      try {
        const value = backend.getItem(key);
        if (value !== null && value !== undefined) return value;
      } catch (error) {
        // fall through to the memory copy
      }
      return memory.has(key) ? memory.get(key) : fallback;
    },
    set(key, value) {
      memory.set(key, String(value));
      try {
        backend.setItem(key, String(value));
        return true;
      } catch (error) {
        return false;
      }
    },
    remove(key) {
      memory.delete(key);
      try {
        backend.removeItem(key);
      } catch (error) {
        // nothing to do
      }
    },
  };
}

export function defaultStorage() {
  let backend = null;
  try {
    backend = globalThis.localStorage ?? null;
  } catch (error) {
    backend = null;
  }
  const unavailable = {
    getItem() { throw new Error('no storage'); },
    setItem() { throw new Error('no storage'); },
    removeItem() { throw new Error('no storage'); },
  };
  return createStorage(backend ?? unavailable);
}
