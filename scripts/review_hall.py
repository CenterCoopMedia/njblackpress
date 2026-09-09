"""Chromium smoke checks and visual evidence for the history hall.

Run: python3 scripts/review_hall.py --output /tmp/hall-review
Requires Playwright and its Chromium build. Changes no archive data.

The screenshots are the review material for the vertical slice: the entrance,
a dense decade, a sheet in focus, an open volume with its reader, a page turn,
and the same on a phone.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import re
import threading
import traceback
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='/tmp/hall-review')
args = parser.parse_args()
output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT / 'docs')))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/historical-notes.html'
results = []
errors = []

# The sheet the review looks at by hand: a short-lived 1880s weekly with two
# source records and no cleared clipping, so it exercises the record design.
SHEET_ID = 38
SHEET_NAME = 'New Jersey Trumpet'


def check(name, condition):
    assert condition, name
    results.append(name)


def ready(page, query=''):
    page.goto(base + query, wait_until='networkidle')
    page.wait_for_function(
        'window.__woven?.app.exhibit && document.getElementById("woven-loading").hidden',
        timeout=30000)
    page.wait_for_timeout(700)
    show_stage(page)


def show_stage(page):
    """Put the whole stage in the window, the way the page does when a story opens."""
    page.evaluate("document.getElementById('woven-stage').scrollIntoView({block: 'start'})")
    page.wait_for_timeout(200)


def shot(page, name, full=False):
    page.screenshot(path=str(output / f'{name}.png'), full_page=full, animations='disabled')


def sheet_point(page, publication_id):
    """Where a sheet sits inside the canvas, so the review clicks the exhibit itself.

    The coordinates are relative to the canvas, not to the window: the page can
    still settle between measuring and clicking, and an element-relative click
    survives that.
    """
    return page.evaluate("""(id) => {
      const woven = window.__woven;
      const exhibit = woven.app.exhibit;
      const slot = exhibit.layout.slotByPublicationId.get(id);
      const canvas = document.getElementById('woven-canvas');
      const controls = document.getElementById('woven-hall-controls');
      let best = null;
      // Stand far enough back along the rail that the sheet on its wall is
      // inside the view, the way a visitor walking up to it would see it.
      for (const back of [7, 9, 11, 14]) {
        exhibit.rail.travelTo(Math.max(0.8, slot.z - back), { immediate: true });
        // The camera's world matrices are refreshed on the next draw, so they
        // are brought up to date here before anything is projected through them.
        exhibit.camera.updateMatrixWorld(true);
        exhibit.camera.matrixWorldInverse.copy(exhibit.camera.matrixWorld).invert();
        const point = new woven.THREE.Vector3(slot.x, slot.y, slot.z).project(exhibit.camera);
        const rect = canvas.getBoundingClientRect();
        const bar = controls.hidden ? 0 : controls.getBoundingClientRect().bottom - rect.top;
        best = {
          x: (point.x + 1) / 2 * rect.width,
          y: (1 - point.y) / 2 * rect.height,
          inside: point.x > -0.95 && point.x < 0.95 && point.y > -0.9 && point.y < 0.9
        };
        // The controls sit over the top of the canvas, so a point the visitor
        // could not reach is not a point this review clicks either.
        best.clickable = best.inside && best.y > bar + 8;
        if (best.clickable) break;
      }
      return best;
    }""", publication_id)


def click_sheet(page, point):
    page.locator('#woven-canvas').click(position={'x': point['x'], 'y': point['y']})


try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        context = browser.new_context(viewport={'width': 1440, 'height': 1000},
                                      device_scale_factor=1, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))

        ready(page)
        check('The hall opens by default on a real WebGL scene',
              page.evaluate('window.__woven.app.exhibit.active && !!window.__woven.renderer.getContext()'))
        check('No forced welcome modal', page.locator('#woven-start-card').is_hidden())
        count = page.evaluate('window.__woven.model.counts.total')
        check('Every publication has a native index button',
              page.locator('#woven-publications button').count() == count)
        check('The entrance says what to do',
              'Choose a publication' in page.locator('#hall-hint').inner_text())
        check('The entrance stands in the first section',
              page.evaluate('window.__woven.app.exhibit.rail.section.id') == '1880s')
        check('The canvas is not a duplicate control in the hall',
              page.evaluate('''() => {
                const canvas = document.getElementById('woven-canvas');
                return !canvas.hasAttribute('role') && !canvas.hasAttribute('tabindex')
                  && canvas.getAttribute('aria-hidden') === 'true';
              }'''))
        check('No horizontal page overflow on desktop',
              page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        before = page.evaluate('window.__woven.renderer.info.render.frame')
        page.wait_for_timeout(400)
        after = page.evaluate('window.__woven.renderer.info.render.frame')
        check('Reduced motion settles with no animation left running',
              page.evaluate('window.__woven.app.exhibit.rail.settled') and after - before <= 2)
        shot(page, 'desktop-entrance')

        ready(page, '?decade=1970s')
        check('A decade link opens that section',
              page.evaluate('window.__woven.app.exhibit.rail.section.id') == '1970s')
        shot(page, 'desktop-dense-1970s')

        ready(page)
        point = sheet_point(page, SHEET_ID)
        check('The sheet is on screen before it is clicked', point['clickable'])
        click_sheet(page, point)
        expect(page.locator('#woven-panel-title')).to_have_text(SHEET_NAME)
        check('Selecting a sheet has a shareable link', f'pub={SHEET_ID}' in page.url)
        page.wait_for_timeout(500)
        shot(page, 'desktop-sheet-focus')

        ready(page, '?story=story-001')
        expect(page.locator('#hall-reader')).to_be_visible()
        check('A story link opens its reader', 'Stop 1 of 9' in page.locator('.hall-reader-count').inner_text())
        check('The reader carries the stop text',
              len(page.locator('.hall-reader-body').inner_text()) > 200)
        check('The reader cites its source', page.locator('.hall-reader-sources cite').count() >= 1)
        shot(page, 'desktop-volume-open')
        page.locator('[data-reader="next"]').click()
        page.wait_for_timeout(700)
        check('Next moves to the following stop',
              'Stop 2 of 9' in page.locator('.hall-reader-count').inner_text())
        check('The stop link is replaced, not stacked', 'stop=' in page.url)
        shot(page, 'desktop-volume-next')
        # Only three of this story's nine stops have a cleared clipping, so the
        # review walks the contents until it finds one.
        stops = page.locator('[data-reader="stops"] option').evaluate_all('(items) => items.map((i) => i.value)')
        for key in stops:
            page.locator('[data-reader="stops"]').select_option(key)
            page.wait_for_timeout(350)
            if page.locator('[data-reader="clipping"]').is_visible():
                break
        check('A stop with a cleared clipping offers the inspector',
              page.locator('[data-reader="clipping"]').is_visible())
        shot(page, 'desktop-volume-clipping')
        page.locator('[data-reader="clipping"]').click()
        expect(page.locator('#hall-inspector')).to_be_visible()
        check('The clipping inspector opens with its credit',
              len(page.locator('.hall-inspector-credit').inner_text()) > 10)
        shot(page, 'desktop-clipping')
        page.keyboard.press('Escape')
        check('Escape closes the inspector', page.locator('#hall-inspector').is_hidden())

        ready(page)
        page.locator('[data-woven-view="timeline"]').click()
        page.wait_for_timeout(600)
        check('The flat timeline still opens', not page.evaluate('window.__woven.app.exhibit.active'))
        check('The flat timeline gets the canvas back as a control',
              page.evaluate('document.getElementById("woven-canvas").getAttribute("role")') == 'application')
        shot(page, 'desktop-flat-timeline')
        page.locator('[data-woven-view="hall"]').click()
        page.wait_for_timeout(400)
        check('The hall comes back', page.evaluate('window.__woven.app.exhibit.active'))

        # Forced text still loads no drawing code at all.
        requested = []
        fallback = context.new_page()
        fallback.on('request', lambda request: requested.append(request.url))
        fallback.goto(base + '?nogl=1', wait_until='networkidle')
        expect(fallback.locator('body')).to_have_class(re.compile('twin-primary'))
        check('Forced text fetches no Three.js', not any('/vendor/three-' in url for url in requested))
        check('Forced text keeps every publication', fallback.locator('#woven-twin .t-open').count() == count)
        fallback.close()
        context.close()

        # Full motion, so the opening animation is real: the words must not wait
        # for it.
        motion = browser.new_context(viewport={'width': 1440, 'height': 1000}, device_scale_factor=1)
        moving = motion.new_page()
        moving.on('pageerror', lambda error: errors.append(str(error)))
        ready(moving)
        state = moving.evaluate('''() => {
          window.__woven.app.playStory('story-001');
          return {
            text: document.querySelector('.hall-reader-body').innerText.length,
            visible: !document.getElementById('hall-reader').hidden,
            animating: window.__woven.app.exhibit.volumes.animating
          };
        }''')
        check('The story text is readable before the volume finishes opening',
              state['visible'] and state['text'] > 200 and state['animating'])
        motion.close()

        # Phone, at the size the specification names.
        mobile = browser.new_context(viewport={'width': 375, 'height': 812}, device_scale_factor=1,
                                     is_mobile=True, has_touch=True, reduced_motion='reduce')
        small = mobile.new_page()
        small.on('pageerror', lambda error: errors.append(str(error)))
        ready(small)
        check('375px has no horizontal page overflow',
              small.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('375px keeps the index below the drawing', small.evaluate('''() => {
          const canvas = document.getElementById('woven-canvas').getBoundingClientRect();
          const index = document.getElementById('woven-browser').getBoundingClientRect();
          return index.top >= canvas.bottom - 2;
        }'''))
        shot(small, 'mobile-entrance')
        point = sheet_point(small, SHEET_ID)
        check('375px can reach a sheet in the drawing', point['clickable'])
        click_sheet(small, point)
        expect(small.locator('#woven-panel-title')).to_have_text(SHEET_NAME)
        small.wait_for_timeout(500)
        shot(small, 'mobile-sheet-focus')
        ready(small, '?story=story-001')
        expect(small.locator('#hall-reader')).to_be_visible()
        # The sheet fills the window under the site header, which stays reachable.
        check('375px opens a full height reading sheet', small.evaluate('''() => {
          const reader = document.getElementById('hall-reader').getBoundingClientRect();
          return reader.top <= 84 && reader.bottom >= innerHeight - 2
            && reader.height >= innerHeight * 0.85;
        }'''))
        check('375px keeps Close reachable without scrolling', small.evaluate('''() => {
          const close = document.querySelector('[data-reader="close"]').getBoundingClientRect();
          return close.top >= 0 && close.bottom <= innerHeight;
        }'''))
        shot(small, 'mobile-reading-sheet')
        mobile.close()
        browser.close()
    check('No uncaught browser errors', not errors)
except Exception:
    errors.append(traceback.format_exc())
    try:
        shot(page, 'failure', True)
    except Exception:
        pass
finally:
    server.shutdown()
    (output / 'results.json').write_text(json.dumps({'passed': results, 'errors': errors}, indent=2))
    print(json.dumps({'passed': results, 'errors': errors}, indent=2))
if errors:
    raise SystemExit(1)
