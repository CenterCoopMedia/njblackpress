import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';
import { yearToY, YEAR_MIN, YEAR_MAX } from './geo.js';

const ease = t => t < .5 ? 4*t*t*t : 1-(-2*t+2)**3/2;

// Geography occupies X/Z. The only vertical scale is the recorded year.
export async function createScene(canvas, labelsEl, model, hooks) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'default'});
  renderer.setPixelRatio(Math.min(devicePixelRatio, 1.75));
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.setClearColor('#100e0b');
  const scene = new THREE.Scene();
  scene.fog = new THREE.FogExp2('#100e0b', .0035);
  const camera = new THREE.PerspectiveCamera(38, 1, .1, 400);
  const controls = new OrbitControls(camera, canvas);
  Object.assign(controls, {enableDamping:true,dampingFactor:.09,minPolarAngle:.25,maxPolarAngle:1.45,minDistance:5,maxDistance:160});
  scene.add(new THREE.HemisphereLight('#fff1d9','#1d2730',2.1));
  const light = new THREE.DirectionalLight('#ffe3b1', 3);
  light.position.set(-20,50,20); scene.add(light);
  const resources = [];
  const keep = r => {resources.push(r);return r;};
  const lineMaterial = keep(new THREE.LineBasicMaterial({color:'#716447',transparent:true,opacity:.45}));
  function line(points, material=lineMaterial, parent=scene) {
    const geometry=keep(new THREE.BufferGeometry().setFromPoints(points.map(p=>new THREE.Vector3(...p))));
    const value=new THREE.Line(geometry,material);parent.add(value);return value;
  }
  const mapGroup = new THREE.Group();scene.add(mapGroup);
  let mapMesh=null;
  if (model.outline?.coordinates?.length) {
    const shape = new THREE.Shape(model.outline.coordinates.map(([x,z])=>new THREE.Vector2(x,-z)));
    const geometry=keep(new THREE.ExtrudeGeometry(shape,{depth:.22,bevelEnabled:false}));
    const material=keep(new THREE.MeshStandardMaterial({color:'#55482e',roughness:1}));
    mapMesh=new THREE.Mesh(geometry,material);mapMesh.rotation.x=-Math.PI/2;mapMesh.position.y=-.25;mapGroup.add(mapMesh);
    line(model.outline.coordinates.map(([x,z])=>[x,.01,z]),keep(new THREE.LineBasicMaterial({color:'#a39367',transparent:true,opacity:.75})));
  }
  const floor=new THREE.Mesh(keep(new THREE.PlaneGeometry(180,180)),keep(new THREE.MeshStandardMaterial({color:'#100e0b',roughness:1})));
  floor.rotation.x=-Math.PI/2;floor.position.y=-.28;scene.add(floor);
  const poleX=-18,poleZ=4,top=yearToY(YEAR_MAX);
  line([[poleX,0,poleZ],[poleX,top,poleZ]],keep(new THREE.LineBasicMaterial({color:'#bbae8c'})));
  for(let y=1880;y<=2020;y+=20){
    line([[poleX-.45,yearToY(y),poleZ],[poleX+.45,yearToY(y),poleZ]]);
    line([[poleX,yearToY(y),poleZ],[-13,yearToY(y),poleZ]],keep(new THREE.LineBasicMaterial({color:'#675e48',transparent:true,opacity:.2})));
  }
  // A physical rule and reference edges keep the height scale readable in perspective.
  function rod(a,b,radius=.035,color='#d2c29b') {
    const start=new THREE.Vector3(...a),end=new THREE.Vector3(...b),delta=end.clone().sub(start);
    const mesh=new THREE.Mesh(keep(new THREE.CylinderGeometry(radius,radius,delta.length(),5)),keep(new THREE.MeshBasicMaterial({color})));
    mesh.position.copy(start).lerp(end,.5);mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),delta.normalize());scene.add(mesh);return mesh;
  }
  rod([poleX,0,poleZ],[poleX,top,poleZ],.055);
  for(const y of [1880,1900,1920,1940,1960,1980,2000,2026])rod([poleX-.55,yearToY(y),poleZ],[poleX+.55,yearToY(y),poleZ],.035);
  const reference=keep(new THREE.LineBasicMaterial({color:'#bbae8c',transparent:true,opacity:.42}));
  for(const y of [0,top])line([[poleX,y,poleZ],[poleX,y,-31],[18,y,-31]],reference);
  // Off-map records have a shared tray, separate from the state silhouette.
  const tray=new THREE.Mesh(keep(new THREE.BoxGeometry(11,.1,8)),keep(new THREE.MeshStandardMaterial({color:'#282821',roughness:1})));
  tray.position.set(22,-.04,10);scene.add(tray);
  const north = new THREE.ArrowHelper(new THREE.Vector3(0,0,-1),new THREE.Vector3(16,.1,-21),5,0xbbae8c,.8,.5);scene.add(north);
  const annotations=[];
  function label(text,position,kind,priority=0){
    const el=document.createElement('span');el.className=`notes-map-label ${kind}`;el.textContent=text;labelsEl.append(el);
    const entry={el,position:new THREE.Vector3(...position),priority,kind};annotations.push(entry);return entry;
  }
  for(const year of [1880,1900,1920,1940,1960,1980,2000,2026])label(String(year),[poleX-.9,yearToY(year),poleZ],'notes-year-tick',100);
  label('YEAR',[poleX,top+1.2,poleZ],'notes-axis-title',100);
  label('N',[16,.2,-27],'notes-north',90);
  label('NEW JERSEY',[-3,.1,12],'notes-state-name',1);
  for(const cluster of model.clusters){
    const c=cluster.placedXZ;
    const ring=new THREE.Mesh(keep(new THREE.RingGeometry(cluster.radius+.08,cluster.radius+.13,48)),keep(new THREE.MeshBasicMaterial({color:'#a58d5a',transparent:true,opacity:cluster.shelf?.6:.3,side:THREE.DoubleSide})));
    ring.rotation.x=-Math.PI/2;ring.position.set(c.x,.015,c.z);scene.add(ring);
    if(!cluster.shelf && cluster.trueXZ && cluster.displaced)line([[cluster.trueXZ.x,.025,cluster.trueXZ.z],[c.x,.025,c.z]]);
    const entry=label(cluster.label+(cluster.displaced?'*':''),[c.x,.12,c.z+cluster.radius+.55],'notes-city-label',cluster.shelf?20:cluster.members.length);entry.clusterId=cluster.id;
  }
  const geometry=keep(new THREE.BoxGeometry(.38,1,.38));
  const opacity=new Float32Array(model.publications.length);
  const fades=new Float32Array(model.publications.length*2);
  geometry.setAttribute('postAlpha',new THREE.InstancedBufferAttribute(opacity,1));
  geometry.setAttribute('postFade',new THREE.InstancedBufferAttribute(fades,2));
  const material=keep(new THREE.MeshStandardMaterial({roughness:.65,metalness:.12,emissive:'#46331c',emissiveIntensity:.28,transparent:true,depthWrite:false}));
  material.onBeforeCompile=shader=>{
    shader.vertexShader='attribute float postAlpha; attribute vec2 postFade; varying float vAlpha; varying vec2 vFade; varying float vHeight;\n'+shader.vertexShader;
    shader.vertexShader=shader.vertexShader.replace('#include <begin_vertex>','#include <begin_vertex>\nvAlpha=postAlpha;vFade=postFade;vHeight=position.y+0.5;');
    shader.fragmentShader='varying float vAlpha; varying vec2 vFade; varying float vHeight;\n'+shader.fragmentShader;
    shader.fragmentShader=shader.fragmentShader.replace('#include <dithering_fragment>','gl_FragColor.a *= vAlpha * mix(1.0,smoothstep(0.0,0.65,vHeight),vFade.x) * mix(1.0,1.0-smoothstep(0.35,1.0,vHeight),vFade.y);\n#include <dithering_fragment>');
  };
  const posts=new THREE.InstancedMesh(geometry,material,model.publications.length);posts.name='publication-posts';scene.add(posts);
  const dummy=new THREE.Object3D();
  const caps=new Map();
  for(let i=0;i<model.publications.length;i++){
    const p=model.publications[i];
    dummy.position.set(p.x,(p.startY+p.endY)/2,p.z);dummy.scale.set(1,Math.max(.12,p.endY-p.startY),1);dummy.updateMatrix();posts.setMatrixAt(i,dummy.matrix);posts.setColorAt(i,new THREE.Color(p.eraColor));
    fades[i*2]=p.startKnown?0:1;fades[i*2+1]=p.endKnown||p.active?0:1;
    if(!p.startKnown && !p.endKnown)fades[i*2]=fades[i*2+1]=0;
    if(p.active || !p.startKnown && !p.endKnown){
      const cap=new THREE.Mesh(keep(new THREE.BoxGeometry(.43,.08,.43)),keep(new THREE.MeshBasicMaterial({color:p.active?'#ffaf62':'#a89c85',transparent:true})));
      cap.position.set(p.x,p.active?top:.05,p.z);scene.add(cap);caps.set(p.id,cap);
    }
    // The locator has no time meaning; it connects a raised span to its town.
    if(p.startY>.2)line([[p.x,.03,p.z],[p.x,p.startY,p.z]],keep(new THREE.LineBasicMaterial({color:p.eraColor,transparent:true,opacity:.14})));
  }
  posts.instanceMatrix.needsUpdate=true;
  const datedEvents=model.events.filter(e=>model.byId.has(e.publicationIds?.[0]) && /^\d{4}/.test(String(e.date)));
  const eventMarks=new THREE.InstancedMesh(keep(new THREE.RingGeometry(.2,.27,12)),keep(new THREE.MeshBasicMaterial({color:'#fff0c9',transparent:true,opacity:.55,side:THREE.DoubleSide})),datedEvents.length);
  datedEvents.forEach((event,i)=>{const p=model.byId.get(event.publicationIds[0]);dummy.position.set(p.x,yearToY(Math.max(YEAR_MIN,Math.min(YEAR_MAX,parseInt(event.date,10)))),p.z);dummy.rotation.set(-Math.PI/2,0,0);dummy.scale.set(1,1,1);dummy.updateMatrix();eventMarks.setMatrixAt(i,dummy.matrix);});
  eventMarks.instanceMatrix.needsUpdate=true;scene.add(eventMarks);

  const selectedOutline=new THREE.BoxHelper(undefined,0xffd8a4);selectedOutline.visible=false;scene.add(selectedOutline);
  const selectionBox=new THREE.Mesh(new THREE.BoxGeometry(1,1,1));
  const yearPlane=new THREE.Mesh(keep(new THREE.PlaneGeometry(46,67)),keep(new THREE.MeshBasicMaterial({color:'#eed9a9',transparent:true,opacity:.08,side:THREE.DoubleSide,depthWrite:false})));
  yearPlane.rotation.x=-Math.PI/2;yearPlane.position.set(2,0,0);yearPlane.visible=false;scene.add(yearPlane);
  const yearEdge=new THREE.LineLoop(keep(new THREE.BufferGeometry().setFromPoints([[-21,0,-33],[25,0,-33],[25,0,34],[-21,0,34]].map(v=>new THREE.Vector3(...v)))),keep(new THREE.LineBasicMaterial({color:'#eec17c',transparent:true,opacity:.6})));yearEdge.visible=false;scene.add(yearEdge);
  const route=new THREE.Group();scene.add(route);
  const locationGroup=new THREE.Group();scene.add(locationGroup);
  const locationLabel=label('',[0,0,0],'notes-selected-town',200);locationLabel.enabled=false;
  function locate(p,height){
    for(const child of [...locationGroup.children]){locationGroup.remove(child);child.geometry.dispose();child.material.dispose();}
    locationLabel.enabled=!!p;if(!p)return;
    locationLabel.el.textContent=p.city||'Place not recorded';locationLabel.position.set(p.x+.6,.15,p.z+.6);
    const end=Math.max(.2,height??p.endY);
    const locator=new THREE.Mesh(new THREE.CylinderGeometry(.045,.045,end,5),new THREE.MeshBasicMaterial({color:'#ffce89',transparent:true,opacity:.8}));locator.position.set(p.x+.25,end/2,p.z+.25);locationGroup.add(locator);
  }

  let selected=null,filter=null,story=null,year=null,visible=true,disposed=false,dirty=true,raf=0,tween=null;
  let atHome=true;
  let idle=!hooks.reducedMotion.matches,drag=null,lastTime=0,frames=0,slowFrames=0;
  const raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2();
  const abort=new AbortController();
  const listen=(target,type,fn,opts={})=>target.addEventListener(type,fn,{...opts,signal:abort.signal});
  function request(){dirty=true;if(!raf&&!disposed&&visible)raf=requestAnimationFrame(tick);}
  function updateAlpha(){
    model.publications.forEach((p,i)=>{
      let a=p.unsourced ? .62 : 1;
      if(filter&&!filter.has(p.id))a*=.12;
      if(story&&!story.publicationIds.includes(p.id))a*=.18;
      if(year!==null && (p.yearFounded==null || p.yearFounded>year || !p.active && (p.yearCeased==null||p.yearCeased<year)))a*=.18;
      if(selected!==null)a*=selected===p.id?1.6:.55;
      opacity[i]=Math.min(1,a);if(caps.has(p.id))caps.get(p.id).material.opacity=opacity[i];
    });
    geometry.attributes.postAlpha.needsUpdate=true;request();
  }
  function select(id){
    selected=id;
    if(!story)locate(model.byId.get(id));
    const p=model.byId.get(id);selectedOutline.visible=!!p;
    if(p){selectionBox.position.set(p.x,(p.startY+p.endY)/2,p.z);selectionBox.scale.set(.5,Math.max(.3,p.endY-p.startY+.15),.5);selectionBox.updateMatrixWorld();selectedOutline.setFromObject(selectionBox);}
    updateAlpha();
  }
  function stopIdle(){atHome=false;idle=false;tween=null;hooks.onInteraction?.();request();}
  controls.addEventListener('start',stopIdle);controls.addEventListener('change',request);
  listen(canvas,'pointerdown',e=>{drag={x:e.clientX,y:e.clientY};stopIdle();});
  function pick(e){
    const r=canvas.getBoundingClientRect();mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);raycaster.setFromCamera(mouse,camera);
    const hits=raycaster.intersectObject(posts);return hits.length?model.publications[hits[0].instanceId]:null;
  }
  listen(canvas,'pointermove',e=>{if(e.buttons)return;const p=pick(e);hooks.onHover?.(p,e);canvas.style.cursor=p?'pointer':'grab';});
  listen(canvas,'pointerleave',()=>hooks.onHover?.(null));
  listen(canvas,'click',e=>{if(drag&&Math.hypot(e.clientX-drag.x,e.clientY-drag.y)>8)return;const p=pick(e);if(p)hooks.onSelect(p.id);});
  listen(canvas,'webglcontextlost',e=>{e.preventDefault();hooks.onError?.();});
  listen(hooks.reducedMotion,'change',()=>{if(hooks.reducedMotion.matches){idle=false;if(tween){camera.position.copy(tween.to);controls.target.copy(tween.target);tween=null;}}request();});
  function move(position,target,ms){
    idle=false;
    if(hooks.reducedMotion.matches||!ms){camera.position.copy(position);controls.target.copy(target);tween=null;controls.update();}
    else tween={from:camera.position.clone(),fromTarget:controls.target.clone(),to:position,target,start:performance.now(),ms};
    request();
  }
  function home(ms=900){
    atHome=true;
    const narrow=canvas.clientWidth<650;
    const target=new THREE.Vector3(3,5,-2),direction=new THREE.Vector3(.72,.78,1).normalize();
    const radius=Math.max(narrow?98:79,45/(Math.tan(camera.fov*Math.PI/360)*Math.max(.45,camera.aspect))*.75);
    move(target.clone().addScaledVector(direction,radius),target,ms);
  }
  function frame(ids,ms=900){
    atHome=false;
    const publications=ids.map(id=>model.byId.get(id)).filter(Boolean);if(!publications.length)return home(ms);
    const box=new THREE.Box3();for(const p of publications){box.expandByPoint(new THREE.Vector3(p.x,p.startY,p.z));box.expandByPoint(new THREE.Vector3(p.x,p.endY,p.z));}
    const target=box.getCenter(new THREE.Vector3()),size=box.getSize(new THREE.Vector3());
    const distance=Math.max(9,Math.max(size.y,size.x/Math.max(.4,camera.aspect),size.z)*2.6);
    const direction=camera.position.clone().sub(controls.target).normalize();move(target.clone().addScaledVector(direction,distance),target,ms);
  }
  function clearRoute(){
    for(const child of [...route.children]){route.remove(child);child.geometry?.dispose();child.material?.dispose();}
  }
  function setStory(value,index=0){
    story=value;if(value)atHome=false;clearRoute();updateAlpha();if(!value){locate(null);return;}
    const points=value.stops.slice(0,index+1).map(s=>s.position);
    // A break has no inferred geographical path. Placeless stops stay in the text.
    for(let i=1;i<points.length;i++){
      if(!points[i-1]||!points[i])continue;
      const a=new THREE.Vector3(points[i-1].x,points[i-1].y,points[i-1].z),b=new THREE.Vector3(points[i].x,points[i].y,points[i].z);
      if(a.distanceTo(b)<.01)continue;
      const mid=a.clone().lerp(b,.5);mid.y=Math.max(a.y,b.y)+Math.min(1.5,a.distanceTo(b)/3);
      const curve=new THREE.QuadraticBezierCurve3(a,mid,b);
      const path=new THREE.Mesh(new THREE.TubeGeometry(curve,28,.045,5,false),new THREE.MeshBasicMaterial({color:'#f79351',transparent:true,opacity:.85}));route.add(path);
    }
    const stop=value.stops[index];
    locate(model.byId.get(stop?.publicationId),stop?.position?.y);
    if(stop?.position){
      const p=stop.position,target=new THREE.Vector3(p.x,p.y,p.z);
      const marker=new THREE.Mesh(new THREE.TorusGeometry(.48,.06,6,32),new THREE.MeshBasicMaterial({color:'#ffda9b'}));marker.rotation.x=Math.PI/2;marker.position.copy(target);route.add(marker);
      const direction=camera.position.clone().sub(controls.target).normalize();move(target.clone().addScaledVector(direction,canvas.clientWidth<650?22:16),target,900);
    }
    request();
  }
  function updateLabels(){
    const w=canvas.clientWidth,h=canvas.clientHeight,used=[];
    for(const a of [...annotations].sort((a,b)=>b.priority-a.priority)){
      const v=a.position.clone().project(camera),x=(v.x+1)*w/2,y=(1-v.y)*h/2;
      let show=a.enabled!==false&&v.z<1&&v.z>-1&&x>10&&x<w-10&&y>16&&y<h-18;
      if(story&&a.kind==='notes-city-label'&&!model.clusters.find(c=>c.id===a.clusterId)?.members.some(id=>story.publicationIds.includes(id)))show=false;
      if(a.kind==='notes-year-tick'&&w<500&&!['1880','1920','1960','2000','2026'].includes(a.el.textContent))show=false;
      if(a.kind==='notes-city-label'&&a.priority<3&&camera.position.distanceTo(controls.target)>40)show=false;
      a.el.hidden=false;
      const width=Math.max(45,a.el.offsetWidth||a.el.textContent.length*7),box={x:x-width/2,y:y-8,w:width,h:19};
      if(a.kind!=='notes-year-tick'&&used.some(b=>box.x<b.x+b.w&&box.x+box.w>b.x&&box.y<b.y+b.h&&box.y+box.h>b.y))show=false;
      const legend=document.getElementById('notes-legend'),bounds=canvas.getBoundingClientRect(),lr=legend.getBoundingClientRect();
      if(lr.width&&box.x<lr.right-bounds.left&&box.x+box.w>lr.left-bounds.left&&box.y<lr.bottom-bounds.top&&box.y+box.h>lr.top-bounds.top)show=false;
      a.el.hidden=!show;if(show){a.el.style.transform=`translate(${x}px,${y}px) translate(-50%,-50%)`;used.push(box);}
    }
  }
  function tick(now){
    raf=0;if(disposed||!visible)return;
    const dt=Math.min(.05,(now-lastTime)/1000||0);lastTime=now;
    if(tween){const t=Math.min(1,(now-tween.start)/tween.ms);camera.position.lerpVectors(tween.from,tween.to,ease(t));controls.target.lerpVectors(tween.fromTarget,tween.target,ease(t));if(t===1)tween=null;dirty=true;}
    if(idle){const offset=camera.position.clone().sub(controls.target);offset.applyAxisAngle(new THREE.Vector3(0,1,0),dt*.021);camera.position.copy(controls.target).add(offset);dirty=true;}
    controls.target.x=THREE.MathUtils.clamp(controls.target.x,-30,35);controls.target.z=THREE.MathUtils.clamp(controls.target.z,-38,40);controls.target.y=THREE.MathUtils.clamp(controls.target.y,0,top+5);
    const changed=controls.update();
    if(dirty||changed){const start=performance.now();renderer.render(scene,camera);updateLabels();frames++;if(performance.now()-start>40)slowFrames++;if(frames===3&&slowFrames>=2)renderer.setPixelRatio(1);dirty=false;}
    if((idle||tween||changed)&&!raf)raf=requestAnimationFrame(tick);
  }
  function resize(){const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return;renderer.setSize(r.width,r.height,false);camera.aspect=r.width/r.height;camera.updateProjectionMatrix();if(atHome)home(0);request();}
  const observer=new ResizeObserver(resize);observer.observe(canvas);
  resize();home(0);idle=!hooks.reducedMotion.matches;updateAlpha();
  return {renderer,camera,controls,posts,mapMesh,select,frame,home,setStory,resize,
    setYear(value){year=value;yearPlane.visible=yearEdge.visible=value!==null;if(value!==null){yearPlane.position.y=yearEdge.position.y=yearToY(value);}updateAlpha();},
    setFilter(value){filter=value;updateAlpha();},
    setVisible(value){visible=value;if(!value){if(raf)cancelAnimationFrame(raf);raf=0;}else{resize();request();}},
    get frames(){return frames;},
    dispose(){disposed=true;abort.abort();observer.disconnect();if(raf)cancelAnimationFrame(raf);controls.dispose();clearRoute();locate(null);resources.forEach(r=>r.dispose());selectedOutline.geometry.dispose();selectedOutline.material.dispose();selectionBox.geometry.dispose();selectionBox.material.dispose();renderer.dispose();labelsEl.replaceChildren();}
  };
}
