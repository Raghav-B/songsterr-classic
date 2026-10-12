"""Exercise the packaged extension without login, real writes, or debugger permission.

Playwright controls the isolated QA browser; the installed extension itself has
no debugger capability. Network interception in this harness only denies writes
and denies archived CDN files. It never supplies frontend bytes to the browser.
"""
import asyncio
import json
import shutil
import tempfile
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

from PIL import Image, ImageChops
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
EXTENSION = ROOT / "artifacts/local-extension"
OUTPUT = ROOT / "artifacts/local-qa"
CHROME = "/home/raghavb/.cache/ms-playwright/chromium-1234/chrome-linux64/chrome"
SONG = "https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439"


async def main():
    OUTPUT.mkdir(exist_ok=True)
    manifest = json.loads((EXTENSION / "manifest.json").read_text())
    assert "debugger" not in manifest["permissions"]
    names = set(json.loads((EXTENSION / "asset-list.json").read_text()))
    names.update(Path(path).name for path in json.loads((EXTENSION / "media-assets.json").read_text()))
    receipt = {"checks": {}, "errors": [], "local_assets": [], "blocked_archive_requests": [], "reads": []}
    profile = tempfile.mkdtemp(prefix="classic-local-qa-")
    classic = False
    async with async_playwright() as playwright:
        context = await playwright.chromium.launch_persistent_context(
            profile, headless=True, executable_path=CHROME, viewport={"width":1440,"height":1000},
            args=["--no-sandbox", "--disable-dev-shm-usage", "--mute-audio", "--disable-extensions-except=" + str(EXTENSION), "--load-extension=" + str(EXTENSION)],
            ignore_default_args=["--disable-extensions"])
        try:
            async def guard(route):
                request = route.request
                url = urlsplit(request.url)
                if request.method not in ("GET", "HEAD", "OPTIONS"):
                    await route.abort()
                elif classic and url.hostname in ("www.songsterr.com", "static3.songsterr.com") and url.path.rsplit("/",1)[-1] in names:
                    receipt["blocked_archive_requests"].append(url.path)
                    await route.abort()
                else:
                    await route.continue_()
            await context.route("**/*", guard)
            def observe(response):
                if not classic:
                    return
                url = urlsplit(response.url)
                if url.scheme == "chrome-extension" and ("/vendor/" in url.path or "/media/" in url.path):
                    receipt["local_assets"].append({"path":url.path,"status":response.status})
                if url.hostname == "www.songsterr.com" and url.path.startswith("/api/"):
                    receipt["reads"].append({"method":response.request.method,"path":url.path,"status":response.status})
            context.on("response", observe)
            worker = context.service_workers[0] if context.service_workers else await context.wait_for_event("serviceworker")
            extension_id = worker.url.split("/")[2]
            page = await context.new_page()
            page.on("pageerror", lambda error: receipt["errors"].append(str(error)))
            await page.goto(SONG, wait_until="domcontentloaded")
            original_user = await page.evaluate("JSON.parse(document.getElementById('state').textContent).user")
            popup = await context.new_page()
            await popup.goto(f"chrome-extension://{extension_id}/popup.html")
            tab = await popup.evaluate("async()=> (await chrome.tabs.query({url:'https://www.songsterr.com/*'}))[0].id")
            classic = True
            receipt["enable"] = await popup.evaluate("id=>chrome.runtime.sendMessage({action:'enable',tabId:id})", tab)
            await page.wait_for_timeout(13000)
            assert await page.evaluate("document.documentElement.dataset.songsterrClassic") == "july-2026"
            assert await page.evaluate("JSON.parse(document.getElementById('state').textContent).user") == original_user
            receipt["checks"]["account_state_unchanged"] = True
            assert await page.evaluate("!!globalThis.songsterrClassicTransport")
            receipt["checks"]["page_adapter_installed"] = True
            print("Local app booted", flush=True)
            await page.locator("#control-mixer").last.click()
            await page.get_by_text('John Frusciante | Gretsch White Falcon | Lead Guitar',exact=True).last.click()
            receipt["checks"]["mixer"] = True
            await page.locator("#control-source").click()
            await page.locator("#control-play").click()
            await page.wait_for_timeout(6000)
            assert await page.locator("#control-play").get_attribute("aria-pressed") == "true"
            assert await page.locator("#control-play").get_attribute("data-can-play") == "true"
            await page.locator("#control-play").click()
            receipt["checks"]["synth_play_pause"] = True
            await page.locator("#control-editor").click()
            await page.locator("#control-import").wait_for()
            await page.wait_for_timeout(3000)
            for _ in range(3):
                dismiss = page.get_by_text("Not now", exact=True)
                if await dismiss.is_visible():
                    await dismiss.click()
                    await page.wait_for_timeout(700)
            receipt["checks"]["editor_open"] = True
            receipt["worker_adapters"] = []
            for score_worker in page.workers:
                receipt["worker_adapters"].append(await score_worker.evaluate("({adapter:!!globalThis.songsterrClassicTransport,origin:location.origin})"))
            assert any(item["adapter"] for item in receipt["worker_adapters"])
            receipt["checks"]["score_worker_adapter_installed"] = True
            # External SVG use cannot cross the extension origin. Assert the
            # actual rendered references, not just successful asset downloads.
            receipt["sprite_uses"] = await page.locator("svg use").evaluate_all("""elements => elements.map(e => {
                const href = e.getAttribute('href') || e.getAttributeNS('http://www.w3.org/1999/xlink','href');
                const box = e.getBBox();
                return {href, visible:e.checkVisibility({visibilityProperty:true}), resolved:href?.startsWith('#') && !!document.getElementById(href.slice(1)), width:box.width,height:box.height};
            })""")
            local_uses = [item for item in receipt["sprite_uses"] if item["href"] and item["href"].startswith("#classic-")]
            assert len(local_uses) > 10
            assert all(item["resolved"] for item in local_uses), "Unresolved local SVG symbol"
            visible_uses = [item for item in local_uses if item["visible"]]
            assert len(visible_uses) > 10, "No visible SVG controls"
            assert all(item["width"] > 0 and item["height"] > 0 for item in visible_uses), "Empty visible SVG geometry"
            assert not any("/static3/media/" in (item["href"] or "") for item in receipt["sprite_uses"])
            receipt["checks"]["bundled_svg_symbols_render"] = True
            # The inspected 1440px screenshot places the first bar's B-string
            # open note here. Exercise actual pointer/keyboard editor input;
            # the server-write guard remains active throughout.
            await page.mouse.click(262, 438)
            await page.mouse.move(1400, 700)
            await page.wait_for_timeout(800)
            note_region = {"x":248,"y":427,"width":30,"height":24}
            before = await page.screenshot(path=str(OUTPUT / "note-before.png"), clip=note_region)
            await page.keyboard.press("7")
            await page.wait_for_timeout(1000)
            after = await page.screenshot(path=str(OUTPUT / "note-after.png"), clip=note_region)
            assert after != before, "Keyboard note entry did not change the rendered note"
            await page.keyboard.press("Control+z")
            await page.wait_for_timeout(1000)
            undone = await page.screenshot(path=str(OUTPUT / "note-undone.png"), clip=note_region)
            # Compare the dark fret glyph, not the orange tutorial halo or the
            # cursor's undo marker. One threshold-edge pixel can vary during
            # rasterization; 0 versus 7 differs in forty pixels in this region.
            glyph = lambda data: Image.open(BytesIO(data)).convert("L").crop((8,4,18,17)).point(lambda value: 255 if value < 100 else 0)
            differences = lambda left, right: sum(value > 0 for value in ImageChops.difference(glyph(left), glyph(right)).getdata())
            assert differences(before, after) > 10, "Fret glyph did not change meaningfully"
            assert differences(before, undone) <= 1, "Undo did not restore the original rendered note"
            await page.keyboard.press("Control+Shift+z")
            await page.wait_for_timeout(1000)
            redone = await page.screenshot(path=str(OUTPUT / "note-redone.png"), clip=note_region)
            assert differences(after, redone) <= 1, "Redo did not restore the changed fret"
            await page.keyboard.press("Control+z")
            await page.wait_for_timeout(700)
            receipt["checks"]["local_note_edit_undo"] = True
            receipt["checks"]["local_note_redo"] = True
            await page.screenshot(path=str(OUTPUT / "editor.png"))
            (OUTPUT / "public-editor.html").write_text(await page.content())
            receipt["editor_controls"] = await page.locator("#control-undo-panel,#control-redo-panel,#control-submitrevision").evaluate_all("es=>es.map(e=>({id:e.id,title:e.title,disabled:e.disabled}))")
            # Identify notation targets for the next edit/undo proof using DOM,
            # not a guessed coordinate over an unseen canvas.
            receipt["notation_elements"] = await page.locator("svg text").evaluate_all("es=>es.slice(0,30).map(e=>({text:e.textContent,html:e.outerHTML.slice(0,250)}))")
            receipt["checks"]["source_location_delay"] = page.url.startswith("https://www.songsterr.com/")
            classic = False
            result = await popup.evaluate("id=>chrome.runtime.sendMessage({action:'disable',tabId:id})",tab)
            assert result == {"enabled":False}
            await page.wait_for_timeout(6000)
            assert await page.evaluate("document.documentElement.dataset.songsterrClassic") is None
            receipt["checks"]["restore_current"] = True
        except Exception as error:
            receipt["failure"] = repr(error)
            await page.screenshot(path=str(OUTPUT / "failure.png"))
        finally:
            await context.close()
    shutil.rmtree(profile)
    (OUTPUT / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"checks":receipt["checks"],"failure":receipt.get("failure"),"local_assets":len(receipt["local_assets"]),"blocked_archive_requests":receipt["blocked_archive_requests"]}), flush=True)
    if "failure" in receipt:
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
