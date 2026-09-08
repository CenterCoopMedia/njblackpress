import { escapeHtml as esc, publicationYears } from './data.js';

// A labelled, scrollable chart keeps exact date comparison available without WebGL.
export function mountFlat(root, model, onSelect) {
  let matches=null,selected=null;
  const rows=model.publications.slice().sort((a,b)=>(a.yearFounded??9999)-(b.yearFounded??9999)||a.name.localeCompare(b.name));
  root.innerHTML=`<div class="notes-flat-heading"><h2>Compare publication years</h2><p>Horizontal position is year. Each row is one publication. Scroll sideways on a small screen.</p></div><div class="notes-flat-scroll" tabindex="0" aria-label="Publication timeline, scroll to compare dates"><div class="notes-flat-chart"><div class="notes-flat-axis"><span>Publication / year →</span><div>${[1880,1900,1920,1940,1960,1980,2000,2026].map(y=>`<b style="left:${(y-1880)/146*100}%">${y}</b>`).join('')}</div></div>${rows.map(p=>{
    const start=p.yearFounded,end=p.active?2026:p.yearCeased;
    const from=start??end??1880,to=end??start??1880;
    return `<button type="button" class="notes-flat-row" data-publication="${p.id}" aria-pressed="false"><span class="notes-flat-name"><strong>${esc(p.name)}</strong><small>${esc(p.city||'Place not recorded')} · ${esc(publicationYears(p))}</small></span><span class="notes-flat-track"><span class="notes-flat-bar${p.active?' is-active':''}${start==null||end==null?' is-unknown':''}" style="left:${Math.max(0,(from-1880)/146*100)}%;width:${Math.max(.25,(to-from)/146*100)}%;--bar-color:${p.eraColor}">${start==null||end==null?'?':''}</span></span></button>`;
  }).join('')}</div></div>`;
  root.addEventListener('click',e=>{const b=e.target.closest('[data-publication]');if(b)onSelect(Number(b.dataset.publication));});
  function sync(){root.querySelectorAll('[data-publication]').forEach(b=>{const id=Number(b.dataset.publication);b.hidden=matches&&!matches.has(id);b.setAttribute('aria-pressed',String(id===selected));});}
  return {select(id){selected=id;sync();},setFilter(ids){matches=ids;sync();}};
}
