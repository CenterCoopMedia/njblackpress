/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ['./docs/**/*.html', './docs/js/**/*.js'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        ink: {
          950: '#050505',
          900: '#0a0a0a',
          800: '#121212',
          700: '#1a1a1a',
          600: '#262626',
        },
        paper: {
          50: '#faf9f6',
          100: '#f4f1ea',
          200: '#e5e2db',
          300: '#d1cdc5',
        },
        accent: {
          DEFAULT: '#ff4d00', // International Orange / Vermilion
          hover: '#cc3d00',
          light: '#ff7a40',
        },
      },
      fontFamily: {
        serif: ['Fraunces', 'serif'],
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
          'url(\'data:image/svg+xml,%3Csvg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg"%3E%3Cfilter id="noiseFilter"%3E%3CfeTurbulence type="fractalNoise" baseFrequency="0.65" numOctaves="3" stitchTiles="stitch"/%3E%3C/filter%3E%3Crect width="100%25" height="100%25" filter="url(%23noiseFilter)" opacity="0.05"/%3E%3C/svg%3E\')',
      },
    },
  },
};
