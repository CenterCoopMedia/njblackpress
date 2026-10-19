# Correction reports

The shared page footer offers **Submit a correction**. Publication pages, wiki
records, and historical notes record panels also offer the action next to the
record. Portable wiki records link to the same form. The form includes the public
page URL and selected publication ID. Readers can describe a problem, suggest a
change, and add a source link. No account or email address is required.

Reports are unverified evidence. The form explains that report text and source
links may become a public GitHub issue. It does not request private information
or newspaper scans. Failed submissions keep the text. Retrying unchanged fields
uses the same receipt ID; the interface confirms receipt only when the private
store returns that exact ID.

## Routing and review

`docs/js/site-nav.js` loads `docs/js/corrections.js` for the main site and HTML
wiki. The dialog uses the archive palette, fonts, and shared focus rule. A native
modal keeps keyboard focus inside and returns it on close. Pending submissions
cannot be closed or edited until the response arrives or the request times out.

The public relay at `https://blackpress-corrections.amditis.tech/report` accepts
the archive origin, bounded JSON, an empty honeypot, and a valid receipt ID. It
limits requests and forwards only to the fixed private dashboard endpoint. All
credentials remain in Worker secrets. The dashboard validates known archive
routes, derives source files and record IDs, stores the report, and queues Joe's
private Telegram card. The card has **File**, **File + fix**, and **Ignore**.

File creates a marked issue in `CenterCoopMedia/njblackpress`. File + fix first
claims the report, then files the issue and starts the isolated Black Press
runner on landofjawn. It verifies the report, edits owning sources, rebuilds
generated files, and runs focused checks. The trusted host validates original
hashes and the bounded text patch, requires cross-provider review, and opens a
ready PR. Joe controls merging. Archive data retains Cassandra's editorial
review requirement. A receipt or dispatched job does not mean a fix is merged
or published.

## Deployment order

This feature needs coordinated activation; merging site code alone cannot
provision its private dependencies. Obtain the required merge and deployment
approval before activation.

1. Merge and deploy the dashboard's `blackpress` report project and authenticated
   `/api/njpbs/blackpress/report` endpoint. Provision
   `BLACKPRESS_REPORT_INTAKE_SECRET` through the managed credential workflow.
2. Merge and deploy the bot's `bpreport` callback and Black Press runner. Provision
   the runner and its helper with the approved image and review tools, as the bot's
   `docs/blackpress-reports.md` describes. Keep existing CCM and NJ PBS routes.
3. Provision a Cloudflare Access service token scoped to this one intake path.
   Set Worker secrets `BLACKPRESS_REPORT_INTAKE_SECRET`, `ACCESS_CLIENT_ID`, and
   `ACCESS_CLIENT_SECRET`. Do not expose credentials in browser code or broaden
   the dashboard's Access policy. Confirm rate namespace `2026101901` is unused
   in the account before deployment. Deploy `corrections/wrangler.jsonc`.
4. Verify the relay with approved synthetic data and an actual Joe-authorized
   Telegram action before publishing the buttons. Verify one receipt, one issue,
   one isolated job, and a ready PR separately. Never forge a human callback.
5. Merge the site PR after its parent research PR, then verify the ordinary
   public page and record routes. No automatic merge or deployment runs on a
   report or button click.

## Checks and recovery

Run `node --test corrections/worker.test.mjs`. The shared service and bot have
SQLite intake/action and source-patch contract checks. Exercise the form at
desktop and mobile sizes, including keyboard/Escape, validation, failure with
retained text, unchanged retry, and saved receipt. Use synthetic data and fake
providers for local checks; do not send live test mail or messages.

For an uncertain submission, retry unchanged fields. For an uncertain Telegram
action, inspect the private report, marked GitHub issue, and retained job before
retrying. Job files are under `~/.local/state/blackpress-reports/<report-id>/` on
landofjawn. A failed review or missing prerequisite stops the job and retains
its evidence. Continue through an interactive session after inspecting the
recorded stage. Never remove claims or job state to force a second launch.

Rate binding reference: [Cloudflare Rate Limiting API](https://developers.cloudflare.com/workers/runtime-apis/bindings/rate-limit/).
