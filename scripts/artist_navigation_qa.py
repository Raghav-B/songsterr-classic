"""Render July's real header while song metadata is still loading.

The public-page fixture clears only song metadata, forcing the fallback that
crashed in the user's console. No login is copied and all writes are denied.
Both packages use the real July modules; only the adapter differs.
"""
import asyncio
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from playwright.async_api import async_playwright
from local_qa import CHROME, ROOT, SONG


async def run_case(playwright, label, extension, html, output):
    """A cold song header must render without the artist-list TypeError."""
    profile = tempfile.mkdtemp(prefix="classic-artist-qa-")
    context = await playwright.chromium.launch_persistent_context(
        profile, executable_path=CHROME, headless=True,
        viewport={"width": 1440, "height": 1000},
        args=["--no-sandbox", "--mute-audio", "--disable-extensions-except=" + str(extension),
              "--load-extension=" + str(extension)],
        ignore_default_args=["--disable-extensions"],
    )
    errors = []
    try:
        async def route_request(route):
            request = route.request
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                await route.abort()
            elif request.is_navigation_request() and request.url == SONG:
                await route.fulfill(status=200, content_type="text/html", body=html)
            elif "/api/meta/" in request.url:
                await route.abort()
            else:
                await route.continue_()

        await context.route("**/*", route_request)
        worker = context.service_workers[0] if context.service_workers else await context.wait_for_event("serviceworker")
        extension_id = worker.url.split("/")[2]
        page = await context.new_page()
        await page.goto(SONG, wait_until="domcontentloaded")
        popup = await context.new_page()
        await popup.goto(f"chrome-extension://{extension_id}/popup.html")
        tab_id = await popup.evaluate("async () => (await chrome.tabs.query({url:'https://www.songsterr.com/*'}))[0].id")
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)
        await popup.evaluate("id => chrome.runtime.sendMessage({action:'enable',tabId:id})", tab_id)
        await page.wait_for_function("document.documentElement.dataset.songsterrClassic === 'july-2026'")
        await page.wait_for_timeout(15000)
        await page.screenshot(path=str(output / f"{label}.png"))
        artist = await page.evaluate("JSON.parse(document.getElementById('state').textContent).artist")
        return {"errors": errors, "artist_list_exists": isinstance(artist["songs"].get("list"), list)}
    finally:
        await context.close()
        shutil.rmtree(profile)


async def main():
    output = ROOT / "artifacts/artist-navigation-qa"
    output.mkdir(exist_ok=True)
    html = subprocess.check_output(["curl", "-fsS", SONG], text=True)
    match = re.search(r'(<script[^>]*id="state"[^>]*>)(.*?)(</script>)', html, re.S)
    state = json.loads(match[2])
    state["meta"]["current"] = None
    state["chords"]["current"] = None
    html = html[:match.start(2)] + json.dumps(state) + html[match.end(2):]
    with tempfile.TemporaryDirectory(prefix="classic-artist-baseline-") as temporary:
        baseline = Path(temporary) / "extension"
        shutil.copytree(ROOT / "artifacts/local-extension", baseline)
        old_adapter = subprocess.check_output(["git", "show", "460ca00:extension/compat.mjs"], cwd=ROOT)
        (baseline / "compat.mjs").write_bytes(old_adapter)
        async with async_playwright() as playwright:
            before = await run_case(playwright, "before", baseline, html, output)
            after = await run_case(playwright, "after", ROOT / "artifacts/local-extension", html, output)
    receipt = {"fixture": "Public song with unloaded meta/chords; metadata reads and all writes denied", "before": before, "after": after}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt), flush=True)
    assert any("reading 'find'" in error for error in before["errors"]), "Baseline did not reproduce"
    assert not any("TypeError" in error for error in after["errors"]), "Fixed header still throws"
    assert after["artist_list_exists"]


if __name__ == "__main__":
    asyncio.run(main())
