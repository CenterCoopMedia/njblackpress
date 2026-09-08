// Canvas 2D keeps the same camera, data, picking, and controls without WebGL.
// Only drawing differs. The full document remains available with ?nogl=1.
import { YEAR_MIN, YEAR_MAX, x } from './layout.js';

export function createFlatRenderer(canvas, model) {
  const ctx = canvas.getContext('2d', { alpha: false });
  if (!ctx) throw new Error('No canvas renderer available');
  let ratio = 1;
  let width = 1;
  let height = 1;
  let background = '#0b121c';
  function resize() { canvas.width = Math.round(width * ratio); canvas.height = Math.round(height * ratio); }
  return {
    domElement: canvas,
    dispose() {},
    capabilities: { getMaxAnisotropy: () => 1 },
    setPixelRatio(value) { ratio = value; resize(); },
    setSize(w, h) { width = w; height = h; resize(); },
    setClearColor(value) { background = `#${value.toString(16).padStart(6, '0')}`; },
    render(scene, camera) {
      const uniforms = scene.getObjectByName('weft-solid').material.uniforms;
      const ghostUniforms = scene.getObjectByName('weft-ghost').material.uniforms;
      const states = uniforms.uState.value.image.data;
      const scale = height / (2 * Math.tan(camera.fov * Math.PI / 360) * camera.position.z);
      const px = (value) => width / 2 + (value - camera.position.x) * scale;
      const py = (value) => height / 2 - (value - camera.position.y) * scale;
      ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
      ctx.globalAlpha = 1;
      ctx.fillStyle = background;
      ctx.fillRect(0, 0, width, height);
      ctx.lineWidth = 1;
      ctx.strokeStyle = '#3b3122';
      ctx.setLineDash([]);
      ctx.beginPath();
      for (let year = YEAR_MIN; year <= YEAR_MAX; year += 10) {
        ctx.moveTo(px(x(year)), py(0.9));
        ctx.lineTo(px(x(year)), py(model.layout.bounds.minY - 0.5));
      }
      for (const band of model.bands) {
        if (!band.count) continue;
        const y = py(band.top - band.height - 0.45);
        ctx.moveTo(px(0), y);
        ctx.lineTo(px(x(YEAR_MAX)), y);
      }
      ctx.stroke();
      const reveal = uniforms.uWeaveProgress.value * x(YEAR_MAX);
      for (const t of model.order) {
        if (py(t.y) < -20 || py(t.y) > height + 20) continue;
        const hi = states[t.threadIndex * 4] / 255;
        const dim = states[t.threadIndex * 4 + 1] / 255;
        const emphasis = states[t.threadIndex * 4 + 2] / 255;
        ctx.globalAlpha = (t.ghost ? Math.min(1, ghostUniforms.uGhostAlpha.value + emphasis * 0.34) : 1) * (1 - dim * 0.82);
        ctx.strokeStyle = hi > 0.6 ? '#ffffff' : t.dye;
        ctx.fillStyle = ctx.strokeStyle;
        ctx.lineWidth = Math.max(t.width, uniforms.uMinHalfW.value * 2) * scale;
        ctx.lineCap = 'round';
        ctx.setLineDash(t.endState === 'unrecorded' ? [Math.max(2, scale * 0.24), Math.max(2, scale * 0.26)] : []);
        const stroke = (start, end, offset = 0) => {
          const edge = reveal >= x(YEAR_MAX) ? 79 : reveal;
          if (start > edge || end < start) return;
          end = Math.min(end, edge);
          ctx.beginPath();
          const steps = Math.max(2, Math.ceil((end - start) * 3));
          for (let i = 0; i <= steps; i++) {
            const part = i / steps;
            let wave = 0;
            const age = uniforms.uPluckAge.value;
            if (uniforms.uPluckAmp.value && age < 1.25 && uniforms.uPluckIdx.value.x === t.threadIndex) {
              wave = Math.exp(-age * 2.6) * Math.sin(part * Math.PI) * Math.sin(part * 18.85 - age * 27) * 0.20 * uniforms.uPluckScale.value;
            }
            const sx = px(start + (end - start) * part);
            const sy = py(t.y + wave + offset * part);
            if (i === 0) ctx.moveTo(sx, sy); else ctx.lineTo(sx, sy);
          }
          ctx.stroke();
        };
        if (t.unknownFounding) {
          for (let i = 0; i < 5; i++) stroke(4 + i * 14, 7.5 + i * 14);
        } else {
          stroke(t.x0, Math.max(t.x1, t.x0 + 0.18));
          if (t.x0 <= reveal) {
            ctx.beginPath();
            ctx.arc(px(t.x0), py(t.y), Math.max(1.3, 0.1 * scale), 0, Math.PI * 2);
            ctx.fill();
          }
        }
        if (t.endState === 'still') {
          stroke(x(YEAR_MAX), 74.5);
          for (const offset of [-0.06, 0, 0.06]) stroke(74.5, 78.5, offset);
        }
      }
      ctx.setLineDash([]);
      ctx.lineWidth = Math.max(1, scale * 0.038);
      for (const k of model.knots) {
        if (k.x > reveal) continue;
        const dim = k.thread ? states[k.thread.threadIndex * 4 + 1] / 255 : 0;
        ctx.globalAlpha = 1 - dim * 0.82;
        ctx.strokeStyle = k.confidence === 'medium' ? '#b8c6d6' : '#ff946d';
        ctx.beginPath();
        ctx.arc(px(k.x), py(k.y), Math.max(1.5, 0.085 * scale), 0, k.confidence === 'medium' ? 4.6 : Math.PI * 2);
        ctx.stroke();
      }
      ctx.globalAlpha = 1;
      // Evidence scans use the same Three.js planes as the WebGL renderer.
      // Paint their decoded images without tinting or filtering the document.
      for (const child of scene.children) {
        const source = child.material?.uniforms?.uMap?.value?.image;
        const loading = child.isMesh && child.geometry.type === 'PlaneGeometry' && child.material?.isMeshBasicMaterial;
        if ((!source && !loading) || !child.visible) continue;
        const depthScale = height / (2 * Math.tan(camera.fov * Math.PI / 360) * (camera.position.z - child.position.z));
        const w = child.geometry.parameters.width * child.scale.x * depthScale;
        const h = child.geometry.parameters.height * child.scale.y * depthScale;
        const left = width / 2 + (child.position.x - camera.position.x) * depthScale - w / 2;
        const top = height / 2 - (child.position.y - camera.position.y) * depthScale - h / 2;
        if (loading) {
          ctx.globalAlpha = child.material.opacity;
          ctx.fillStyle = `#${child.material.color.getHexString()}`;
          ctx.fillRect(left, top, w, h);
          ctx.globalAlpha = 0.7;
          ctx.strokeStyle = '#e2662b';
          ctx.lineWidth = 1;
          ctx.strokeRect(left, top, w, h);
          ctx.globalAlpha = 1;
        } else ctx.drawImage(source, left, top, w, h);
      }
    }
  };
}
