// History hall — the story reader. Plain DOM, no drawing code.
//
// The reader is the story. It opens with the full text of the stop, its
// citation, its confidence wording, its rights note, and any required credit,
// and none of that waits for a camera move or a page turn to finish. On a small
// screen it becomes a full height reading sheet with an ordinary vertical flow.

const FOCUSABLE = 'a[href], button:not([disabled]), select, input, [tabindex]:not([tabindex="-1"])';

/**
 * Keep Tab inside a modal container. This is called from the keydown listener
 * the container already has, rather than adding one of its own: a trap that
 * registered its own listener would leave one behind every time the reader was
 * opened on a second story.
 */
function trapKey(event, container) {
  if (event.key !== 'Tab') return;
  const items = [...container.querySelectorAll(FOCUSABLE)].filter((el) => el.offsetParent !== null);
  if (!items.length) return;
  const first = items[0];
  const last = items[items.length - 1];
  if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
  else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
}

/**
 * @param {object} options
 * @param {HTMLElement} options.root the reader region already in the page
 * @param {HTMLElement} options.inspector the image inspector's own element
 */
export function createReader(options) {
  const {
    root, inspector, narrow,
    onPrevious = () => {}, onNext = () => {}, onClose = () => {},
    onGotoStop = () => {}, onSelectPublication = () => {}, copyLink = () => '',
    // Inspecting a clipping is a state of the hall, not a private mode of the
    // reader, so the request goes out and the inspector opens on the way back.
    onOpenClipping = () => {}, onCloseClipping = () => {},
    // Every listener the reader registers goes through the hall's counter, so a
    // repeated open and close cycle can be shown not to accumulate any.
    listen = (target, type, handler, opts) => target.addEventListener(type, handler, opts)
  } = options;

  root.innerHTML = `
    <div class="hall-reader-head">
      <div>
        <p class="hall-reader-kicker" data-reader-era></p>
        <h2 id="hall-reader-title" tabindex="-1"></h2>
      </div>
      <button type="button" class="woven-btn" data-reader="close">Close</button>
    </div>
    <div class="hall-reader-controls">
      <button type="button" class="woven-btn" data-reader="previous">Previous</button>
      <button type="button" class="woven-btn" data-reader="next">Next</button>
      <p class="hall-reader-count" data-reader-count role="status"></p>
    </div>
    <label class="hall-reader-jump">Go to stop
      <select data-reader="stops"></select>
    </label>
    <figure class="hall-reader-plate" data-reader-plate hidden>
      <img alt="" data-reader-image>
      <p class="hall-reader-missing" data-reader-missing hidden></p>
      <figcaption data-reader-figcaption></figcaption>
    </figure>
    <div class="hall-reader-body" data-reader-body></div>
    <div class="hall-reader-actions">
      <button type="button" class="woven-btn" data-reader="clipping" hidden>View clipping</button>
      <button type="button" class="woven-btn" data-reader="copy">Copy link</button>
      <span class="hall-reader-note" data-reader-status role="status"></span>
    </div>`;

  const parts = {
    era: root.querySelector('[data-reader-era]'),
    title: root.querySelector('#hall-reader-title'),
    count: root.querySelector('[data-reader-count]'),
    body: root.querySelector('[data-reader-body]'),
    stopList: root.querySelector('[data-reader="stops"]'),
    plate: root.querySelector('[data-reader-plate]'),
    image: root.querySelector('[data-reader-image]'),
    missing: root.querySelector('[data-reader-missing]'),
    figcaption: root.querySelector('[data-reader-figcaption]'),
    previous: root.querySelector('[data-reader="previous"]'),
    next: root.querySelector('[data-reader="next"]'),
    close: root.querySelector('[data-reader="close"]'),
    clipping: root.querySelector('[data-reader="clipping"]'),
    copy: root.querySelector('[data-reader="copy"]'),
    status: root.querySelector('[data-reader-status]')
  };

  let story = null;
  let stop = null;
  let opened = false;
  let returnFocus = null;
  // True while the reading sheet covers the page and behaves as a dialog.
  let modal = false;

  listen(parts.previous, 'click', () => onPrevious());
  listen(parts.next, 'click', () => onNext());
  listen(parts.close, 'click', () => onClose());
  listen(parts.stopList, 'change', () => onGotoStop(parts.stopList.value));
  listen(parts.clipping, 'click', () => requestInspector());
  listen(parts.copy, 'click', async () => {
    const url = copyLink();
    try {
      await navigator.clipboard.writeText(url);
      parts.status.textContent = 'Link copied.';
    } catch {
      parts.status.textContent = url;
    }
  });
  // An image the browser cannot fetch is said in words, with the stop's own
  // metadata still beside it. The reader never shows a broken picture frame.
  listen(parts.image, 'error', () => {
    if (!stop || !stop.clipping) return;
    parts.image.hidden = true;
    parts.missing.hidden = false;
    parts.missing.textContent = 'Image unavailable. This clipping could not be loaded; its citation and rights note are below.';
    parts.clipping.disabled = true;
  });
  listen(root, 'click', (event) => {
    const button = event.target.closest('[data-reader-pub]');
    if (button) onSelectPublication(Number(button.dataset.readerPub));
  });
  listen(root, 'keydown', (event) => {
    if (modal) trapKey(event, root);
    if (event.key === 'Escape' && opened) { event.stopPropagation(); onClose(); }
    // Left and right turn pages, but only while the focus is inside the reader
    // and not inside a control that owns those keys itself.
    if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;
    if (!opened || event.altKey || event.metaKey || event.ctrlKey) return;
    const target = event.target;
    if (target.closest('select, input, textarea, [contenteditable="true"]')) return;
    event.preventDefault();
    if (event.key === 'ArrowLeft') onPrevious(); else onNext();
  });

  // A swipe across the picture turns the page, the way a thumb would. It is
  // limited to the picture: a swipe that is mostly vertical, or that starts in
  // the text, belongs to the page's own scrolling.
  const SWIPE_MIN = 42;
  let swipe = null;
  // A picture is draggable by default, and the browser's own drag cancels the
  // pointer the moment it starts, so the swipe would never finish.
  parts.image.draggable = false;
  listen(parts.plate, 'dragstart', (event) => event.preventDefault());
  listen(parts.plate, 'pointerdown', (event) => {
    if (event.pointerType === 'mouse' && event.buttons !== 1) return;
    swipe = { x: event.clientX, y: event.clientY, id: event.pointerId };
  });
  listen(parts.plate, 'pointerup', (event) => {
    if (!swipe || event.pointerId !== swipe.id) return;
    const dx = event.clientX - swipe.x;
    const dy = event.clientY - swipe.y;
    swipe = null;
    if (Math.abs(dx) < SWIPE_MIN || Math.abs(dx) <= Math.abs(dy)) return;
    // Swiping left carries the page away and brings the next one in.
    if (dx < 0) onNext(); else onPrevious();
  });
  listen(parts.plate, 'pointercancel', () => { swipe = null; });

  function paragraph(text, className) {
    const p = document.createElement('p');
    if (className) p.className = className;
    p.textContent = text;
    return p;
  }

  function render() {
    parts.era.textContent = story.note ? `${story.era} · ${story.note}` : story.era;
    parts.title.textContent = story.title;
    parts.count.textContent = `Stop ${stop.index + 1} of ${story.stopCount}`;
    parts.previous.disabled = stop.index === 0;
    parts.next.disabled = stop.index === story.stopCount - 1;

    parts.stopList.replaceChildren(...story.stops.map((item, index) => {
      const option = document.createElement('option');
      option.value = item.key;
      option.textContent = `${index + 1}. ${item.title}`;
      option.selected = item.key === stop.key;
      return option;
    }));

    const body = document.createDocumentFragment();
    body.append(paragraph(stop.date, 'hall-reader-date'));
    const heading = document.createElement('h3');
    heading.textContent = stop.title;
    body.append(heading);
    if (stop.description) body.append(paragraph(stop.description));
    // The story's own summary opens the reading, once, at its first stop.
    if (stop.index === 0 && story.summary) body.append(paragraph(story.summary));
    if (story.thinlySourced) body.append(paragraph('Thinly sourced. Read this story as a lead, not a finding.', 'hall-reader-flag'));
    // Anything the archive did not record as high confidence is said in words.
    if (stop.confidence && stop.confidence !== 'high') {
      body.append(paragraph(`Confidence: ${stop.confidence}.`, 'hall-reader-flag'));
    }

    if (stop.publications.length) {
      const heading2 = document.createElement('h4');
      heading2.textContent = 'Publications in this stop';
      body.append(heading2);
      const list = document.createElement('ul');
      list.className = 'hall-reader-pubs';
      for (const publication of stop.publications) {
        const item = document.createElement('li');
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'woven-btn';
        button.dataset.readerPub = String(publication.id);
        button.textContent = publication.name;
        item.append(button);
        list.append(item);
      }
      body.append(list);
    }

    const sources = document.createElement('div');
    sources.className = 'hall-reader-sources';
    const sourceHeading = document.createElement('h4');
    sourceHeading.textContent = 'Source';
    sources.append(sourceHeading);
    for (const citation of stop.citations) {
      const cite = document.createElement('cite');
      cite.textContent = citation;
      sources.append(cite);
    }
    if (!stop.citations.length) sources.append(paragraph('No source citation is recorded for this stop.'));
    if (stop.rightsNote) sources.append(paragraph(stop.rightsNote, 'hall-reader-rights'));
    body.append(sources);
    parts.body.replaceChildren(body);

    const clip = stop.clipping;
    parts.clipping.hidden = !clip;
    parts.clipping.disabled = false;
    parts.missing.hidden = true;
    if (clip) {
      parts.plate.hidden = false;
      parts.image.hidden = false;
      parts.image.src = clip.path;
      parts.image.alt = clip.alt;
      parts.figcaption.textContent = clip.caption || '';
    } else {
      parts.plate.hidden = true;
      parts.image.removeAttribute('src');
    }
    parts.status.textContent = '';
  }

  // ---- image inspector ----------------------------------------------------
  let inspectorOpen = false;
  let inspectorReturn = null;
  let zoom = 1;

  inspector.innerHTML = `
    <div class="hall-inspector-inner" role="dialog" aria-modal="true" aria-labelledby="hall-inspector-title">
      <div class="hall-inspector-bar">
        <h2 id="hall-inspector-title">Clipping</h2>
        <button type="button" class="woven-btn" data-inspect="out" aria-label="Zoom out">−</button>
        <button type="button" class="woven-btn" data-inspect="in" aria-label="Zoom in">+</button>
        <button type="button" class="woven-btn" data-inspect="reset">Reset</button>
        <button type="button" class="woven-btn" data-inspect="close">Close</button>
      </div>
      <div class="hall-inspector-scroll"><img alt="" data-inspect-image></div>
      <figcaption class="hall-inspector-credit" data-inspect-credit></figcaption>
    </div>`;
  const inspectorImage = inspector.querySelector('[data-inspect-image]');
  const inspectorCredit = inspector.querySelector('[data-inspect-credit]');
  const inspectorInner = inspector.querySelector('.hall-inspector-inner');

  function applyZoom() {
    inspectorImage.style.width = `${Math.round(zoom * 100)}%`;
  }
  listen(inspector.querySelector('[data-inspect="in"]'), 'click', () => { zoom = Math.min(4, zoom * 1.4); applyZoom(); });
  listen(inspector.querySelector('[data-inspect="out"]'), 'click', () => { zoom = Math.max(0.5, zoom / 1.4); applyZoom(); });
  listen(inspector.querySelector('[data-inspect="reset"]'), 'click', () => { zoom = 1; applyZoom(); });
  // Every one of these asks the hall to leave clipping inspection, and only
  // while it is still open: the hall's own Escape handler runs first, and a
  // second request would close the story underneath.
  listen(inspector.querySelector('[data-inspect="close"]'), 'click', () => { if (inspectorOpen) onCloseClipping(); });
  listen(inspector, 'keydown', (event) => {
    if (!inspectorOpen) return;
    trapKey(event, inspectorInner);
    if (event.key === 'Escape') { event.stopPropagation(); onCloseClipping(); }
  });
  listen(inspector, 'click', (event) => { if (inspectorOpen && event.target === inspector) onCloseClipping(); });
  // The large image can fail too, and the credit stays under it either way.
  listen(inspectorImage, 'error', () => {
    inspectorImage.hidden = true;
    inspectorCredit.textContent = `Image unavailable. ${inspectorCredit.textContent}`.trim();
  });

  /** Ask the hall to enter clipping inspection. The state decides, not the button. */
  function requestInspector() {
    const clip = stop && stop.clipping;
    if (!clip) return;
    onOpenClipping({
      webPath: clip.fullPath || clip.path,
      alt: clip.alt,
      caption: clip.caption,
      citation: clip.citation,
      rightsNote: clip.rightsNote,
      stopId: stop.key
    });
  }

  /** Show the inspector. Called when the state has entered clipping mode. */
  function openInspector(overlay) {
    const clip = overlay || (stop && stop.clipping && {
      webPath: stop.clipping.fullPath || stop.clipping.path,
      alt: stop.clipping.alt,
      caption: stop.clipping.caption,
      citation: stop.clipping.citation,
      rightsNote: stop.clipping.rightsNote
    });
    if (!clip) return;
    inspectorReturn = document.activeElement;
    inspectorImage.hidden = false;
    inspectorImage.src = clip.webPath;
    inspectorImage.alt = clip.alt || '';
    inspectorCredit.textContent = [clip.caption, clip.citation, clip.rightsNote].filter(Boolean).join(' · ');
    zoom = 1;
    applyZoom();
    inspector.hidden = false;
    inspectorOpen = true;
    inspector.querySelector('[data-inspect="close"]').focus();
  }

  /** Hide it again. Called when the state has left clipping mode. */
  function closeInspector() {
    if (!inspectorOpen) return;
    inspector.hidden = true;
    inspectorOpen = false;
    if (inspectorReturn && document.contains(inspectorReturn)) inspectorReturn.focus();
  }

  // ---- modality -----------------------------------------------------------
  // On a small screen the sheet covers the page, so it behaves as a dialog:
  // named, focused, escapable, modal, and it gives focus back when it closes.
  // On a wide screen it is a region beside the hall and nothing is trapped. The
  // window can change shape while the reader is open, so this is decided again
  // on every change of the media query rather than once at open.
  const stage = root.parentElement;
  let inertBefore = null;

  /** While the sheet is modal nothing behind it may be reached. */
  function setBackgroundInert(on) {
    if (!stage) return;
    if (on) {
      if (inertBefore) return;
      inertBefore = new Map();
      for (const element of stage.children) {
        if (element === root || element === inspector) continue;
        // Each element's own value goes back afterwards: the publication index
        // sets its own while a record is open.
        inertBefore.set(element, element.inert);
        element.inert = true;
      }
    } else if (inertBefore) {
      for (const [element, value] of inertBefore) element.inert = value;
      inertBefore = null;
    }
  }

  function applyModality() {
    modal = opened && narrow.matches;
    root.setAttribute('role', modal ? 'dialog' : 'region');
    if (modal) root.setAttribute('aria-modal', 'true');
    else root.removeAttribute('aria-modal');
    setBackgroundInert(modal);
  }
  listen(narrow, 'change', () => { if (opened) applyModality(); });

  return {
    get isOpen() { return opened; },
    get inspectorOpen() { return inspectorOpen; },
    get isModal() { return modal; },
    requestInspector,
    openInspector,
    closeInspector,
    open(storyView, stopView) {
      story = storyView;
      stop = stopView;
      returnFocus = document.activeElement;
      root.hidden = false;
      opened = true;
      render();
      applyModality();
      parts.title.focus({ preventScroll: true });
    },
    setStop(stopView) {
      if (!opened) return;
      stop = stopView;
      render();
    },
    close() {
      if (!opened) return;
      closeInspector();
      opened = false;
      root.hidden = true;
      applyModality();
      if (returnFocus && document.contains(returnFocus)) returnFocus.focus({ preventScroll: true });
      returnFocus = null;
    },
    dispose() {
      closeInspector();
      opened = false;
      applyModality();
      root.hidden = true;
      root.replaceChildren();
      inspector.replaceChildren();
    }
  };
}
