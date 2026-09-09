# lessons

- When generating docs from grouped data, validate slug collisions instead of assuming labels map one-to-one to filenames.
- Keep generated output reproducible by accepting an explicit generation date and preserving existing timestamps by default.
- Escape YAML and markdown table content with reusable helpers before writing generated pages.

## History hall session, September 2026

- Ask about naming before writing a spec. The first draft called the view
  "the hall" and kept "woven" internals as out of scope; Joe's rule was that
  nothing visitor facing may say woven. Put the public name and the
  allowlist of internal names in section 2 of every interface spec.
- When a reviewer rewrites a spec from an older draft, do not merge line by
  line. Keep the reviewer's text, then add one addendum with the decisions
  and the repository facts that take precedence. Build agents read one file.
- Check the Playwright pip version against the Chromium build under
  /opt/pw-browsers before running a browser review. Build 1194 needs
  playwright 1.56.
- Three.js instance colour is ignored unless the material has vertexColors
  and the geometry has a colour attribute. An InstancedMesh accent that
  renders white is this bug.
- Tailwind scans docs/js for class candidates. A local identifier such as
  ordinal, outline, or contents adds a rule to tailwind.css. Run build:css
  after every JavaScript change and rename the identifier if the CSS moves.
- Review screenshots before showing them to Joe. The first slice had a flat
  sheet where a bound volume was specified; one more agent round fixed it
  and the review with Joe took one question instead of three.
