# Vendored three.js r171

Pinned by `data/research/design/WOVEN_SPEC.md` section 1.2. These files are served
same-origin. Nothing in Woven fetches a CDN at runtime.

| File | Source URL | Bytes | sha384 |
|---|---|---|---|
| `three.module.min.js` | https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.module.min.js | 339149 | `sha384-nMDT6MQtyrbFXD89PryBsu+fdRtrBVn1ot0qcqb1ddUN9CM9WlcU0mqv0ZW7zgXD` |
| `three.core.min.js` | https://cdn.jsdelivr.net/npm/three@0.171.0/build/three.core.min.js | 365910 | `sha384-o7aLe+NzQLKhqUTx3AWnCnAsurwCaoG+cVd4flrG/xpmV7l6qzNtiGIw7qvdkPMH` |
| `addons/controls/OrbitControls.js` | https://cdn.jsdelivr.net/npm/three@0.171.0/examples/jsm/controls/OrbitControls.js | 32430 | `sha384-TNVkFtMGVpSMUMt5yuFmRsmuqa6tWGR1yzL5V8fTeDkKKDehIy+o+TV5P+FnvlLd` |

Downloaded 2026-08-19.

Regenerate:

```bash
shasum -b -a 384 docs/vendor/three-0.171.0/three.module.min.js | xxd -r -p | base64
```

The hash for `three.module.min.js` is repeated in the `importmap` `integrity` block in
`docs/woven.html`. If the two disagree, Chrome refuses to load the module. That is
intended.

`three.module.min.js` in r171 re-exports from `three.core.min.js`, so both build
files are required. Only these three files are vendored. Do not add addons that
Woven does not import.
