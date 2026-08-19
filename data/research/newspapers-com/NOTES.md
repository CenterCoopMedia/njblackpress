# Newspapers.com research notes

Session date: 2026-08-17

**Scope: New Jersey only.** Search location must be New Jersey. Keep only clips printed in New Jersey newspapers. Out-of-state papers (New York Age, Washington Bee, Evening World, New-York Tribune, Baltimore Afro-American) can point us to a fact, but they are not keepers for this archive.

Chrome is left open on the signed-in newspapers.com profile. Playwright must stay attached through `browser_daemon.py`. Do not call `browser.close()` or stop Playwright, or the window dies.

## What newspapers.com actually holds

The paper catalog (`/papers/` + title filter) did not return any NJ Black titles as source publications. The title filter also threw a load error after repeated queries. Treat that as "not held as a paper," not as a final inventory. The useful collection here is **mentions and reprints** in other papers, plus the Baltimore **Afro-American**, which newspapers.com does hold.

Oldest ceased NJ Black papers do not appear to be digitized on newspapers.com as full runs. Chronicling America, Red Bank Public Library, Newark Public Library, and LOC catalog records remain the place to send people for actual issues.

## Download / export on Newspapers.com

The toolbar control is an icon button with `title="Print or Download"` (no visible text). It opens a panel. The left card is Entire Page. The right card is Select portion of page. After Entire Page, the panel offers Print, Save as JPG, and Save as PDF*.

**Solved 2026-08-19.** Playwright `expect_download` and `Page.setDownloadBehavior` never see these files. Use the browser-level CDP session instead:

```python
bsess = browser.new_browser_cdp_session()
bsess.send("Browser.setDownloadBehavior",
           {"behavior": "allowAndName", "downloadPath": DEST, "eventsEnabled": True})
```

Then read the real path from the `Browser.downloadProgress` event with `state == "completed"`. `allowAndName` writes GUID-named files, so that event is the only way to learn the path. Rename after the fact.

The Save as JPG pill is a plain anchor whose href already carries `a=download&width=<full>&height=<full>` plus a signed `iat` JWT; one click is enough. The Save as PDF* pill has no href, is JS-driven, and fires unreliably — click it with a trusted Playwright click and retry up to three times. Do not use Select portion of page; it needs a manual drag.

Full-resolution exports for all 26 keeper pages are in `downloads/` as `<paper-slug>_<YYYY-MM-DD>_p<page>_<clip-slug>.jpg` and `.pdf`. Scans run 2304–3557 px wide and 3532–5160 px tall. Log: `downloads/clean-download-log.json`.

All 138 titles were queried on Newspapers.com (New Jersey card filter on the first page). Results are in `all138.json` and on each catalog row under `sources.newspapers_com`.

## How search has to work

Do not search `"The Sentinel" Trenton`. That returns missile stories. Do not take rank 1. Sort or pick by date and by paper.

Use founder names, exact paper titles in quotes, and contemporary Black papers (New York Age, Washington Bee, Afro-American, Chicago Defender).

Open the on-page "Find text" box and jump to the highlight before you save a screenshot. The viewer lands at the top of the page.

## Saved files

Screenshots of every search and page open live in `data/research/newspapers-com/screenshots/` (128 files). The shareable keeper set is copied into `data/research/newspapers-com/clips/` with a `catalog.json` and `index.html`. Each keeper has a Newspapers.com image URL for sharing now. Next step for embed is to hit Clip on those pages so we get a `/clip/` URL the site can use. Do not dump full page scans onto the public GitHub Pages site until each clip is cropped and cited.

## Verified clips

| What | Source | Date | URL | Why it matters |
| --- | --- | --- | --- | --- |
| R. Henri Herbert profile | New-York Tribune, p. 14 | 1895-12-08 | https://www.newspapers.com/image/78953914/ | Calls him a noted colored leader of Mercer County; credits him with unifying Black Republican voters |
| Herbert obituary | New York Age, p. 1 | 1909-10-21 | https://www.newspapers.com/image/33451515/ | "R. Henri Herbert dies suddenly / Found dead in middle of street in Trenton." Document clerk at the State House |
| Trumpet as Negro organ | Evening World, p. 2 | 1888-12-11 | https://www.newspapers.com/image/50663302/ | Reprint line "From the New Jersey Trumpet—Negro Organ" and "A roaring Jersey Negro editor" |
| Murrell as Trumpet editor | Washington Bee, p. 2 | 1889-05-18 | https://www.newspapers.com/image/46319440/ | "Col. Wm. Murrell editor of the New Jersey Trumpet" received a commission |
| Murrell speaking | Asbury Park Press, p. 1 | 1893-07-22 | https://www.newspapers.com/image/436760060/ | "Colonel Murrell, editor of the New Jersey Trumpet" spoke on the colored question at a beach/pavilion meeting |
| Red Bank Echo cited | New York Age, p. 4 | 1921-04-09 | https://www.newspapers.com/image/39621583/ | "The Red Bank Echo" treated as a peer Black paper |
| Newark Herald folded | Afro-American, p. 7 | 1932-07-09 | https://www.newspapers.com/image/1134167020/ | "Jersey's only colored weekly has ceased publication." Editor Clark; Cotton Building; more than four years old; hope of resumption |
| Echo burned out | Monmouth Democrat (Freehold), p. 4 | 1904-09-08 | https://www.newspapers.com/image/497174278/ | "Weekly negro newspaper" at Long Branch; fire thought incendiary; first issue edited by Rock & Howard |
| Echo moves to Red Bank | Asbury Park Press, p. 2 | 1909-03-05 | https://www.newspapers.com/image/143869436/ | W. E. Rock edited it in Long Branch five years, then bought a home in Red Bank |
| Herbert vs Bradley | Trenton Sunday Advertiser, p. 1 | 1893-11-05 | https://www.newspapers.com/image/1194114727/ | Herbert asks "colored fellow-citizens" to defeat Founder Bradley over the Asbury Park pavilion ban |
| Herbert on GOP committee | Trenton Sunday Advertiser, p. 1 | 1895-10-20 | https://www.newspapers.com/image/1194116748/ | Appointed consulting member of the Republican State Committee |
| Murrell at Asbury meeting | Shore Press, p. 6 | 1893-07-28 | https://www.newspapers.com/image/436807841/ | Editor of the Trumpet on the platform against Bradley's pavilion signs |
| NJ Afro-American described | Daily Record (Morristown), p. D2 | 2023-05-21 | https://www.newspapers.com/image/962761544/ | Newark edition of the Baltimore Afro-American chain; 1947 masthead photo; "the New Jersey edition no longer exists" |
| The Landscape / Alfred P. Smith | Ridgewood News, p. 14 | 1987-11-26 | https://www.newspapers.com/image/1122504536/ | First title A.P. Smith's Paper; May 1881–July 1901; East Allendale Road |
| The Landscape renamed | The Record (Hackensack), p. 2 | 1991-02-09 | https://www.newspapers.com/image/496517756/ | 1881 start; most subscribers white; Smith wrote Lincoln in 1862 |
| Smallest newspaper | Sunday News (Ridgewood), p. 2 | 1993-06-27 | https://www.newspapers.com/image/634766635/ | Four pages, 6 x 8 inches |
| New Jersey Guardian cited | The News (Paterson), p. 9 | 1939-09-09 | https://www.newspapers.com/image/525697398/ | "journal for colored readers which has state-wide circulation" |
| Melvin B. Johnson left papers | Star-Ledger, p. 14 | 1949-01-19 | https://www.newspapers.com/image/1108232407/ | Former Negro newspaper publisher and editor until 1946 |
| Johnson at Montclair and Newark | Asbury Park Press, p. 2 | 1949-11-06 | https://www.newspapers.com/image/143065742/ | Former editor and publisher of weekly newspapers at Montclair and Newark |
| Ironsides Echo award | Courier-Post, p. 14 | 1932-03-22 | https://www.newspapers.com/image/446292432/ | Monthly student paper; second place Columbia; student editor Leon Snead |
| Ironsides Echo awards | Trenton Times, p. 13 | 1940-05-07 | https://www.newspapers.com/image/1191434889/ | Two second-place Columbia awards; adviser Frances O. Grant; printer L. J. Roberts |
| Harry B. Webber / After Hours | Courier-News, p. 8 | 1991-06-24 | https://www.newspapers.com/image/223216862/ | AP obit: city editor of NJ Herald News; editor-publisher of After Hours in the 1940s |
| Camp Cooper paper | Courier-Post, p. 3 | 1936-01-06 | https://www.newspapers.com/image/447571125/ | CCC Company 1275 at Erlton; journalism class turns out Camp Cooper regularly |

Danky and Hady 1998 keepers (IA `africanamericanne00dank`, local files in `data/research/danky/`): Apex News p.46; Camden News / Camp Berlin Broadcast / Camp Cooper Chats p.131; The Citizen p.154; Hiram Star-News p.277; North Jersey Independent p.430; Club World p.158; Nite Lite p.427; Liberator (Edison) p.336.

| Bronze Thrills July issue | Asbury Park Press, p. 21 | 1960-05-20 | https://www.newspapers.com/image/143086953/ | Lakewood column: life story set for the July issue of Bronze Thrills |

Screenshots live in `data/research/newspapers-com/screenshots/` as `match-*.png` and `keeper-*.png`.

## Data changes this session

The Sentinel record had `yearCeased: null` and `isActive: true` even though the notes already say it ran 1880-1882. That is now corrected.

New Jersey Afro-American notes already said it ran through 1991, but `yearCeased` was null. That is now 1991.

Newark Herald (1928) keeps 1939 as the catalog end date because Vol. 11, no. 18 (June 11, 1938) implies the title came back or never fully died. The 1932 Afro-American fold notice is now in the historical notes.

## Trends

The database is 138 titles. Newark accounts for 40. Next are Paramus (10), Trenton (9), then Atlantic City, Plainfield, East Orange, and New Brunswick (5 each). That is one metro core, one capital city, and a later Bergen magazine cluster, not an even statewide press.

Foundings come in three different businesses. The 1880s give three pioneer weeklies (Sentinel, Landscape, Trumpet). The 1930s jump to 14 titles, many of them CCC camp papers plus the Guardian and Herald News. The 1970s are the peak at 30, after Newark 1967, with political and campus papers. The 1980s–90s add 46 more, a lot of them Paramus/River Edge entertainment magazines (Word Up, Hype, Right On!), which are Black-audience periodicals printed in New Jersey, not local civic weeklies. Digital titles show up in the 2010s–20s.

Closures cluster too: 8 in the 1930s, 6 in the 1940s, 6 in the 1970s, 8 in the 1990s. The 1932 Afro-American report that the Newark Herald had folded fits that 1930s die-off. Many pre-1970 titles still have no cease year, so the official 97 “active” count is too high.

New Jersey white dailies notice the Black press in a few repeating situations. The editor becomes a political actor (Herbert in Trenton, Murrell speaking in Asbury Park). A paper dies and the loss is treated as statewide. A later commemorative piece names the founder (the 1948 Trenton Times “R. Henri Herbert Ball Team”). The papers that keep showing up are the Trenton Times / Sunday Advertiser, Asbury Park Press / Shore Press, and the Jersey Journal / Jersey City News.

The sidebar “New Jersey” control on newspapers.com reports hundreds of in-state hits (Herbert 396, Trumpet 262, Murrell 85, Afro-American 433) but does not reliably rewrite the result list. Filter by reading the city line on each card. Do not trust a click on the count label.

## Still to do

Open Baltimore Afro-American pages from 1941-1955 and walk the on-page matches for "New Jersey Afro-American." Some of those may be the Newark edition, not just mentions.

Search `W. E. Rock` and `"The Echo" "Long Branch"` with a 1904-1910 date cap.

Use the Clip button on the verified pages so they land in the paid My Clippings folder.

Sort remaining searches by oldest date, not relevance.

Do not use the paper-catalog titleKeyword endpoint until it stops returning a load error.
