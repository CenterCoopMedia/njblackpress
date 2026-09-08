// Development only. GitHub Pages still serves docs/ directly, without a JS build.
import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';
import { readFile } from 'node:fs/promises';
import { resolve, sep } from 'node:path';

const vendor = resolve(fileURLToPath(new URL('./docs/vendor/', import.meta.url)));

export default defineConfig({
  root: 'docs',
  server: { host: '0.0.0.0', allowedHosts: ['terminal.local'] },
  plugins: [{
    name: 'preserve-vendor-integrity',
    configureServer(server) {
      // The import map verifies these exact bytes. Development transforms would
      // invalidate that checksum, so vendored modules must be served unchanged.
      server.middlewares.use(async (request, response, next) => {
        try {
          const path = new URL(request.url, 'http://localhost').pathname;
          if (!path.startsWith('/vendor/')) return next();
          const file = resolve(vendor, decodeURIComponent(path.slice('/vendor/'.length)));
          if (!file.startsWith(vendor + sep)) return next();
          const bytes = await readFile(file);
          response.setHeader('Content-Type', 'text/javascript');
          response.end(bytes);
        } catch { next(); }
      });
    }
  }],
  resolve: {
    alias: [
      { find: /^three$/, replacement: fileURLToPath(new URL('./docs/vendor/three-0.171.0/three.module.min.js', import.meta.url)) },
      { find: 'three/addons', replacement: fileURLToPath(new URL('./docs/vendor/three-0.171.0/addons', import.meta.url)) }
    ]
  }
});
