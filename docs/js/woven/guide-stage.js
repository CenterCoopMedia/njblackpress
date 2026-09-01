// Woven — coordinate guidance with the existing stage overlays and measurements.
export function createStageCoordinator({ tourbar, toursButton, moreTools, searchCount }) {
  function closeOverlays() {
    const interactiveOpen = ['woven-panel', 'woven-card', 'woven-ghostnames']
      .some((id) => document.getElementById(id) && !document.getElementById(id).hidden) ||
      (tourbar && !tourbar.hidden);
    if (interactiveOpen) window.njbpWoven?.exit?.();
    for (const id of ['woven-help-card', 'woven-tourpicker', 'woven-ghostcard']) {
      const overlay = document.getElementById(id);
      if (overlay) overlay.hidden = true;
    }
    toursButton?.setAttribute('aria-expanded', 'false');
  }

  let refreshFrame = 0;
  function refreshChrome() {
    if (refreshFrame) return;
    refreshFrame = requestAnimationFrame(() => {
      refreshFrame = 0;
      const app = window.__woven?.app;
      if (app?.labels?.update) app.labels.update();
      else app?.measureChrome?.();
      if (app) app.needsRender = true;
    });
  }

  if (searchCount) {
    const observer = new MutationObserver(refreshChrome);
    observer.observe(searchCount, { childList: true, characterData: true, subtree: true });
  }

  function prepareSearch() {
    closeOverlays();
    if (moreTools) moreTools.open = false;
  }

  return { closeOverlays, prepareSearch, refreshChrome };
}
