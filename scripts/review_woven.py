"""Real Chromium smoke checks and visual evidence for both Woven views.

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
base = f'http://127.0.0.1:{server.server_port}/woven.html'
results = []
errors = []

def check(name, condition):
    assert condition, name
    results.append(name)

def ready(page, query=''):
    page.goto(base+query, wait_until='networkidle')
    page.wait_for_function('window.__woven?.app.exhibit && !document.getElementById("woven-loading").hidden === false', timeout=30000)
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
        chosen=page.locator('#woven-publications button').first
        publication=int(chosen.get_attribute('data-pub'))
        title=chosen.locator('strong').inner_text()
        chosen.click()
        expect(page.locator('#woven-panel-title')).to_have_text(title)
        check('Record dock leaves the art visible', page.locator('#woven-canvas').is_visible())
        check('Index is inert while its record dock is open', page.locator('#woven-browser').evaluate('(el)=>el.inert'))
        check('Selection has a shareable URL', f'pub={publication}' in page.url)
        shot(page,'desktop-record')
        page.locator('#woven-panel .p-close').click()
        page.wait_for_timeout(80)
        check('Record close restores the index', not page.locator('#woven-browser').evaluate('(el)=>el.inert'))
        page.locator('[data-woven-view="timeline"]').click()
        page.wait_for_timeout(600)
        check('Precise timeline is available', not page.evaluate('window.__woven.app.exhibit.active'))
        shot(page,'desktop-timeline')
        page.locator('[data-woven-view="woven"]').click()
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
        ready(page,f'?view=woven&pub={publication}')
        check('Sculptural record deep link preserves its view', page.evaluate('window.__woven.app.exhibit.active'))
        expect(page.locator('#woven-panel-title')).to_have_text(title)
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
        # Failed data is explicit, rather than an endless loading screen.
        failed=context.new_page()
        failed.route('**/data/publications.json',lambda route:route.fulfill(status=503,body='Unavailable'))
        failed.goto(base,wait_until='networkidle')
        check('Data failure has a visible explanation', 'could not load' in failed.locator('#woven-loading').inner_text().lower())
        shot(failed,'data-error')
        failed.close()
        ready(page)
        page.evaluate('window.__woven.renderer.getContext().getExtension("WEBGL_lose_context").loseContext()')
        expect(page.locator('body')).to_have_class(__import__('re').compile('twin-primary'))
        check('Lost WebGL context promotes the same archive list', page.locator('#woven-twin .t-open').count()==count)
        context.close()
        # Separate touch contexts: drawing and index stack without overlaying.
        for width,height in [(390,844),(375,812),(768,1024)]:
            mobile=browser.new_context(viewport={'width':width,'height':height},device_scale_factor=1,is_mobile=True,has_touch=True,reduced_motion='reduce')
            p=mobile.new_page()
            p.on('pageerror',lambda error:errors.append(str(error)))
            ready(p)
            check(f'{width}px has no horizontal page overflow',p.evaluate('document.documentElement.scrollWidth <= innerWidth'))
            boxes=p.evaluate('''()=>{const a=document.getElementById('woven-canvas').getBoundingClientRect();const b=document.getElementById('woven-browser').getBoundingClientRect();return {bottom:a.bottom,top:b.top}}''')
            check(f'{width}px index is below the drawing',boxes['top']>=boxes['bottom']-2)
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
