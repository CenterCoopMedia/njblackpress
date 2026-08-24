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
    { label: 'Woven', path: 'woven.html' },
    { label: 'About', path: 'index.html#about' }
  ];
  const stain = location.pathname.endsWith('/woven.html');
  const accent = stain ? 'stain' : 'accent';
  const activePath = location.pathname.split('/').pop() || 'index.html';

  const isActive = link => {
    if (link.path === 'wiki/index.html') return location.pathname.includes('/wiki/');
    return link.path.split('#')[0] === activePath && !link.path.includes('#');
  };

  const markup = (mobile = false) => links.map(link => {
    const active = isActive(link);
    const spacing = mobile ? 'inline-block py-2' : 'inline-block py-[14px]';
    const color = active ? `text-${accent}` : `hover:text-${accent} transition-colors`;
    return `<li><a href="${url(link.path)}" class="${spacing} ${color}"${active ? ' aria-current="page"' : ''}>${link.label}</a></li>`;
  }).join('');

  const desktop = document.querySelector('nav ul.hidden');
  if (desktop) desktop.innerHTML = markup();

  const logo = document.querySelector('nav a:has(img)');
  if (logo) logo.href = url('index.html');

  let menu = document.getElementById('mobile-menu');
  let openButton = document.getElementById('mobile-menu-btn');
  let closeButton = document.getElementById('mobile-menu-close');
  let createdMenu = false;

  if (!menu) {
    const mobileLink = document.querySelector('nav a.md\\:hidden');
    if (mobileLink) {
      mobileLink.outerHTML = `<button id="mobile-menu-btn" class="md:hidden p-[10px] text-paper-100 hover:text-${accent}" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu"><span aria-hidden="true">Menu</span></button>`;
      document.querySelector('nav').insertAdjacentHTML('afterend', `<div id="mobile-menu" class="fixed inset-0 bg-ink-950 z-[60] transform translate-x-full transition-transform duration-300 md:hidden flex flex-col justify-center items-center"><button id="mobile-menu-close" class="absolute top-[18px] right-[18px] p-[6px] text-paper-300 hover:text-${accent}" aria-label="Close menu">Close</button><ul class="space-y-6 text-center font-display text-2xl font-medium tracking-wide"></ul></div>`);
      menu = document.getElementById('mobile-menu');
      openButton = document.getElementById('mobile-menu-btn');
      closeButton = document.getElementById('mobile-menu-close');
      createdMenu = true;
    }
  }

  const mobileList = menu?.querySelector('ul');
  if (mobileList) mobileList.innerHTML = markup(true);
  if (!menu || !openButton || !closeButton) return;

  const setOpen = open => {
    menu.classList.toggle('translate-x-full', !open);
    document.body.classList.toggle('overflow-hidden', open);
    openButton.setAttribute('aria-expanded', String(open));
  };
  if (createdMenu) {
    openButton.addEventListener('click', () => setOpen(menu.classList.contains('translate-x-full')));
    closeButton.addEventListener('click', () => setOpen(false));
  }
  mobileList?.querySelectorAll('a').forEach(link => link.addEventListener('click', () => setOpen(false)));
})();
