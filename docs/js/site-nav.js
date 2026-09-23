(() => {
  const script = document.currentScript;
  if (!script) return;
  const root = new URL('../', script.src);
  const url = path => new URL(path, root).href;
  const links = [
    { label: 'Home', path: 'index.html' },
    { label: 'Timeline', path: 'index.html#timeline' },
    { label: 'Archive', path: 'archive.html' },
    { label: 'Stories', path: 'story.html' },
    { label: 'Eras', path: 'era.html' },
    { label: 'Map', path: 'map.html' },
    { label: 'Wiki', path: 'wiki/index.html' },
    { label: 'Historical notes', path: 'historical-notes.html' },
    { label: 'About', path: 'index.html#about' }
  ];
  const activePath = location.pathname.split('/').pop() || 'index.html';

  const isActive = link => {
    const inWiki = location.pathname.includes('/wiki/');
    if (link.path === 'wiki/index.html') return inWiki;
    if (inWiki) return false;
    return link.path.split('#')[0] === activePath && !link.path.includes('#');
  };

  const markup = (mobile = false) => links.map(link => {
    const active = isActive(link);
    const spacing = mobile ? 'inline-flex items-center min-h-[44px] px-4' : 'inline-block py-[14px]';
    const color = active ? 'text-stain' : 'hover:text-stain transition-colors';
    return `<li><a href="${url(link.path)}" class="${spacing} ${color}"${active ? ' aria-current="page"' : ''}>${link.label}</a></li>`;
  }).join('');

  const desktop = document.querySelector('nav ul.hidden');
  if (desktop) desktop.innerHTML = markup();

  const logo = document.querySelector('nav a:has(img)');
  if (logo) logo.href = url('index.html');

  // One footer for every page. A page opts in with <footer data-site-footer>.
  const footer = document.querySelector('footer[data-site-footer]');
  if (footer) {
    const external = 'target="_blank" rel="noopener noreferrer"';
    const linkClass = 'inline-flex items-center min-h-[44px] px-3 hover:text-stain transition-colors';
    footer.className = 'bg-walnut-950 border-t border-walnut-600 py-10 px-4 md:px-8';
    footer.innerHTML = `<div class="max-w-[1400px] mx-auto flex flex-col md:flex-row justify-between items-center gap-6 text-xs font-mono text-linen-300 uppercase tracking-wider">
      <div class="flex flex-col sm:flex-row items-center gap-4 text-center sm:text-left">
        <a href="https://centerforcooperativemedia.org" ${external} class="inline-flex min-h-[44px] items-center">
          <img src="${url('ccm-banner.png')}" alt="Center for Cooperative Media" class="h-5 w-auto opacity-80 hover:opacity-100 transition-opacity">
        </a>
        <p>&copy; ${new Date().getFullYear()} Center for Cooperative Media, Montclair State University</p>
      </div>
      <ul class="flex flex-wrap justify-center gap-x-2">
        <li><a href="${url('index.html#about')}" class="${linkClass}">About</a></li>
        <li><a href="mailto:info@centerforcooperativemedia.org" class="${linkClass}">Contact</a></li>
        <li><a href="https://github.com/CenterCoopMedia/njblackpress" ${external} class="${linkClass}">Source on GitHub</a></li>
      </ul>
    </div>`;
  }

  // One mobile menu for every page: a modal dialog built here, so each page
  // only supplies a #mobile-menu-btn button or an a.md:hidden placeholder.
  const icon = path => `<svg class="w-6 h-6" aria-hidden="true" focusable="false" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${path}"/></svg>`;
  let openButton = document.getElementById('mobile-menu-btn');
  if (!openButton) {
    const placeholder = document.querySelector('nav a.md\\:hidden');
    if (!placeholder) return;
    placeholder.outerHTML = `<button id="mobile-menu-btn" class="md:hidden inline-flex items-center justify-center w-11 h-11 text-linen-100 hover:text-stain">${icon('M4 6h16M4 12h16M4 18h16')}</button>`;
    openButton = document.getElementById('mobile-menu-btn');
  }
  openButton.type = 'button';
  openButton.setAttribute('aria-label', 'Open menu');
  openButton.setAttribute('aria-expanded', 'false');
  openButton.setAttribute('aria-controls', 'mobile-menu');

  document.getElementById('mobile-menu')?.remove();
  document.body.insertAdjacentHTML('beforeend', `<div id="mobile-menu" role="dialog" aria-modal="true" aria-label="Site menu" hidden class="fixed inset-0 z-[60] bg-walnut-950 overflow-y-auto overscroll-contain md:hidden">
    <button id="mobile-menu-close" type="button" class="fixed top-[18px] right-[18px] inline-flex items-center justify-center w-11 h-11 text-linen-300 hover:text-stain" aria-label="Close menu">${icon('M6 18L18 6M6 6l12 12')}</button>
    <ul class="min-h-full flex flex-col items-center justify-center gap-1 py-20 text-center font-display text-2xl font-medium tracking-wide">${markup(true)}</ul>
  </div>`);
  const menu = document.getElementById('mobile-menu');
  const closeButton = document.getElementById('mobile-menu-close');
  const focusable = () => [...menu.querySelectorAll('a[href], button')];

  const setOpen = (open, restoreFocus = true) => {
    menu.hidden = !open;
    document.body.classList.toggle('overflow-hidden', open);
    openButton.setAttribute('aria-expanded', String(open));
    if (open) closeButton.focus();
    else if (restoreFocus) openButton.focus();
  };

  openButton.addEventListener('click', () => setOpen(true));
  closeButton.addEventListener('click', () => setOpen(false));
  menu.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setOpen(false, false)));
  menu.addEventListener('keydown', event => {
    if (event.key === 'Escape') {
      event.preventDefault();
      setOpen(false);
      return;
    }
    if (event.key !== 'Tab') return;
    const items = focusable();
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
  // The menu is hidden at desktop widths; do not leave the page scroll-locked.
  // Focus moves to the site logo, which stays visible at every width, so a
  // keyboard user keeps their place. The md:hidden rule can hide the menu
  // before this event runs, and the browser then drops focus to the body.
  window.matchMedia('(min-width: 768px)').addEventListener('change', event => {
    if (!event.matches || menu.hidden) return;
    const hadFocus = document.activeElement === document.body || menu.contains(document.activeElement);
    setOpen(false, false);
    if (hadFocus) (logo || document.querySelector('nav a[href]'))?.focus();
  });
})();
