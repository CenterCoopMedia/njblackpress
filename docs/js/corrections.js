(() => {
  const endpoint = 'https://blackpress-corrections.amditis.tech/report';
  const publicRoot = 'https://centercoopmedia.github.io/njblackpress/';
  const footer = document.querySelector('footer[data-site-footer] ul');
  if (!footer) return;
  const item = document.createElement('li');
  item.innerHTML = '<button type="button" data-submit-correction class="correction-trigger">Submit a correction</button>';
  footer.prepend(item);

  const dialog = document.createElement('dialog');
  dialog.className = 'correction-dialog';
  dialog.setAttribute('aria-labelledby', 'correction-title');
  dialog.innerHTML = `<form>
    <div class="correction-heading"><h2 id="correction-title">Submit a correction</h2>
      <button type="button" data-correction-close aria-label="Close correction form"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true" focusable="false"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>
    <p id="correction-context"></p>
    <p>Tell us what needs to change. Your report and supporting links may be included in a public issue after review. Do not include private information.</p>
    <label for="correction-description">What needs to be corrected?</label>
    <textarea id="correction-description" name="description" required minlength="10" maxlength="4000" rows="4"></textarea>
    <label for="correction-fix">Suggested correction <span>(optional)</span></label>
    <textarea id="correction-fix" name="suggested_fix" maxlength="4000" rows="3"></textarea>
    <label for="correction-source">Supporting source link <span>(optional)</span></label>
    <input id="correction-source" name="source_url" type="url" maxlength="2048" placeholder="https://">
    <div hidden aria-hidden="true"><label>Leave this empty<input name="website" tabindex="-1" autocomplete="off"></label></div>
    <p id="correction-status" role="status" aria-live="polite"></p>
    <div class="correction-actions"><button type="submit">Send correction</button><button type="button" data-correction-close>Cancel</button></div>
  </form>`;
  document.body.append(dialog);
  const form = dialog.querySelector('form');
  const status = dialog.querySelector('#correction-status');
  const submit = dialog.querySelector('[type="submit"]');
  let context = null;
  let lastFocus = null;
  let pending = false;
  let lastPayload = '';
  let requestId = '';
  let received = false;
  const drafts = new Map();

  function pageContext(button) {
    let path = location.pathname.split('/njblackpress/')[1] ?? location.pathname.replace(/^\//, '');
    if (!path || path.endsWith('/')) path += 'index.html';
    const url = new URL(path || 'index.html', publicRoot);
    const params = new URLSearchParams(location.search);
    const pageKeys = {
      'publication.html': ['id'], 'story.html': ['id'], 'era.html': ['decade'],
      'historical-notes.html': ['pub', 'story', 'decade', 'stop', 'nogl', 'twin'],
      'woven.html': ['pub', 'story', 'decade', 'stop', 'nogl', 'twin'],
    };
    for (const key of pageKeys[path] || []) {
      if (params.has(key)) url.searchParams.set(key, params.get(key));
    }
    const recordId = button?.dataset.correctionRecordId;
    if (['publication.html', 'historical-notes.html', 'woven.html'].includes(path) && /^[1-9][0-9]{0,3}$/.test(recordId || '')) {
      url.searchParams.set(url.pathname.endsWith('/publication.html') ? 'id' : 'pub', recordId);
    }
    url.hash = location.hash;
    return { url: url.href, title: (button?.dataset.correctionTitle || document.title).slice(0, 200) };
  }

  function open(button) {
    if (dialog.open || pending) return;
    context = pageContext(button);
    const saved = drafts.get(context.url);
    form.reset();
    for (const name of ['description', 'suggested_fix', 'source_url']) form.elements[name].value = saved?.[name] || '';
    requestId = saved?.requestId || '';
    lastPayload = saved?.lastPayload || '';
    received = false;
    submit.disabled = false;
    submit.textContent = 'Send correction';
    dialog.querySelector('#correction-context').textContent = context.title;
    status.textContent = '';
    lastFocus = button;
    dialog.showModal();
    form.elements.description.focus();
  }

  dialog.addEventListener('close', () => {
    if (!received && context) {
      drafts.set(context.url, { ...Object.fromEntries(new FormData(form)), requestId, lastPayload });
    }
    lastFocus?.focus();
  });
  dialog.addEventListener('cancel', event => { if (pending) event.preventDefault(); });
  // Keep the hall's Escape handler and other page shortcuts out of the modal.
  dialog.addEventListener('keydown', event => {
    event.stopPropagation();
    if (pending && event.key === 'Escape') event.preventDefault();
    if (event.key !== 'Tab') return;
    const items = [...dialog.querySelectorAll('button:not([disabled]), input, textarea')]
      .filter(element => element.getClientRects().length);
    const first = items[0];
    const last = items[items.length - 1];
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault();
      first.focus();
    }
  });
  dialog.addEventListener('click', event => {
    if (event.target.closest('[data-correction-close]') && !pending) dialog.close();
  });
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-submit-correction]');
    if (button) open(button);
  });
  let waitingForPublication = false;
  function openFromHash() {
    if (location.hash !== '#submit-correction') return;
    if (location.pathname.endsWith('/publication.html') && !document.documentElement.dataset.publicationReady) {
      if (!waitingForPublication) {
        waitingForPublication = true;
        document.addEventListener('publication-ready', () => {
          waitingForPublication = false;
          openFromHash();
        }, { once: true });
      }
      return;
    }
    open(document.querySelector('[data-submit-correction][data-correction-title]') || document.querySelector('[data-submit-correction]'));
  }
  window.addEventListener('hashchange', openFromHash);
  openFromHash();

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (pending || received || !form.reportValidity()) return;
    const fields = Object.fromEntries(new FormData(form));
    const payload = { ...context, ...fields };
    const signature = JSON.stringify(payload);
    if (signature !== lastPayload) {
      requestId = crypto.randomUUID().replaceAll('-', '');
      lastPayload = signature;
    }
    pending = true;
    form.querySelectorAll('input, textarea').forEach(field => { field.readOnly = true; });
    dialog.querySelectorAll('[data-correction-close]').forEach(button => { button.disabled = true; });
    submit.disabled = true;
    submit.textContent = 'Sending…';
    form.elements.description.focus();
    status.textContent = 'Sending your correction…';
    try {
      const response = await fetch(endpoint, {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        credentials: 'omit', signal: AbortSignal.timeout(20000),
        body: JSON.stringify({ ...payload, request_id: requestId }),
      });
      const result = await response.json();
      if (response.status === 409) {
        requestId = '';
        lastPayload = '';
      }
      if (!response.ok || result.success !== true || result.id !== 'bp_' + requestId) throw new Error(result.error || 'We could not confirm receipt. Please retry.');
      received = true;
      drafts.delete(context.url);
      status.textContent = `Thank you. Your correction was received for review. Reference: ${result.id}.`;
      submit.textContent = 'Received';
    } catch (error) {
      status.textContent = error.name !== 'Error'
        ? 'We could not confirm receipt. Your text is saved in this form. Please retry.' : error.message;
      submit.disabled = false;
      submit.textContent = 'Retry correction';
    } finally {
      pending = false;
      form.querySelectorAll('input, textarea').forEach(field => { field.readOnly = false; });
      dialog.querySelectorAll('[data-correction-close]').forEach(button => { button.disabled = false; });
    }
  });
})();
