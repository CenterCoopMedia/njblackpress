/** @type {import('tailwindcss').Config} */
// Design tokens for the site. This is now the single source: the pages load the
// compiled output (docs/css/tailwind.css) and no longer carry an inline
// `tailwind.config`. Rebuild with `npm run build:css` after any token or
// new-class change.
//
// These values were re-synced from the pages' warm-wood palette (issue #48).
// The earlier version of this file predated that redesign (cold greys, an
// international-orange accent, a Fraunces serif) and would have compiled a
// stylesheet that did not match the pages.
module.exports = {
  content: ['./docs/**/*.html', './docs/js/**/*.js'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        // wood - structure, grounds, frames
        walnut: {
          950: '#0b0806',
          900: '#14100b',
          800: '#1e1811',
          700: '#2b2318',
          600: '#3b3122',
        },
        oak: {
          500: '#6b563c',
          400: '#8a7252',
          300: '#a89179',
        },
        // textile - surfaces and text
        linen: {
          50: '#faf7f0',
          100: '#f3eee2',
          200: '#e3dccc',
          300: '#cdc4b1',
        },
        thread: {
          400: '#a89c85',
          500: '#7d7261',
        },
        // stain - the accent
        stain: {
          DEFAULT: '#e2662b',
          light: '#f0854a',
          deep: '#8f3a14',
        },
        // legacy aliases, repointed to warm tokens (issue #48 pass 1)
        ink: {
          950: '#0b0806',
          900: '#14100b',
          800: '#1e1811',
          700: '#2b2318',
          600: '#3b3122',
        },
        paper: {
          50: '#faf7f0',
          100: '#f3eee2',
          200: '#e3dccc',
          300: '#cdc4b1',
        },
        accent: {
          DEFAULT: '#e2662b', // burnt sienna / wood stain
          hover: '#8f3a14',
          light: '#f0854a',
        },
      },
      fontFamily: {
        display: ['Libre Franklin', 'Helvetica Neue', 'Arial', 'sans-serif'],
        sans: ['DM Sans', 'sans-serif'],
        mono: [
          'ui-monospace',
          'SFMono-Regular',
          'Menlo',
          'Monaco',
          'Consolas',
          'monospace',
        ],
      },
      backgroundImage: {
        noise:
          'url(\'data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.9" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E\')',
      },
    },
  },
};
