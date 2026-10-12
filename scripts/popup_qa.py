"""Exercise real popup DOM/CSS with a deterministic Chrome API boundary.

No Songsterr writes or personal profile access. local_qa.py separately checks
this same popup against the real extension worker and a public Songsterr tab.
"""
import asyncio
import json
from playwright.async_api import async_playwright
from local_qa import ROOT, CHROME


async def main():
    output = ROOT / "artifacts/popup-qa"
    output.mkdir(exist_ok=True)
    checks = []
    errors = []
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(executable_path=CHROME, headless=True, args=["--no-sandbox"])
        page = await browser.new_page(viewport={"width":360,"height":560}, device_scale_factor=2)
        page.on("pageerror", lambda error: errors.append(str(error)))
        await page.add_init_script("""
            globalThis.popupQA = {enabled:false,legacyPreview:false,fail:false,url:'https://www.songsterr.com/a/wsa/test-tab-s439',calls:[]};
            globalThis.chrome = {
                tabs:{query:async()=>[{id:1,url:popupQA.url}]},
                runtime:{getManifest:()=>({version:'0.3.0'}),sendMessage:async message=>{
                    popupQA.calls.push(message);
                    if(message.action === 'status')return {enabled:popupQA.enabled,legacyPreview:popupQA.legacyPreview};
                    await new Promise(resolve=>setTimeout(resolve,400));
                    if(popupQA.fail)return {error:'Could not reload this tab. Try again.'};
                    popupQA.enabled=message.action==='enable';popupQA.legacyPreview=false;
                    return {enabled:popupQA.enabled,legacyPreview:false};
                }}
            };
        """)
        url = (ROOT / "extension/popup.html").as_uri()
        await page.goto(url)
        switch = page.get_by_role("switch", name="Classic interface")
        await page.locator("body[data-state='off']").wait_for()
        assert await switch.get_attribute("aria-checked") == "false"
        await page.locator("main").screenshot(path=str(output / "off.png"))
        await switch.focus()
        await page.keyboard.press("Space")
        await page.locator("body[data-state='busy']").wait_for()
        assert await switch.is_disabled()
        await page.locator("body[data-state='on']").wait_for()
        await page.wait_for_timeout(650)
        assert await switch.get_attribute("aria-checked") == "true"
        await page.locator("main").screenshot(path=str(output / "on.png"))
        checks.append("Keyboard toggle enables editing; busy state prevents duplicate clicks")
        await switch.click()
        await page.locator("body[data-state='off']").wait_for()
        checks.append("OFF restores current UI state")
        await page.evaluate("popupQA.fail=true")
        await switch.click()
        await page.locator("#error:not([hidden])").wait_for()
        assert await switch.get_attribute("aria-checked") == "false"
        assert await switch.is_enabled()
        await page.locator("main").screenshot(path=str(output / "error.png"))
        checks.append("Failed activation exposes error and preserves the actual switch state")
        await page.evaluate("popupQA.enabled=true;popupQA.legacyPreview=true;popupQA.fail=false;start()")
        assert await switch.get_attribute("aria-checked") == "false"
        assert "Older preview" in await page.locator("#description").inner_text()
        await switch.click()
        await page.locator("body[data-state='on']").wait_for()
        checks.append("Legacy preview requires explicit activation instead of claiming editing is enabled")
        await page.evaluate("popupQA.enabled=false;popupQA.url='https://example.com/';start()")
        assert await switch.is_disabled()
        await page.locator("main").screenshot(path=str(output / "unavailable.png"))
        checks.append("Non-Songsterr tabs cannot toggle")
        await page.evaluate("popupQA.url='https://www.songsterr.com/favorites';popupQA.enabled=true;start()")
        assert await switch.is_enabled()
        checks.append("Classic can be switched off after navigating to My tabs")
        await page.emulate_media(reduced_motion="reduce")
        assert await page.locator(".thumb").evaluate("el=>getComputedStyle(el).transitionDuration") == "0s"
        assert await page.locator(".staff b").evaluate("el=>getComputedStyle(el).animationName") == "none"
        checks.append("Reduced motion disables switch and playhead animations")
        await page.locator("summary").click()
        await page.locator("main").screenshot(path=str(output / "details.png"))
        assert await page.evaluate("document.documentElement.scrollWidth") == 360
        assert not errors, errors
        await browser.close()
    (output / "receipt.json").write_text(json.dumps({"checks":checks,"errors":errors},indent=2)+'\n')
    print(json.dumps(checks),flush=True)


if __name__ == '__main__':
    asyncio.run(main())
