// History hall — wall copies, image loading, and what the hall owns.
//
// Every image the hall shows comes from the generated wall copy manifest or
// from the public clipping index. Nothing here guesses a file path, and nothing
// here decides whether a file may be shown: that decision is already recorded.
//
// Work is cancelled by generation token. An image that finishes decoding after
// the visitor has moved to another story must not paint over what they are
// looking at now, so every caller passes the token it started with.
//
// Decoded images are owned, not cached for ever. The hall names its working set
// — the sheets it has painted, the open spread, and the stops either side of it
// — and everything outside that set is released. Without that, walking the hall
// once would hold all 55 wall copies decoded at the same time.

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
   * The promise resolves to null when the token is no longer current, so a late
   * arrival can never paint over the view the visitor moved on to.
   */
  function loadImage(path, { token = generation(), priority = 'low' } = {}) {
    if (!path || disposed || failed.has(path)) return Promise.resolve(null);
    if (images.has(path)) return Promise.resolve(isCurrent(token) ? images.get(path) : null);
    if (inFlight.has(path)) return inFlight.get(path).then((image) => (isCurrent(token) ? image : null));
    const work = (async () => {
      const image = new Image();
      image.decoding = 'async';
      if ('fetchPriority' in image) image.fetchPriority = priority === 'high' ? 'high' : 'low';
      image.src = path;
      try {
        await image.decode();
      } catch {
        // A file that will not decode is remembered, so the hall shows the
        // image-unavailable wording instead of asking for it again on every
        // repaint.
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

  /** True once a file has failed to decode. The caller says so in words. */
  function hasFailed(path) {
    return failed.has(path);
  }

  /**
   * Keep only the working set. Everything else is released: the map entry goes
   * and the element's source is dropped, which is what lets the browser free the
   * decoded pixels rather than holding them behind a live reference.
   *
   * @param {Iterable<string>} keep paths the hall is using right now
   * @returns {number} how many decoded images were released
   */
  function evict(keep) {
    const working = keep instanceof Set ? keep : new Set(keep || []);
    let released = 0;
    for (const [path, image] of [...images]) {
      if (working.has(path)) continue;
      images.delete(path);
      // removeAttribute rather than src = '', which some browsers treat as a
      // request for the page itself.
      image.removeAttribute('src');
      released += 1;
    }
    return released;
  }

  /**
   * A byte estimate for the decoded images the hall holds. Decoded pixels are
   * counted as RGBA8; the compressed file on the network is a different number.
   */
  function residentBytes() {
    let total = 0;
    for (const image of images.values()) {
      total += (image.naturalWidth || 0) * (image.naturalHeight || 0) * 4;
    }
    return total;
  }

  function dispose() {
    disposed = true;
    for (const image of images.values()) image.removeAttribute('src');
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
    hasFailed,
    evict,
    residentBytes,
    dispose,
    /** Counters for the review: what the hall owns and what it is still waiting for. */
    get decodedImages() { return images.size; },
    get pendingImages() { return inFlight.size; },
    get failedImages() { return failed.size; },
    get manifest() { return manifest || []; }
  };
}
