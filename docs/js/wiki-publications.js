(() => {
  const table = document.getElementById('publication-index');
  const body = table?.querySelector('tbody');
  const headers = Array.from(table?.querySelectorAll('[data-sort-key]') || []);
  const status = document.getElementById('publication-sort-status');

  if (!body || headers.length === 0) return;

  const keys = ['publication', 'city', 'years', 'status'];
  const collator = new Intl.Collator('en', { numeric: true, sensitivity: 'base' });
  let activeKey = 'publication';
  let direction = 'ascending';

  const valueFor = (row, key) => {
    const cell = row.cells[keys.indexOf(key)];
    return cell?.dataset.sortValue || '';
  };

  const updateHeaders = () => {
    headers.forEach((button) => {
      const heading = button.closest('th');
      const active = button.dataset.sortKey === activeKey;
      if (active) heading.setAttribute('aria-sort', direction);
      else heading.removeAttribute('aria-sort');
      const arrow = button.querySelector('[aria-hidden="true"]');
      arrow.textContent = active ? (direction === 'ascending' ? '↑' : '↓') : '↕';
      arrow.classList.toggle('text-accent', active);
      arrow.classList.toggle('opacity-40', !active);
    });
  };

  const sortRows = (key) => {
    direction = key === activeKey && direction === 'ascending' ? 'descending' : 'ascending';
    activeKey = key;
    const factor = direction === 'ascending' ? 1 : -1;
    const rows = Array.from(body.rows);

    rows.sort((a, b) => {
      const aValue = valueFor(a, key);
      const bValue = valueFor(b, key);
      if (key === 'city') {
        if (aValue === 'Unknown' && bValue !== 'Unknown') return 1;
        if (bValue === 'Unknown' && aValue !== 'Unknown') return -1;
      }
      const primary = collator.compare(aValue, bValue);
      if (primary !== 0) return primary * factor;
      return collator.compare(valueFor(a, 'publication'), valueFor(b, 'publication'));
    });
    body.append(...rows);
    updateHeaders();
    if (status) status.textContent = `Sorted by ${key}, ${direction}.`;
  };

  headers.forEach((button) => {
    button.addEventListener('click', () => sortRows(button.dataset.sortKey));
  });
})();
