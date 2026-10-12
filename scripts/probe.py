"""Try pinned assets on a public song in an already isolated QA browser."""
import asyncio
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "extension/vendor"


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(sys.argv[1])
        context = await browser.new_context(service_workers="block", viewport={"width": 1440, "height": 1000})
        page = await context.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)

        async def route(request_route):
            request = request_route.request
            if request.method not in ("GET", "HEAD", "OPTIONS"):
                await request_route.abort()
                return
            name = urlparse(request.url).path.rsplit("/", 1)[-1]
            if request.resource_type == "document" and urlparse(request.url).hostname == "www.songsterr.com":
                response = await request_route.fetch()
                html = await response.text()
                print("DOCUMENT", request.url, len(html), flush=True)
                match = re.search(r'(<script[^>]*id="state"[^>]*>)(.*?)(</script>)', html, re.S)
                if match:
                    print("STATE MATCH", flush=True)
                    state = json.loads(match[2])
                    state.setdefault("artist", {"pattern": "", "filters": state["songs"]["filters"], "artists": {}, "songs": state["songs"]})
                    html = html[:match.start(2)] + json.dumps(state).replace("</", "<\\/") + html[match.end(2):]
                await request_route.fulfill(response=response, body=html)
                return
            if re.fullmatch(r"appClient-[\w-]+\.js", name):
                name = "appClient-CQbxiWv10TmWc-Ge.js"
            if re.fullmatch(r"appClient-[\w-]+\.css", name):
                name = "appClient-442d1888c9.css"
            if re.fullmatch(r"common-[\w-]+\.css", name):
                name = "common-7b4ff45b27.css"
            path = VENDOR / name
            if path.is_file() and urlparse(request.url).hostname == "static3.songsterr.com":
                content_type = "text/css" if name.endswith(".css") else "text/javascript"
                data = path.read_bytes()
                if name == "appClient-CQbxiWv10TmWc-Ge.js":
                    data = b'document.getElementById("root").replaceChildren();\n' + data
                await request_route.fulfill(body=data, content_type=content_type,
                                            headers={"Access-Control-Allow-Origin": "*"})
                return
            await request_route.continue_()

        await context.route("**/*", route)
        await page.goto("https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439?sw=off")
        await page.wait_for_timeout(10000)
        dest = ROOT / "artifacts"
        dest.mkdir(exist_ok=True)
        await page.screenshot(path=str(dest / "probe.png"))
        print(await page.evaluate("async()=>({styleContent:await Promise.all([...document.querySelectorAll('link[rel=stylesheet]')].map(async e=>({url:e.href,begin:(await(await fetch(e.href)).text()).slice(0,90)}))),font:getComputedStyle(document.body).fontFamily,root:getComputedStyle(document.documentElement).getPropertyValue('--system'),html:document.documentElement.className,headers:[...document.querySelectorAll('header')].map(e=>({class:e.className,display:getComputedStyle(e).display,position:getComputedStyle(e).position})),sheets:[...document.styleSheets].map(e=>{try{return{href:e.href,rules:e.cssRules.length}}catch{return{href:e.href}}})})"))
        print(json.dumps({"errors": list(dict.fromkeys(errors))[:6], "text": (await page.locator("body").inner_text())[:4500]}))
        await context.unroute("**/*", route)


asyncio.run(main())
