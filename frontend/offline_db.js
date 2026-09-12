/**
 * Wave Music - High-Performance IndexedDB Offline Storage
 * Allows saving complete tracks (audio blobs + metadata + covers) directly into phone internal storage.
 * Tracks play 100% offline in subway tunnels, flights, or zero-connectivity environments.
 */

(function () {
  'use strict';

  const DB_NAME = 'WaveMusicOfflineDB';
  const DB_VERSION = 1;
  const STORE_NAME = 'tracks';

  let _dbPromise = null;

  function getDB() {
    if (_dbPromise) return _dbPromise;

    _dbPromise = new Promise((resolve, reject) => {
      if (!window.indexedDB) {
        console.warn('[OfflineDB] IndexedDB is not supported on this device');
        return resolve(null);
      }

      const request = window.indexedDB.open(DB_NAME, DB_VERSION);

      request.onupgradeneeded = (e) => {
        const db = e.target.result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
          store.createIndex('savedAt', 'savedAt', { unique: false });
          store.createIndex('artist', 'artist', { unique: false });
        }
      };

      request.onsuccess = (e) => {
        resolve(e.target.result);
      };

      request.onerror = (e) => {
        console.error('[OfflineDB] Error opening database:', e.target.error);
        resolve(null);
      };
    });

    return _dbPromise;
  }

  async function saveOfflineTrack(track, audioBlob) {
    const db = await getDB();
    if (!db || !track || !track.id) return false;

    return new Promise((resolve, reject) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);

        const record = {
          id: String(track.id),
          title: String(track.title || 'Без названия'),
          artist: String(track.artist || 'Неизвестный артист'),
          duration: String(track.duration || '3:00'),
          duration_ms: track.duration_ms || 180000,
          cover: String(track.cover || 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=400'),
          blob: audioBlob,
          size: audioBlob.size,
          savedAt: Date.now(),
          isOffline: true
        };

        const req = store.put(record);
        req.onsuccess = () => resolve(true);
        req.onerror = (err) => {
          console.error('[OfflineDB] Failed to put track:', err);
          resolve(false);
        };
      } catch (err) {
        console.error('[OfflineDB] Transaction error in saveOfflineTrack:', err);
        resolve(false);
      }
    });
  }

  async function getOfflineTrack(id) {
    const db = await getDB();
    if (!db || !id) return null;

    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.get(String(id));
        req.onsuccess = () => resolve(req.result || null);
        req.onerror = () => resolve(null);
      } catch (e) {
        resolve(null);
      }
    });
  }

  async function isOfflineTrack(id) {
    if (!id) return false;
    const track = await getOfflineTrack(id);
    return Boolean(track && track.blob);
  }

  async function getAllOfflineTracks() {
    const db = await getDB();
    if (!db) return [];

    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.getAll();
        req.onsuccess = () => {
          const results = req.result || [];
          results.sort((a, b) => (b.savedAt || 0) - (a.savedAt || 0));
          resolve(results);
        };
        req.onerror = () => resolve([]);
      } catch (e) {
        resolve([]);
      }
    });
  }

  async function deleteOfflineTrack(id) {
    const db = await getDB();
    if (!db || !id) return false;

    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const req = store.delete(String(id));
        req.onsuccess = () => resolve(true);
        req.onerror = () => resolve(false);
      } catch (e) {
        resolve(false);
      }
    });
  }

  async function getOfflineCount() {
    const db = await getDB();
    if (!db) return 0;

    return new Promise((resolve) => {
      try {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const store = tx.objectStore(STORE_NAME);
        const req = store.count();
        req.onsuccess = () => resolve(req.result || 0);
        req.onerror = () => resolve(0);
      } catch (e) {
        resolve(0);
      }
    });
  }

  // Export to window
  window.offlineDB = {
    getDB,
    saveOfflineTrack,
    getOfflineTrack,
    isOfflineTrack,
    getAllOfflineTracks,
    deleteOfflineTrack,
    getOfflineCount
  };

  console.log('[OfflineDB] IndexedDB offline storage module loaded successfully');
})();
