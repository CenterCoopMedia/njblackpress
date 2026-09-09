// History hall — wall copies, image loading, and what the hall owns.
//
// Every image the hall shows comes from the generated wall copy manifest or
// from the public clipping index. Nothing here guesses a file path, and nothing
// here decides whether a file may be shown: that decision is already recorded.
//
// Work is cancelled by generation token. An image that finishes decoding after
// the visitor has moved to another story must not paint over what they are
// looking at now, so every caller passes the token it started with.

const MANIFEST_URL = 'data/wall-copies.json';

/**
 * @param {object} options
 * @param {() => number} options.generation current token from state.js
 */
export function createAssets({ generation = () => 0 } = {}) {
  const images = new Map();      // path -> HTMLImageElement
  const inFlight = new Map();    // path -> Promise
  const failed = new Set();
  let manifest = null;
  let byPublication = new Map();
  let bySourcePath = new Map();
  let disposed = false;

  async function loadManifest() {
    if (manifest) return manifest;
    try {
      const response = await fetch(MANIFEST_URL);
      if (!response.ok) throw new Error(String(response.status));
      const document_ = await response.json();
      manifest = document_.wallCopies || [];
    } catch {
      // A missing manifest is not a broken hall: sheets fall back to their
      // publication record design, which is the majority treatment anyway.
      manifest = [];
    }
    for (const copy of manifest) {
      bySourcePath.set(copy.sourcePath, copy);
      for (const id of copy.publicationIds || []) {
        if (!byPublication.has(id)) byPublication.set(id, copy);
      }
    }
    return manifest;
  }

  /** The wall copy cleared for a publication, or null when none is. */
  function wallCopyForPublication(id) {
    return byPublication.get(id) || null;
  }

  /** The wall copy for a public clipping path, so the book reuses one asset. */
  function wallCopyForPath(webPath) {
    return bySourcePath.get(webPath) || null;
  }

  /**
   * Decode one image. `priority` marks what the visitor is looking at now; a
   * low priority request yields to the browser rather than competing with it.
   */
  function loadImage(path, { token = generation(), priority = 'low' } = {}) {
    if (!path || disposed || failed.has(path)) return Promise.resolve(null);
    if (images.has(path)) return Promise.resolve(images.get(path));
    if (inFlight.has(path)) return inFlight.get(path).then((image) => (isCurrent(token) ? image : null));
    const work = (async () => {
      const image = new Image();
      image.decoding = 'async';
      if ('fetchPriority' in image) image.fetchPriority = priority === 'high' ? 'high' : 'low';
      image.src = path;
      try {
        await image.decode();
      } catch {
        failed.add(path);
        return null;
      }
      if (disposed) return null;
      images.set(path, image);
      return image;
    })();
    inFlight.set(path, work);
    work.finally(() => inFlight.delete(path));
    return work.then((image) => (isCurrent(token) ? image : null));
  }

  function isCurrent(token) {
    return token == null || token === generation();
  }

  /** Already decoded, so a paint can use it without waiting. */
  function peek(path) {
    return images.get(path) || null;
  }

  /**
   * A byte estimate for what the hall holds, so package 3 can measure the
   * budget rather than guess it. Decoded images are counted as RGBA8.
   */
  function residentBytes() {
    let total = 0;
    for (const image of images.values()) {
      total += (image.naturalWidth || 0) * (image.naturalHeight || 0) * 4;
    }
    return total;
  }

  function forget(path) {
    images.delete(path);
  }

  function dispose() {
    disposed = true;
    images.clear();
    inFlight.clear();
    failed.clear();
    byPublication = new Map();
    bySourcePath = new Map();
  }

  return {
    loadManifest,
    wallCopyForPublication,
    wallCopyForPath,
    loadImage,
    peek,
    forget,
    residentBytes,
    dispose,
    get manifest() { return manifest || []; }
  };
}
