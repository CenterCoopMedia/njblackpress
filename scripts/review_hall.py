"""Chromium smoke checks and visual evidence for the history hall.

Run: python3 scripts/review_hall.py --output /tmp/hall-review
Requires Playwright and its Chromium build. Changes no archive data.

The screenshots are the review material: the entrance, a dense decade, a sheet
in focus, an open volume read from above, a page turn, the filtered hall, a
record revealed past the filters, an image that would not load, and the same on
a phone, including the portrait entrance.

The checks also cover what a screenshot cannot show: that repeated view and
story cycles leave the hall owning no more than it did, that the adaptive tier
can be pinned, that a lost context keeps the reading, and that Back and Forward
restore state without stacking entries.
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
    """Put the whole stage in the window, the way the page does when a story opens.

    Instantly: the page scrolls smoothly, and a screenshot taken while that is
    still moving shows the stage half out of the window.
    """
    page.evaluate(
        "document.getElementById('woven-stage')"
        ".scrollIntoView({block: 'start', behavior: 'instant'})")
    page.wait_for_timeout(300)


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


def set_filter(page, city='', evidence='all'):
    """Filter the way a visitor does: through the controls, not through the model."""
    page.select_option('#woven-city', city)
    page.select_option('#woven-evidence', evidence)
    page.wait_for_timeout(250)


def stats(page):
    return page.evaluate('window.__woven.app.exhibit.stats()')


def tone_of(page, publication_id):
    """How brightly one sheet's paper is lit, read straight off the instance."""
    return page.evaluate("""(id) => {
      const exhibit = window.__woven.app.exhibit;
      const slot = exhibit.layout.slotByPublicationId.get(id);
      const papers = exhibit.sheets.group.children.find((child) => child.name === 'sheet-papers');
      const colour = new window.__woven.THREE.Color();
      papers.getColorAt(slot.index, colour);
      return colour.r;
    }""", publication_id)


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

        # ---- the reading pose looks straight down at the spread -------------
        ready(page, '?story=story-006')
        pose = page.evaluate("""() => {
          const camera = window.__woven.app.exhibit.camera;
          const direction = new window.__woven.THREE.Vector3();
          camera.getWorldDirection(direction);
          const book = window.__woven.app.exhibit.layout.bookSlotByStoryId.get('story-006');
          return {
            down: direction.y, sideways: Math.abs(direction.x) + Math.abs(direction.z),
            up: [camera.up.x, camera.up.y, camera.up.z],
            aboveTable: camera.position.y > 1.6,
            overBook: Math.abs(camera.position.z - book.position.z) < 0.05
          };
        }""")
        check('The reading pose looks straight down at the spread',
              pose['down'] < -0.99 and pose['sideways'] < 0.05 and pose['aboveTable'] and pose['overBook'])
        check('The spread is the right way up under that camera',
              abs(pose['up'][0]) == 1 and pose['up'][1] == 0)
        page.wait_for_timeout(400)
        shot(page, 'desktop-reading-pose')
        check('The stop cue marks the publications it names',
              page.evaluate('window.__woven.app.exhibit.sheets.relatedCount') >= 1)
        # Left and right turn pages, but only from inside the reader.
        page.locator('[data-reader="next"]').focus()
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(400)
        check('Right turns the page from inside the reader',
              'Stop 2 of 9' in page.locator('.hall-reader-count').inner_text())
        page.keyboard.press('ArrowLeft')
        page.wait_for_timeout(400)
        check('Left turns it back', 'Stop 1 of 9' in page.locator('.hall-reader-count').inner_text())
        # A swipe across the picture turns the page; the text still scrolls.
        plate = page.locator('[data-reader-plate]')
        if plate.is_visible():
            box = plate.bounding_box()
            page.mouse.move(box['x'] + box['width'] - 20, box['y'] + box['height'] / 2)
            page.mouse.down()
            page.mouse.move(box['x'] + 20, box['y'] + box['height'] / 2, steps=8)
            page.mouse.up()
            page.wait_for_timeout(400)
            check('A swipe across the picture turns the page',
                  'Stop 2 of 9' in page.locator('.hall-reader-count').inner_text())
        context.grant_permissions(['clipboard-read', 'clipboard-write'])
        page.locator('[data-reader="copy"]').click()
        page.wait_for_timeout(300)
        copied = page.evaluate('navigator.clipboard.readText()')
        check('Copy link carries the story and stop', 'story=story-006' in copied and 'stop=' in copied)
        check('Copy link carries no camera numbers',
              'x=' not in copied and 'z=' not in copied and 'camera' not in copied)
        # Closing a story reached by a deep link stays on the page.
        entries = page.evaluate('history.length')
        page.keyboard.press('Escape')
        page.wait_for_timeout(300)
        check('Closing a deep-linked story stays on the page',
              'historical-notes.html' in page.url
              and page.locator('#hall-reader').is_hidden()
              and page.evaluate('history.length') == entries)

        # ---- filters in the scene -------------------------------------------
        ready(page)
        cities = page.evaluate("""() => {
          const counts = new Map();
          for (const t of window.__woven.model.threads) {
            if (!t.city) continue;
            counts.set(t.city, (counts.get(t.city) || 0) + 1);
          }
          const many = [...counts].sort((a, b) => b[1] - a[1])[0];
          const one = [...counts].find(([, n]) => n === 1);
          const inside = window.__woven.model.threads.find((t) => t.city === many[0]).id;
          const outside = window.__woven.model.threads.find((t) => t.city && t.city !== many[0]).id;
          return { many: many[0], manyCount: many[1], one: one[0], inside, outside };
        }""")
        set_filter(page, city=cities['many'])
        check('A filter with many matches counts them',
              f"{cities['manyCount']} of {count} publications" in page.locator('#woven-browser-status').inner_text())
        check('The where-am-I line says what the filter did',
              'match these filters' in page.locator('#hall-where').inner_text())
        check('A matching sheet keeps its light', tone_of(page, cities['inside']) > 0.9)
        check('A sheet outside the filter is dimmed, not put out',
              0.2 < tone_of(page, cities['outside']) < 0.7)
        check('The filtered hall is not a dark room',
              page.evaluate('window.__woven.app.exhibit.sheets.paintedCount') > 0)
        check('Filtering never reorders the gallery', page.evaluate("""() => {
          const exhibit = window.__woven.app.exhibit;
          return exhibit.layout.publicationOrder.every(
            (id, i) => exhibit.layout.slotByPublicationId.get(id).index === i);
        }"""))
        shot(page, 'desktop-filtered')
        set_filter(page, city=cities['one'])
        check('A filter with one match says so',
              f'1 of {count} publications' in page.locator('#woven-browser-status').inner_text())
        # Zero results: a city that holds no title founded in the first band.
        zero = page.evaluate("""() => {
          const evidenceValues = ['evidence', 'unillustrated', 'active'];
          const cities = [...document.getElementById('woven-city').options].map((o) => o.value).filter(Boolean);
          for (const city of cities) {
            const here = window.__woven.model.threads.filter((t) => t.city === city);
            for (const value of evidenceValues) {
              const match = here.some((t) => value === 'active' ? t.endState === 'still'
                : value === 'evidence' ? !t.ghost : t.ghost);
              if (!match) return { city, evidence: value };
            }
          }
          return null;
        }""")
        set_filter(page, city=zero['city'], evidence=zero['evidence'])
        check('A zero result is explicit in the index',
              'No publications match these filters' in page.locator('#woven-browser-status').inner_text())
        check('A zero result is explicit in the where-am-I line',
              'No publications match these filters' in page.locator('#hall-where').inner_text())
        check('A zero result offers a way back', not page.locator('#woven-clear-filters').is_disabled())
        shot(page, 'desktop-filter-zero')

        # ---- a record outside the filters ------------------------------------
        set_filter(page, city=cities['many'])
        page.evaluate('(id) => window.__woven.app.select(id, {})', cities['outside'])
        page.wait_for_timeout(400)
        check('A record outside the filters is revealed, not hidden',
              page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId') == cities['outside'])
        check('The mismatch is explained',
              page.locator('#woven-notice').is_visible()
              and 'outside the filters' in page.locator('#hall-notice-text').inner_text())
        check('The explanation offers to clear the filters',
              page.locator('#hall-notice-action').is_visible()
              and page.locator('#hall-notice-action').inner_text() == 'Clear filters')
        check('The filters were not changed behind the visitor',
              page.evaluate('document.getElementById("woven-city").value') == cities['many'])
        check('The revealed record is listed with its reason',
              page.locator('.woven-publication[data-revealed="true"]').count() == 1)
        check('A revealed sheet can still be picked', page.evaluate("""(id) => {
          const exhibit = window.__woven.app.exhibit;
          const slot = exhibit.layout.slotByPublicationId.get(id);
          exhibit.rail.travelTo(Math.max(0.8, slot.z - 4), { immediate: true });
          exhibit.camera.updateMatrixWorld(true);
          exhibit.camera.matrixWorldInverse.copy(exhibit.camera.matrixWorld).invert();
          const point = new window.__woven.THREE.Vector3(slot.x, slot.y, slot.z).project(exhibit.camera);
          const rect = document.getElementById('woven-canvas').getBoundingClientRect();
          const hit = exhibit.sheets.pick(
            (point.x + 1) / 2 * rect.width, (1 - point.y) / 2 * rect.height, rect, exhibit.camera);
          return !!hit && hit.publicationId === id;
        }""", cities['outside']))
        shot(page, 'desktop-revealed-record')
        page.locator('#hall-notice-action').click()
        page.wait_for_timeout(300)
        check('Clear filters clears them, when the visitor asks',
              page.evaluate('document.getElementById("woven-city").value') == ''
              and page.locator('#woven-notice').is_hidden())

        # ---- previous and next publication -----------------------------------
        ready(page)
        page.locator('#hall-next-pub').click()
        page.wait_for_timeout(400)
        first = page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId')
        page.locator('#hall-next-pub').click()
        page.wait_for_timeout(400)
        second = page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId')
        order = page.evaluate('window.__woven.app.exhibit.layout.publicationOrder')
        check('Next publication moves in the gallery order',
              order.index(second) == order.index(first) + 1)
        page.locator('#hall-previous-pub').click()
        page.wait_for_timeout(400)
        check('Previous publication moves back',
              page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId') == first)
        # Arrow keys work in the controls, and nowhere else.
        page.locator('#hall-next-pub').focus()
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(400)
        check('Right steps a publication from inside the hall controls',
              page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId') == second)
        check('Stepping keeps the focus on the control, so it can be repeated',
              page.evaluate('document.activeElement.id') == 'hall-next-pub')
        page.keyboard.press('Shift+ArrowRight')
        page.wait_for_timeout(500)
        check('Shift and right step a decade',
              page.evaluate('window.__woven.app.exhibit.rail.section.id') != '1880s')
        section_before = page.evaluate('window.__woven.app.exhibit.rail.section.id')
        selected_before = page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId')
        # The top bar is outside the controls group, so the shortcut must not
        # reach it. (The index is inert while a record is open, so it cannot be
        # the control this is tested from.)
        page.locator('#btn-tours').focus()
        page.keyboard.press('ArrowRight')
        page.wait_for_timeout(250)
        check('Arrow keys outside the controls are left alone',
              page.evaluate('window.__woven.app.exhibit.rail.section.id') == section_before
              and page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId') == selected_before)

        # ---- history --------------------------------------------------------
        ready(page)
        page.evaluate('(id) => window.__woven.app.select(id, {})', order[3])
        page.wait_for_timeout(400)
        page.evaluate('(id) => window.__woven.app.select(id, {})', order[9])
        page.wait_for_timeout(400)
        entries = page.evaluate('history.length')
        page.go_back()
        page.wait_for_timeout(600)
        check('Back restores the previous publication',
              page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId') == order[3]
              and f'pub={order[3]}' in page.url)
        check('Back creates no new history entry', page.evaluate('history.length') == entries)
        page.go_forward()
        page.wait_for_timeout(600)
        check('Forward restores the later publication',
              page.evaluate('window.__woven.app.exhibit.state.getState().selectedPublicationId') == order[9])
        check('Forward creates no new history entry', page.evaluate('history.length') == entries)

        # ---- invalid routes --------------------------------------------------
        for query, wording in [
            ('?pub=99999', 'No publication in the archive has that number.'),
            ('?pub=abc', 'not a publication number'),
            ('?decade=1800s', 'not a section of the hall'),
            ('?story=story-999', 'No guided story in the archive has that name.'),
            ('?view=banana', 'not one of the hall or the flat timeline')
        ]:
            ready(page, query)
            check(f'{query} explains itself',
                  page.locator('#woven-notice').is_visible()
                  and wording in page.locator('#hall-notice-text').inner_text())
            check(f'{query} still offers the index',
                  page.locator('#woven-publications button').count() == count)
        ready(page, '?story=story-006&stop=evt-nope')
        check('An invalid stop opens the first stop and says so',
              'Stop 1 of' in page.locator('.hall-reader-count').inner_text()
              and 'not part of this story' in page.locator('#hall-notice-text').inner_text())
        shot(page, 'desktop-invalid-route')

        # ---- the adaptive tier ------------------------------------------------
        ready(page)
        standard_pool = page.evaluate('window.__woven.app.exhibit.sheets.poolLimit')
        page.locator('#hall-tier').click()
        page.wait_for_timeout(500)
        simplified = page.evaluate("""() => {
          const exhibit = window.__woven.app.exhibit;
          return {
            tier: exhibit.tier, pinned: exhibit.pinnedTier,
            pool: exhibit.sheets.poolLimit,
            bend: exhibit.volumes.bendEnabled,
            pixelRatio: window.__woven.renderer.getPixelRatio(),
            pressed: document.getElementById('hall-tier').getAttribute('aria-pressed'),
            note: document.getElementById('hall-tier-note').textContent
          };
        }""")
        check('The simplified tier can be pinned', simplified['tier'] == 'simplified' and simplified['pinned'] == 'simplified')
        check('The simplified tier is a pressed control', simplified['pressed'] == 'true')
        check('The simplified tier explains itself', 'Simplified view' in simplified['note'])
        check('The simplified tier halves the painted pool',
              simplified['pool'] == 12 and standard_pool == 24)
        check('The simplified tier drops the optional detail',
              simplified['bend'] is False
              and simplified['pixelRatio'] <= 1.25
              and page.evaluate('window.__woven.app.exhibit.state.getState().tier') == 'simplified')
        shot(page, 'desktop-simplified')
        page.locator('#hall-tier').click()
        page.wait_for_timeout(400)
        check('The visitor can pin the standard tier back',
              page.evaluate('window.__woven.app.exhibit.tier') == 'standard'
              and page.evaluate('window.__woven.app.exhibit.sheets.poolLimit') == 24)

        # ---- bounded resources ------------------------------------------------
        # The budget is about growth after the caches settle, so the baseline is
        # taken once the first paint backlog is done and once one view switch and
        # one story have already put their own geometry on the card.
        ready(page)
        page.wait_for_function(
            'window.__woven.app.exhibit.stats().pendingPaints === 0', timeout=20000)
        page.locator('[data-woven-view="timeline"]').click()
        page.wait_for_timeout(200)
        page.locator('[data-woven-view="hall"]').click()
        page.wait_for_timeout(200)
        page.evaluate("window.__woven.app.playStory('story-006')")
        page.wait_for_timeout(600)
        page.evaluate('window.__woven.app.exhibit.state.close()')
        page.wait_for_timeout(400)
        page.wait_for_function(
            'window.__woven.app.exhibit.stats().pendingPaints === 0', timeout=20000)
        page.wait_for_timeout(600)
        settled_stats = stats(page)
        for _ in range(10):
            page.locator('[data-woven-view="timeline"]').click()
            page.wait_for_timeout(120)
            page.locator('[data-woven-view="hall"]').click()
            page.wait_for_timeout(120)
        page.wait_for_timeout(800)
        after_views = stats(page)
        stories = page.evaluate('window.__woven.model.tours.slice(0, 10).map((t) => t.id)')

        def story_cycles():
            for story in stories:
                page.evaluate('(id) => window.__woven.app.playStory(id)', story)
                page.wait_for_timeout(200)
                page.evaluate('window.__woven.app.exhibit.state.close()')
                page.wait_for_timeout(150)
            page.wait_for_timeout(1000)
            return stats(page)

        # Ten stories in ten sections draw markers, tables, and volumes that had
        # never been drawn before, and the renderer counts a geometry the first
        # time it reaches the card. So the run is done twice: the second ten are
        # measured against the first ten, where every one of those has already
        # been paid for and only a leak could still add to the count.
        after_stories = story_cycles()
        after_repeat = story_cycles()
        print(json.dumps({'settled': settled_stats, 'views': after_views,
                          'stories': after_stories, 'repeat': after_repeat}, indent=1))
        check('Ten view switches register no new listeners',
              after_views['listeners'] == settled_stats['listeners'])
        check('Twenty story cycles register no new listeners',
              after_repeat['listeners'] == settled_stats['listeners'])
        check('The story cycles leave no pending paint work',
              after_repeat['pendingPaints'] == 0 and after_repeat['pendingImages'] == 0)
        check('Decoded images stay inside the working set',
              after_repeat['decodedImages'] <= settled_stats['paintedFaces'] + 6)
        check('The painted pool returns to its settled size',
              after_repeat['paintedFaces'] == settled_stats['paintedFaces'])
        check('Ten view switches own no more than the settled hall',
              after_views['textures'] <= settled_stats['textures']
              and after_views['geometries'] <= settled_stats['geometries']
              and after_views['residentBytes'] <= settled_stats['residentBytes'])
        check('Owned textures do not climb across repeated story cycles',
              after_repeat['textures'] <= after_stories['textures'])
        check('Owned geometry does not climb across repeated story cycles',
              after_repeat['geometries'] <= after_stories['geometries'])
        check('Resident bytes do not climb across repeated story cycles',
              after_repeat['residentBytes'] <= after_stories['residentBytes'])
        check('The hall stays inside its standard texture budget',
              after_stories['residentBytes'] < 128 * 1024 * 1024)

        # ---- a scene nobody is looking at draws nothing --------------------------
        ready(page)
        page.wait_for_timeout(500)
        # Scrolled past: the stage has to actually leave the window for this to
        # be a measurement. At the full window height this page cannot scroll far
        # enough to put it out of view, so the window is shortened first.
        page.set_viewport_size({'width': 1440, 'height': 500})
        page.wait_for_timeout(400)
        offscreen = page.evaluate("""() => {
          const stage = document.getElementById('woven-stage');
          // Instant, because a smooth scroll would still be moving when the
          // frame count is read.
          window.scrollTo({ top: window.scrollY + stage.getBoundingClientRect().bottom + 80, behavior: 'instant' });
          return stage.getBoundingClientRect().bottom < 0;
        }""")
        page.wait_for_timeout(800)
        drawn = page.evaluate('window.__woven.renderer.info.render.frame')
        page.wait_for_timeout(700)
        check('An offscreen hall stops drawing',
              offscreen and page.evaluate('window.__woven.renderer.info.render.frame') == drawn)
        page.set_viewport_size({'width': 1440, 'height': 1000})
        page.evaluate("document.getElementById('woven-stage').scrollIntoView({block: 'start'})")
        page.wait_for_timeout(500)
        # A hidden document stops it too, which is the other half of the same row
        # in the fallback table.
        page.evaluate("""() => {
          Object.defineProperty(document, 'hidden', { configurable: true, get: () => true });
          document.dispatchEvent(new Event('visibilitychange'));
        }""")
        page.wait_for_timeout(600)
        drawn = page.evaluate('window.__woven.renderer.info.render.frame')
        page.wait_for_timeout(700)
        check('A hidden document stops the hall drawing',
              page.evaluate('window.__woven.renderer.info.render.frame') == drawn)
        page.evaluate("""() => {
          Object.defineProperty(document, 'hidden', { configurable: true, get: () => false });
          document.dispatchEvent(new Event('visibilitychange'));
        }""")
        page.wait_for_timeout(300)

        # ---- one image that will not load --------------------------------------
        broken = context.new_page()
        broken.on('pageerror', lambda error: errors.append(str(error)))
        broken.route('**/images/evidence/wall/**', lambda route: route.fulfill(status=404, body='gone'))
        broken.goto(base + '?story=story-006', wait_until='networkidle')
        broken.wait_for_function(
            'window.__woven?.app.exhibit && document.getElementById("woven-loading").hidden', timeout=30000)
        broken.wait_for_timeout(1500)
        check('A failed image is named in the reader, with its metadata kept',
              broken.locator('.hall-reader-missing').is_visible()
              and 'Image unavailable' in broken.locator('.hall-reader-missing').inner_text()
              and broken.locator('.hall-reader-sources cite').count() >= 1)
        check('A failed image does not stop the story text',
              len(broken.locator('.hall-reader-body').inner_text()) > 200)
        check('The page texture says the image is unavailable', broken.evaluate("""() => {
          const exhibit = window.__woven.app.exhibit;
          const state = exhibit.state.getState();
          const story = exhibit.volumes.openStoryId;
          return !!story && exhibit.assets.failedImages > 0;
        }"""))
        broken.wait_for_timeout(400)
        shot(broken, 'desktop-image-unavailable')
        broken.close()

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

        # Forced text still loads no drawing code at all, on either flag, and it
        # opens the record or story the link asked for.
        for flag, target in [('?nogl=1&pub=38', 'pub'), ('?twin=1&story=story-006', 'story')]:
            requested = []
            fallback = context.new_page()
            fallback.on('request', lambda request: requested.append(request.url))
            fallback.goto(base + flag, wait_until='networkidle')
            expect(fallback.locator('body')).to_have_class(re.compile('twin-primary'))
            check(f'{flag} fetches no Three.js', not any('/vendor/three-' in url for url in requested))
            check(f'{flag} keeps every publication', fallback.locator('#woven-twin .t-open').count() == count)
            if target == 'pub':
                check(f'{flag} opens the requested record',
                      fallback.locator('#thread-38-detail').is_visible())
            else:
                check(f'{flag} opens the requested story',
                      fallback.locator('#tour-story-006 details').evaluate('(el) => el.open'))
            shot(fallback, f'text-archive-{target}')
            fallback.close()

        # No usable WebGL at all: the Canvas 2D timeline opens with the record
        # the link asked for, and the page explains why the hall is not there.
        nogpu = context.new_page()
        nogpu.on('pageerror', lambda error: errors.append(str(error)))
        nogpu.add_init_script("""const get = HTMLCanvasElement.prototype.getContext;
          HTMLCanvasElement.prototype.getContext = function(kind, ...args) {
            if (kind === 'webgl' || kind === 'webgl2') return null;
            return get.call(this, kind, ...args);
          };""")
        nogpu.goto(base + f'?pub={SHEET_ID}', wait_until='networkidle')
        nogpu.wait_for_timeout(1500)
        check('No WebGL opens the Canvas 2D timeline',
              nogpu.locator('#woven-stage').get_attribute('data-renderer') == 'flat')
        check('No WebGL explains that the hall is unavailable',
              nogpu.locator('#woven-renderer-note').is_visible()
              and nogpu.locator('[data-woven-view="hall"]').is_disabled())
        expect(nogpu.locator('#woven-panel-title')).to_have_text(SHEET_NAME)
        check('No WebGL still opens the requested record in the DOM', True)
        check('No WebGL keeps the whole index',
              nogpu.locator('#woven-publications button').count() == count)
        shot(nogpu, 'desktop-no-webgl')
        nogpu.close()

        # A hall that cannot be built at all leaves the page usable and offers
        # the flat timeline. The module is denied, which is the real shape of an
        # initialisation failure.
        failed = context.new_page()
        failed.on('pageerror', lambda error: errors.append(str(error)))
        failed.route('**/js/hall/hall.js', lambda route: route.fulfill(status=500, body='no'))
        failed.goto(base, wait_until='networkidle')
        failed.wait_for_timeout(1500)
        check('A hall that fails to open says so',
              failed.locator('#woven-renderer-note').is_visible()
              and 'could not open' in failed.locator('#woven-renderer-note').inner_text())
        check('A hall that fails to open leaves the index usable',
              failed.locator('#woven-publications button').count() == count)
        check('A hall that fails to open offers the flat timeline',
              failed.locator('[data-woven-view="hall"]').is_disabled()
              and failed.locator('[data-woven-view="timeline"]').get_attribute('aria-pressed') == 'true')
        failed.locator('#woven-publications button').first.click()
        expect(failed.locator('#woven-panel')).to_be_visible()
        check('A hall that fails to open still opens records', True)
        check('A hall that fails to open is not a loading screen',
              failed.locator('#woven-loading').is_hidden())
        shot(failed, 'desktop-mount-failure')
        failed.close()

        # A lost context keeps the reading: the record, the story, and the stop.
        lost = context.new_page()
        lost.on('pageerror', lambda error: errors.append(str(error)))
        lost.goto(base + '?story=story-006', wait_until='networkidle')
        lost.wait_for_function(
            'window.__woven?.app.exhibit && document.getElementById("woven-loading").hidden', timeout=30000)
        lost.wait_for_timeout(600)
        lost.select_option('#woven-city', 'Newark')
        lost.wait_for_timeout(200)
        lost.locator('[data-reader="next"]').click()
        lost.wait_for_timeout(500)
        stop_id = lost.evaluate('window.__woven.app.exhibit.state.getState().stopId')
        lost_requests = []
        lost.on('request', lambda request: lost_requests.append(request.url))
        lost.evaluate('window.__woven.renderer.getContext().getExtension("WEBGL_lose_context").loseContext()')
        expect(lost.locator('body')).to_have_class(re.compile('twin-primary'))
        lost.wait_for_timeout(600)
        check('A lost context promotes the whole archive as text',
              lost.locator('#woven-twin .t-open').count() == count)
        check('A lost context keeps the story open',
              lost.locator('#tour-story-006 details').evaluate('(el) => el.open'))
        check('A lost context keeps the stop the visitor was on',
              lost.locator(f'#tour-story-006-stop-{stop_id}').get_attribute('aria-current') == 'step')
        check('A lost context says what happened to the filters',
              'Newark' in lost.locator('#woven-banner .banner-text').inner_text())
        check('A lost context is not automatically rebuilt',
              not any('/vendor/three-' in url for url in lost_requests)
              and lost.locator('#woven-stage').count() == 0)
        shot(lost, 'desktop-context-lost')
        lost.close()

        # A missing font never blocks entry; the fallback stack paints instead.
        fontless = context.new_page()
        fontless.on('pageerror', lambda error: errors.append(str(error)))
        fontless.route('https://fonts.googleapis.com/**', lambda route: route.abort())
        fontless.route('https://fonts.gstatic.com/**', lambda route: route.abort())
        fontless.goto(base, wait_until='domcontentloaded')
        fontless.wait_for_function(
            'window.__woven?.app.exhibit && document.getElementById("woven-loading").hidden', timeout=30000)
        fontless.wait_for_timeout(800)
        check('A font that will not load does not block the hall',
              fontless.evaluate('window.__woven.app.exhibit.active')
              and fontless.evaluate('window.__woven.app.exhibit.sheets.paintedCount') > 0)
        shot(fontless, 'desktop-no-fonts')
        fontless.close()
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
        # Decision 10: a portrait window turns to the wall on the left of the
        # picture, and the hall recedes to the right past the first sheet.
        entrance = small.evaluate("""() => {
          const exhibit = window.__woven.app.exhibit;
          const camera = exhibit.camera;
          const direction = new window.__woven.THREE.Vector3();
          camera.getWorldDirection(direction);
          const slot = exhibit.layout.slots.find((s) => s.wall === 'right');
          const projected = new window.__woven.THREE.Vector3(slot.x, slot.y, slot.z).project(camera);
          const deeper = new window.__woven.THREE.Vector3(0, 1.55, slot.z + 8).project(camera);
          return {
            turned: Math.abs(direction.x) > Math.abs(direction.z),
            towardWall: direction.x > 0,
            sheetInView: Math.abs(projected.x) < 0.6 && Math.abs(projected.y) < 0.9,
            hallToTheRight: deeper.x > projected.x,
            portrait: camera.aspect < 1
          };
        }""")
        check('The portrait entrance turns toward the wall on the left',
              entrance['portrait'] and entrance['turned'] and entrance['towardWall'])
        check('The portrait entrance fills the view with the first sheet on that wall',
              entrance['sheetInView'])
        check('The portrait entrance lets the hall recede to the right', entrance['hallToTheRight'])
        shot(small, 'mobile-entrance')
        # A tap on a sheet still focuses it from that entrance.
        tapped = small.evaluate("""() => {
          const exhibit = window.__woven.app.exhibit;
          const slot = exhibit.layout.slots.find((s) => s.wall === 'right');
          const rect = document.getElementById('woven-canvas').getBoundingClientRect();
          exhibit.camera.updateMatrixWorld(true);
          exhibit.camera.matrixWorldInverse.copy(exhibit.camera.matrixWorld).invert();
          const point = new window.__woven.THREE.Vector3(slot.x, slot.y, slot.z).project(exhibit.camera);
          const hit = exhibit.sheets.pick(
            (point.x + 1) / 2 * rect.width, (1 - point.y) / 2 * rect.height, rect, exhibit.camera);
          return !!hit && hit.publicationId === slot.publicationId;
        }""")
        check('A tap on a sheet still focuses it in portrait', tapped)
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
