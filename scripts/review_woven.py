"""Real Chromium smoke checks and visual evidence for both historical notes views.

Run: python scripts/review_woven.py --output /tmp/woven-review
Requires Playwright and its Chromium browser. Does not change archive data.
"""
import argparse
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import traceback
from playwright.sync_api import sync_playwright, expect

ROOT = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument('--output', default='/tmp/woven-review')
args = parser.parse_args()
output = Path(args.output)
output.mkdir(parents=True, exist_ok=True)
server = ThreadingHTTPServer(('127.0.0.1', 0), partial(SimpleHTTPRequestHandler, directory=str(ROOT/'docs')))
threading.Thread(target=server.serve_forever, daemon=True).start()
base = f'http://127.0.0.1:{server.server_port}/historical-notes.html'
results = []
errors = []

def check(name, condition):
    assert condition, name
    results.append(name)

def ready(page, query=''):
    page.goto(base+query, wait_until='networkidle')
    page.wait_for_function('window.__woven?.app.exhibit && document.getElementById("woven-loading").hidden', timeout=30000)
    page.wait_for_timeout(300)

def shot(page, name, full=False):
    page.screenshot(path=str(output/f'{name}.png'), full_page=full, animations='disabled')

try:
    with sync_playwright() as pw:
        browser = pw.chromium.launch(args=['--use-angle=swiftshader', '--enable-unsafe-swiftshader'])
        context = browser.new_context(viewport={'width':1440,'height':1000}, device_scale_factor=1, reduced_motion='reduce')
        page = context.new_page()
        page.on('pageerror', lambda error: errors.append(str(error)))
        ready(page)
        check('Default opens a real WebGL 3D scene', page.evaluate('window.__woven.app.exhibit.active && !!window.__woven.renderer.getContext()'))
        check('No forced welcome modal', page.locator('#woven-start-card').is_hidden())
        check('Reduced motion starts paused', page.evaluate('!window.__woven.app.exhibit.motion'))
        count = page.evaluate('window.__woven.model.counts.total')
        check('Every publication has a native index button', page.locator('#woven-publications button').count()==count)
        check('No horizontal page overflow on desktop', page.evaluate('document.documentElement.scrollWidth <= innerWidth'))
        check('Full text archive starts collapsed', not page.locator('#woven-list-disclosure').evaluate('(el)=>el.open'))
        check('3D timeline shows the recorded year range', page.locator('#woven-exhibit-axis').inner_text().startswith('1880') and '2026' in page.locator('#woven-exhibit-axis').inner_text())
        check('Short-lived title uses only its recorded span', page.evaluate('''() => {
          const exhibit = window.__woven.app.exhibit;
          const node = exhibit.nodes.find(n => n.thread.name === 'New Jersey Trumpet');
          const curve = node.curves[0];
          return Math.abs(curve[0].x - ((1887-1880)/146-.5)*80) < .001
            && Math.abs(curve.at(-1).x - ((1897-1880)/146-.5)*80) < .001;
        }'''))
        shot(page, 'desktop-woven', True)
        page.locator('#woven-motion').click()
        check('Motion is opt-in under reduced motion', page.evaluate('window.__woven.app.exhibit.motion'))
        page.locator('#woven-motion').click()
        page.mouse.move(1,1)
        before = page.evaluate('window.__woven.renderer.info.render.frame')
        page.wait_for_timeout(350)
        after = page.evaluate('window.__woven.renderer.info.render.frame')
        check('Paused scene does not continuously render', after-before <= 2)
        page.locator('#woven-evidence').select_option('active')
        active_count=page.evaluate('window.__woven.model.counts.stillPublishing')
        check('Active filter matches archive records', page.locator('#woven-publications button').count()==active_count)
        city=page.locator('#woven-city option').nth(1).get_attribute('value')
        page.locator('#woven-city').select_option(city)
        expected=page.evaluate('(city)=>window.__woven.model.threads.filter(t=>t.city===city && t.endState==="still").length',city)
        check('City and status filters combine', page.locator('#woven-publications button').count()==expected)
        page.locator('#woven-clear-filters').click()
        page.locator('[data-era="C"]').click()
        era_count = page.evaluate('window.__woven.model.bands.find(b=>b.key==="C").count')
        check('Founding era filters the index', page.locator('#woven-publications button').count()==era_count)
        page.locator('#woven-evidence').select_option('evidence')
        expected = page.evaluate('window.__woven.model.threads.filter(t=>t.bandKey==="C" && !t.ghost).length')
        check('Era and evidence filters combine', page.locator('#woven-publications button').count()==expected)
        page.locator('#woven-search').fill('Sentinel')
        page.get_by_role('option').first.click()
        expect(page.locator('#woven-panel')).to_be_visible()
        page.locator('#woven-panel .p-close').click()
        check('Cross-era search restores the selected title in the index', page.locator('#woven-publications button[aria-pressed="true"]').count()==1)
        check('Cross-era selection clears conflicting filters', page.locator('[data-era="all"]').get_attribute('aria-pressed')=='true')
        page.locator('#woven-search').fill('')
        chosen=page.locator('#woven-publications button').first
        publication=int(chosen.get_attribute('data-pub'))
        title=chosen.locator('strong').inner_text()
        chosen.click()
        expect(page.locator('#woven-panel-title')).to_have_text(title)
        check('Record dock leaves the art visible', page.locator('#woven-canvas').is_visible())
        check('Index is inert while its record dock is open', page.locator('#woven-browser').evaluate('(el)=>el.inert'))
        check('Selection has a shareable URL', f'pub={publication}' in page.url)
        check('Default 3D selection keeps its mode in shared links', 'view=3d' in page.url)
        shot(page,'desktop-record')
        page.locator('#woven-panel .p-close').click()
        page.wait_for_timeout(80)
        check('Record close restores the index', not page.locator('#woven-browser').evaluate('(el)=>el.inert'))
        check('Record close returns keyboard focus to the publication', page.evaluate('document.activeElement.dataset.pub') == str(publication))
        page.mouse.move(1,1)
        page.evaluate('window.scrollTo(0,120)')
        point=page.evaluate('''()=>{const n=window.__woven.app.exhibit.nodes.find(n=>!n.thread.ghost);const a=n.projected[0][0], b=n.projected[0].at(-1);const p={x:(a.x+b.x)/2,y:(a.y+b.y)/2};const r=document.getElementById('woven-canvas').getBoundingClientRect();return {x:r.left+p.x,y:r.top+p.y};}''')
        page.mouse.click(point['x'],point['y'])
        expect(page.locator('#woven-panel')).to_be_visible()
        check('Canvas hit testing works after the page scrolls', True)
        page.locator('#woven-panel .p-close').click()
        page.locator('#woven-publications button').first.click()
        page.locator('#woven-find-title').click()
        expect(page.locator('#woven-search')).to_be_focused()
        check('Find a title restores search focus from an open record', True)
        page.locator('[data-woven-view="timeline"]').click()
        page.wait_for_timeout(600)
        check('Precise timeline is available', not page.evaluate('window.__woven.app.exhibit.active'))
        page.locator('#btn-whole').click()
        distance = page.evaluate('window.__woven.camera.position.z')
        page.get_by_role('button', name='Zoom in', exact=True).click()
        check('Visible zoom changes the timeline camera', page.evaluate('window.__woven.camera.position.z') < distance)
        page.locator('#woven-more-tools summary').click()
        page.get_by_role('button', name='Reset the view', exact=True).click()
        check('Reset preserves Timeline mode', not page.evaluate('window.__woven.app.exhibit.active'))
        if page.locator('#woven-more-tools').evaluate('(el)=>el.open'):
            page.locator('#woven-more-tools summary').click()
        shot(page,'desktop-timeline')
        page.locator('[data-woven-view="3d"]').click()
        page.locator('#woven-canvas').focus()
        page.keyboard.press('ArrowDown')
        page.keyboard.press('Enter')
        expect(page.locator('#woven-panel')).to_be_visible()
        check('Canvas can select a record with the keyboard', True)
        page.keyboard.press('Escape')
        page.locator('#woven-story-list button').first.click()
        page.wait_for_function('window.__woven.app.tour?.isPlaying')
        check('Sourced stories open in the precise timeline', not page.evaluate('window.__woven.app.exhibit.active'))
        page.wait_for_timeout(400)
        shot(page,'desktop-story')
        page.evaluate('window.njbpWoven.exit()')
        # Explicit sculptural links and old publication links both remain valid.
        ready(page,f'?view=3d&pub={publication}')
        check('Sculptural record deep link preserves its view', page.evaluate('window.__woven.app.exhibit.active'))
        expect(page.locator('#woven-panel-title')).to_have_text(title)
        ready(page,'?twin=1')
        check('Explicit text-view link opens the list',page.locator('#woven-list-disclosure').evaluate('(el)=>el.open'))
        ready(page,f'?pub={publication}')
        check('Existing publication deep link preserves timeline behavior', not page.evaluate('window.__woven.app.exhibit.active'))
        # Reuse no framework and no GPU code on the fallback path.
        requested=[]
        fallback=context.new_page()
        fallback.on('request',lambda request:requested.append(request.url))
        fallback.goto(base+'?nogl=1',wait_until='networkidle')
        expect(fallback.locator('body')).to_have_class(__import__('re').compile('twin-primary'))
        check('Fallback does not fetch Three.js', not any('/vendor/three-' in url for url in requested))
        check('Fallback has all publication disclosures', fallback.locator('#woven-twin .t-open').count()==count)
        fallback.locator('#woven-twin .t-open').first.click()
        expect(fallback.locator('#woven-twin .t-detail').first).to_be_visible()
        shot(fallback,'no-webgl')
        fallback.close()
        # Deny WebGL to exercise the real compatibility path, not a query shortcut.
        flat = context.new_page()
        flat.add_init_script("""const get = HTMLCanvasElement.prototype.getContext;
          HTMLCanvasElement.prototype.getContext = function(kind, ...args) {
            if (kind === 'webgl' || kind === 'webgl2') return null;
            return get.call(this, kind, ...args);
          };""")
        ready(flat)
        check('Unavailable WebGL opens the interactive flat timeline', flat.locator('#woven-stage').get_attribute('data-renderer')=='flat')
        check('Flat mode explains the unavailable 3D view', flat.locator('#woven-renderer-note').is_visible() and flat.locator('[data-woven-view="3d"]').is_disabled())
        flat.locator('[data-era="C"]').click()
        check('Flat timeline retains era browsing', flat.locator('#woven-publications button').count()==era_count)
        flat.locator('#woven-publications button').first.click()
        expect(flat.locator('#woven-panel')).to_be_visible()
        flat.locator('#woven-panel .p-close').click()
        flat.locator('#woven-story-list button').first.click()
        flat.wait_for_function('window.__woven.app.tour?.isPlaying')
        check('Flat timeline retains guided stories', True)
        flat.evaluate('window.njbpWoven.exit()')
        shot(flat, 'flat-timeline')
        flat.close()
        # Failed data is explicit, rather than an endless loading screen.
        failed=context.new_page()
        failed.route('**/data/publications.json',lambda route:route.fulfill(status=503,body='Unavailable'))
        failed.goto(base,wait_until='networkidle')
        check('Data failure has a visible explanation', 'could not load' in failed.locator('#woven-loading').inner_text().lower())
        shot(failed,'data-error')
        failed.close()
        ready(page)
        page.locator('#woven-browser a[href="#woven-twin"]').click()
        check('Read-as-list link opens the complete archive',page.locator('#woven-list-disclosure').evaluate('(el)=>el.open'))
        ready(page)
        page.evaluate('window.__woven.renderer.getContext().getExtension("WEBGL_lose_context").loseContext()')
        expect(page.locator('body')).to_have_class(__import__('re').compile('twin-primary'))
        check('Lost WebGL context promotes the same archive list', page.locator('#woven-twin .t-open').count()==count)
        check('Context loss removes unusable visual story controls',page.locator('#woven-stories').is_hidden())
        context.close()
        # Separate touch contexts: drawing and index stack without overlaying.
        for width,height in [(390,844),(320,740),(375,812),(768,1024)]:
            mobile=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,is_mobile=True,has_touch=True,reduced_motion='reduce')
            p=mobile.new_page()
            p.on('pageerror',lambda error:errors.append(str(error)))
            ready(p)
            check(f'{width}px has no horizontal page overflow',p.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            boxes=p.evaluate('''()=>{const a=document.getElementById('woven-canvas').getBoundingClientRect();const b=document.getElementById('woven-browser').getBoundingClientRect();return {bottom:a.bottom,top:b.top}}''')
            check(f'{width}px index is below the drawing',boxes['top']>=boxes['bottom']-2)
            check(f'{width}px search has one visible label',p.locator('#woven-searchform .woven-search-submit').evaluate("el=>getComputedStyle(el,'::before').content") in ('none','normal','\"\"'))
            shot(p,f'mobile-{width}',True)
            p.locator('#woven-publications button').first.click()
            expect(p.locator('#woven-panel')).to_be_visible()
            p.locator('#woven-panel .p-close').click()
            check(f'{width}px record can close',p.locator('#woven-panel').is_hidden())
            mobile.close()
        browser.close()
    check('No uncaught browser errors',not errors)
except Exception:
    errors.append(traceback.format_exc())
    try: shot(page,'failure',True)
    except Exception: pass
finally:
    server.shutdown()
    (output/'results.json').write_text(json.dumps({'passed':results,'errors':errors},indent=2))
    print(json.dumps({'passed':results,'errors':errors},indent=2))
if errors: raise SystemExit(1)
