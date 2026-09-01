// Woven — responsive first-visit dialog behavior.
const FOCUSABLE = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])'
].join(',');

export function createStartDialog({ dialog, trigger, media, beforeOpen, afterClose }) {
  function focusables() {
    return dialog ? Array.from(dialog.querySelectorAll(FOCUSABLE)).filter((el) => !el.hidden) : [];
  }

  function syncModality() {
    if (!dialog) return;
    dialog.setAttribute('aria-modal', String(!dialog.hidden && media.matches));
  }

  function open() {
    if (!dialog || !dialog.hidden) return false;
    beforeOpen?.();
    dialog.hidden = false;
    document.body.classList.add('woven-guide-open');
    syncModality();
    requestAnimationFrame(() => {
      const preferred = dialog.querySelector('[data-guide-action]');
      (preferred || focusables()[0])?.focus({ preventScroll: true });
    });
    return true;
  }

  function close(options = {}) {
    if (!dialog || dialog.hidden) return false;
    dialog.hidden = true;
    document.body.classList.remove('woven-guide-open');
    syncModality();
    afterClose?.(options);
    if (options.restoreFocus !== false) trigger?.focus({ preventScroll: true });
    return true;
  }

  function containFocus(event) {
    if (!dialog || dialog.hidden) return;
    if (event.key === 'Escape') {
      event.preventDefault();
      event.stopImmediatePropagation();
      close();
      return;
    }
    if (event.key !== 'Tab' || !media.matches) return;
    const nodes = focusables();
    if (!nodes.length) return;
    const first = nodes[0];
    const last = nodes[nodes.length - 1];
    const active = document.activeElement;
    if (!dialog.contains(active) || (!event.shiftKey && active === last) || (event.shiftKey && active === first)) {
      event.preventDefault();
      (event.shiftKey ? last : first).focus({ preventScroll: true });
    }
  }

  dialog?.addEventListener('click', (event) => {
    if (event.target === dialog) close();
  });
  document.addEventListener('keydown', containFocus, true);
  media.addEventListener('change', syncModality);
  syncModality();

  return { open, close };
}
