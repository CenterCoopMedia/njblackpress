import { loadModel, publishingAt, publicationYears } from './data.js';
import { mountContent } from './content.js';
import { mountFlat } from './flat.js';

const $=id=>document.getElementById(id);
const reducedMotion=matchMedia('(prefers-reduced-motion: reduce)');
const state={view:'map',mode:'intro',publication:null,story:null,stop:0,year:null};
let model,scene,content,flat,returnFocus=null,canMap=true,applyingURL=false,keyboardIndex=0;
const stage=$('notes-stage'),canvas=$('notes-canvas'),panel=$('notes-panel');
const announce=text=>{$('notes-live').textContent=text;};
const canonicalView=value=>['flat','timeline'].includes(value)?'flat':'map';
function saveURL(){
  if(applyingURL)return;
  const url=new URL(location.href);
  for(const key of ['view','pub','id','story','stop','year','ghost','twin'])url.searchParams.delete(key);
  url.searchParams.set('view',state.view);
  if(state.publication!==null)url.searchParams.set('pub',state.publication);
  if(state.story){url.searchParams.set('story',state.story);url.searchParams.set('stop',state.stop);}
  if(state.year!==null)url.searchParams.set('year',state.year);
  if(url.href!==location.href)history.pushState(null,'',url);
}
function sync(){
  stage.dataset.state=state.mode;stage.dataset.view=state.view;
  document.querySelectorAll('[data-notes-view]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.notesView===state.view)));
  canvas.hidden=state.view!=='map';$('notes-labels').hidden=state.view!=='map';$('notes-flat').hidden=state.view!=='flat';
  scene?.setVisible(state.view==='map'&&!document.hidden);
  $('notes-intro-card').hidden=state.mode!=='intro'||state.view!=='map';
  $('notes-story-bar').hidden=!state.story;
  $('notes-year-enabled').checked=state.year!==null;
  $('notes-year').disabled=state.year===null;
  $('notes-year').value=state.year??2026;
  $('notes-year-label').textContent=state.year??'All years';
  $('notes-year-count').textContent=state.year===null?'Recorded spans, 1880–2026':`${model.publications.filter(p=>publishingAt(p,state.year)).length} publications with recorded spans in ${state.year} · ${model.counts.unrecordedYears} with unrecorded years`;
  scene?.setYear(state.year);
  flat?.select(state.publication);
}
function closeDialogs(){for(const id of ['notes-find','notes-stories'])if($(id).open)$(id).close();}
function openPanel(){panel.hidden=false;stage.classList.add('notes-panel-open');requestAnimationFrame(()=>{scene?.resize();panel.querySelector('h2')?.focus();});}
function closePanel({restore=true}={}){
  panel.hidden=true;stage.classList.remove('notes-panel-open');
  if(restore&&returnFocus?.isConnected)returnFocus.focus();
  requestAnimationFrame(()=>scene?.resize());
}
function publication(id,{write=true,move=true}={}){
  const p=model.byId.get(Number(id));if(!p)return;
  returnFocus=document.activeElement;closeDialogs();state.publication=p.id;state.mode='record';
  content.showPublication(p.id,{backToStory:!!state.story});openPanel();scene?.select(p.id);
  if(move&&!state.story)scene?.frame([p.id]);sync();if(write)saveURL();announce(`${p.name}. ${p.city||'Place not recorded'}. ${publicationYears(p)}.`);
}
function showStop(id,index=0,{write=true}={}){
  const story=model.stories.find(s=>s.id===id);if(!story)return;
  closeDialogs();returnFocus=document.activeElement;
  $('notes-legend').open=false;
  state.story=id;state.stop=Math.max(0,Math.min(story.stops.length-1,Number(index)||0));state.publication=null;state.mode='story';
  content.showStop(story,state.stop);openPanel();
  scene?.select(null);scene?.setStory(story,state.stop);
  $('notes-story-title').textContent=story.title;
  $('notes-stop-label').textContent=story.stops.length?`Stop ${state.stop+1} of ${story.stops.length}`:'Story overview';
  $('btn-prev').disabled=state.stop===0;$('btn-next').textContent=state.stop>=story.stops.length-1?'Next story':'Next';
  sync();if(write)saveURL();announce(`${story.title}. ${$('notes-stop-label').textContent}. ${story.stops[state.stop]?.dateLabel||''}`);
}
function leave({write=true}={}){
  state.mode='explore';state.story=null;state.publication=null;state.stop=0;
  closePanel();scene?.setStory(null);scene?.select(null);scene?.home();sync();if(write)saveURL();
}
function next(){
  const i=model.stories.findIndex(s=>s.id===state.story),story=model.stories[i];if(!story)return;
  if(state.stop<story.stops.length-1)showStop(story.id,state.stop+1);
  else showStop(model.stories[(i+1)%model.stories.length].id,0);
}
function setView(value,{write=true}={}){
  state.view=canMap?canonicalView(value):'flat';if(state.view==='flat'&&state.mode==='intro')state.mode='explore';
  sync();if(write)saveURL();
}
function setYear(value,{write=true}={}){
  state.year=value===null?null:Math.min(2026,Math.max(1880,Math.round(Number(value)||2026)));
  if(state.mode==='intro')state.mode='explore';sync();if(write)saveURL();
}
function filters(){
  const ids=content.renderFind({query:$('notes-search').value,city:$('notes-city').value,evidence:$('notes-evidence').value});
  scene?.setFilter(ids);flat?.setFilter(ids);
  $('btn-find').textContent=ids.size<model.publications.length?`Find a title (${ids.size})`:'Find a title';
}
function showDialog(id){$(id).showModal();if(id==='notes-find')$('notes-search').focus();}
async function applyURL(){
  applyingURL=true;
  const p=new URLSearchParams(location.search);
  leave({write:false});setView(p.get('view'),{write:false});
  setYear(p.has('year')&&Number.isFinite(Number(p.get('year')))?Number(p.get('year')):null,{write:false});
  if(p.get('story'))showStop(p.get('story'),Number(p.get('stop'))||0,{write:false});
  const id=p.get('pub')??p.get('id');if(id!==null&&/^\d+$/.test(id))publication(Number(id),{write:false,move:!state.story});
  if(!p.has('story')&&!p.has('pub')&&!p.has('id')&&!p.has('year')&&state.view==='map'){state.mode='intro';sync();}
  if(p.has('ghost')){$('notes-evidence').value='missing';filters();showDialog('notes-find');}
  if(p.get('nogl')==='1'||p.get('twin')==='1'||location.hash==='#woven-twin'||location.hash==='#notes-twin'){
    $('notes-list-disclosure').open=true;
    if(location.hash==='#woven-twin')history.replaceState(null,'',location.href.replace('#woven-twin','#notes-twin'));
  }
  applyingURL=false;
}
function fallBack(){
  canMap=false;scene?.dispose();scene=null;state.view='flat';document.body.classList.add('notes-no-gl');
  $('notes-renderer-note').hidden=false;
  $('notes-renderer-note').textContent='The time map is unavailable in this browser. The flat timeline, stories, and full list remain available.';
  document.querySelector('[data-notes-view="map"]').disabled=true;
  sync();
}
async function boot(){
  try{model=await loadModel();}catch(error){
    $('notes-loading').textContent='The archive could not load. Reload this page or open the full archive.';
    $('notes-live-assertive').textContent='Publication data is unavailable.';console.error('Historical notes data load failed',error);return;
  }
  content=mountContent(model,{onPublication:id=>publication(id),onStory:id=>showStop(id),onStop:(id,index)=>showStop(id,index)});
  flat=mountFlat($('notes-flat'),model,id=>publication(id,{move:false}));
  if(model.mapAvailable!==false && new URLSearchParams(location.search).get('nogl')!=='1'){
    try{
      const {createScene}=await import('./scene.js');
      scene=await createScene(canvas,$('notes-labels'),model,{reducedMotion,
        onSelect:id=>publication(id),
        onHover:(p,e)=>{const tip=$('notes-tooltip');tip.hidden=!p;if(p){tip.textContent=`${p.name} · ${p.city||'Place not recorded'} · ${publicationYears(p)}`;const r=stage.getBoundingClientRect();tip.style.left=`${Math.max(8,Math.min(e.clientX-r.left+12,stage.clientWidth-270))}px`;tip.style.top=`${Math.max(8,e.clientY-r.top-50)}px`; }},
        onInteraction:()=>{$('notes-tooltip').hidden=true;},onError:fallBack});
    }catch(error){console.warn('Time map unavailable',error);fallBack();}
  }else fallBack();
  $('notes-loading').hidden=true;
  $('notes-legend').addEventListener('toggle',()=>scene?.resize());
  $('btn-look').addEventListener('click',()=>{state.mode='explore';scene?.home(0);sync();canvas.focus();});
  $('btn-reset').addEventListener('click',()=>leave());
  $('btn-stories').addEventListener('click',()=>showDialog('notes-stories'));
  document.querySelectorAll('[data-open-stories]').forEach(b=>b.addEventListener('click',()=>showDialog('notes-stories')));
  $('btn-find').addEventListener('click',()=>showDialog('notes-find'));
  $('btn-close-stories').addEventListener('click',()=>$('notes-stories').close());
  $('btn-close-find').addEventListener('click',()=>$('notes-find').close());
  document.querySelectorAll('[data-notes-view]').forEach(b=>b.addEventListener('click',()=>setView(b.dataset.notesView)));
  $('btn-close-panel').addEventListener('click',()=>{if(state.story){if(state.publication!==null){state.publication=null;showStop(state.story,state.stop);}else leave();}else{state.publication=null;state.mode='explore';closePanel();scene?.select(null);sync();saveURL();}});
  $('btn-prev').addEventListener('click',()=>showStop(state.story,state.stop-1));$('btn-next').addEventListener('click',next);$('btn-leave').addEventListener('click',()=>leave());
  $('notes-year-enabled').addEventListener('change',()=>setYear($('notes-year-enabled').checked?Number($('notes-year').value):null));
  $('notes-year').addEventListener('input',()=>setYear(Number($('notes-year').value),{write:false}));
  $('notes-year').addEventListener('change',saveURL);
  for(const id of ['notes-search','notes-city','notes-evidence'])$(id).addEventListener(id==='notes-search'?'input':'change',filters);
  $('notes-clear').addEventListener('click',()=>{$('notes-search').value='';$('notes-city').value='';$('notes-evidence').value='all';filters();});
  const ordered=model.publications.slice().sort((a,b)=>b.z-a.z||(a.yearFounded??9999)-(b.yearFounded??9999)||a.id-b.id);
  canvas.addEventListener('keydown',e=>{
    if(e.altKey||e.ctrlKey||e.metaKey)return;
    if(state.story&&(e.key==='ArrowLeft'||e.key==='ArrowRight')){e.preventDefault();e.key==='ArrowLeft'?showStop(state.story,state.stop-1):next();return;}
    if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight','Home','End'].includes(e.key)){
      e.preventDefault();keyboardIndex=e.key==='Home'?0:e.key==='End'?ordered.length-1:(keyboardIndex+(['ArrowUp','ArrowLeft'].includes(e.key)?-1:1)+ordered.length)%ordered.length;
      const p=ordered[keyboardIndex];scene?.select(p.id);scene?.frame([p.id],0);announce(`${p.name}. ${p.city}. ${publicationYears(p)}. Press Enter to open.`);
    }else if(e.key==='Enter'){e.preventDefault();publication(ordered[keyboardIndex].id);}else if(e.key.toLowerCase()==='s'){e.preventDefault();showDialog('notes-stories');}else if(e.key.toLowerCase()==='y'){e.preventDefault();if(state.year===null)setYear(2026);$('notes-year').focus();}
  });
  document.addEventListener('keydown',e=>{if(e.key==='Escape'&&!$('notes-find').open&&!$('notes-stories').open&&!panel.hidden){e.preventDefault();if(state.story)leave();else $('btn-close-panel').click();}});
  document.addEventListener('visibilitychange',()=>scene?.setVisible(!document.hidden&&state.view==='map'));
  const revealList=()=>{$('notes-list-disclosure').open=true;};
  document.querySelectorAll('a[href="#notes-twin"]').forEach(a=>a.addEventListener('click',revealList));
  window.addEventListener('hashchange',()=>{if(['#notes-twin','#woven-twin'].includes(location.hash))revealList();});
  window.addEventListener('popstate',applyURL);
  window.__notes={model,state,get scene(){return scene;},publication,showStop,setYear,setView,leave};
  await applyURL();
}
boot();
