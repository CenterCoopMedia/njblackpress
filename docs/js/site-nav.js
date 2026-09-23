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
    const spacing = mobile ? 'inline-block py-2' : 'inline-block py-[14px]';
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

  let menu = document.getElementById('mobile-menu');
  let openButton = document.getElementById('mobile-menu-btn');
  let closeButton = document.getElementById('mobile-menu-close');
  let createdMenu = false;

  if (!menu) {
    const mobileLink = document.querySelector('nav a.md\\:hidden');
    if (mobileLink) {
      mobileLink.outerHTML = `<button id="mobile-menu-btn" class="md:hidden p-[10px] text-linen-100 hover:text-stain" aria-label="Open menu" aria-expanded="false" aria-controls="mobile-menu"><span aria-hidden="true">Menu</span></button>`;
      document.querySelector('nav').insertAdjacentHTML('afterend', `<div id="mobile-menu" class="fixed inset-0 bg-walnut-950 z-[60] transform translate-x-full transition-transform duration-300 md:hidden flex flex-col justify-center items-center"><button id="mobile-menu-close" class="absolute top-[18px] right-[18px] p-[6px] text-linen-300 hover:text-stain" aria-label="Close menu">Close</button><ul class="space-y-6 text-center font-display text-2xl font-medium tracking-wide"></ul></div>`);
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
