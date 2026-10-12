"""Replay Firefox against a fresh Selenium session inside the isolated desktop.

Requires Selenium, Pillow, and a geckodriver server with --allow-system-access.
The caller owns the fresh profile/display; never attach a personal session.
A temporary companion addon blocks writes and actual archived-CDN downloads.
It is removed at the end so the testing browser is not left secretly read-only.
"""
import argparse
import json
import time
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support.ui import WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
ADDON = "songsterr-classic@raghavbhardwaj.com"
GUARD = "classic-qa-guard@localhost"
SONG = "https://www.songsterr.com/a/wsa/red-hot-chili-peppers-californication-tab-s439"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--webdriver", default="http://127.0.0.1:4447")
    parser.add_argument("--session-file", type=Path, required=True)
    args = parser.parse_args()
    saved = json.loads(args.session_file.read_text())

    class Attached(webdriver.Remote):
        def start_session(self, capabilities):
            self.session_id = saved["sessionId"]
            self.caps = saved["capabilities"]

    driver = Attached(args.webdriver, options=Options())
    driver.command_executor._commands.update({
        "SET_CONTEXT": ("POST", "/session/$sessionId/moz/context"),
        "INSTALL_ADDON": ("POST", "/session/$sessionId/moz/addon/install"),
        "UNINSTALL_ADDON": ("POST", "/session/$sessionId/moz/addon/uninstall"),
    })
    output = ROOT / "artifacts/firefox-qa"
    output.mkdir(exist_ok=True)
    guard = output / "guard"
    guard.mkdir(exist_ok=True)
    assets = json.loads((ROOT / "extension/asset-list.json").read_text())
    media = json.loads((ROOT / "artifacts/local-extension/media-assets.json").read_text())
    assets += [path.rsplit("/", 1)[-1] for path in media]
    (guard / "manifest.json").write_text(json.dumps({
        "manifest_version": 2, "name": "Classic QA network guard", "version": "1.0",
        "browser_specific_settings": {"gecko": {"id": GUARD}},
        "permissions": ["webRequest", "webRequestBlocking", "https://*.songsterr.com/*"],
        "background": {"scripts": ["guard.js"]},
    }))
    (guard / "guard.js").write_text("const assets=new Set(" + json.dumps(assets) + ");\n" + """
browser.webRequest.onBeforeRequest.addListener(request => {
    if (!["GET", "HEAD", "OPTIONS"].includes(request.method)) return {cancel:true};
}, {urls:["https://*.songsterr.com/*"]}, ["blocking"]);
// DNR may redirect to local bytes first. Cancel only requests still headed
// to the archived CDN at the point where HTTP headers would be sent.
browser.webRequest.onBeforeSendHeaders.addListener(request => {
    if (assets.has(new URL(request.url).pathname.split('/').pop())) return {cancel:true};
}, {urls:["https://*.songsterr.com/*"]}, ["blocking"]);
""")
    driver.execute("INSTALL_ADDON", {"path": str(guard), "temporary": True})
    checks = []
    popup = None
    song = None
    wait = WebDriverWait(driver, 20)

    def chrome_script(script):
        driver.execute("SET_CONTEXT", {"context": "chrome"})
        try:
            return driver.execute_script(script, ADDON)
        finally:
            driver.execute("SET_CONTEXT", {"context": "content"})

    def click(identifier):
        wait.until(lambda d: any(e.is_displayed() for e in d.find_elements(By.ID, identifier)))
        [e for e in driver.find_elements(By.ID, identifier) if e.is_displayed()][-1].click()

    def snapshot(name):
        data = driver.get_screenshot_as_png()
        (output / (name + ".png")).write_bytes(data)
        # Compare only the inspected fret glyph, not the animated tutorial halo.
        return Image.open(BytesIO(data)).crop((259, 432, 269, 447)).convert("RGB")

    try:
        driver.switch_to.new_window("tab")
        song = driver.current_window_handle
        driver.get(SONG)
        assert driver.execute_script("return innerWidth") == 1920
        original_user = driver.execute_script("return JSON.parse(document.getElementById('state').textContent).user")
        assert not driver.execute_script("return document.documentElement.dataset.songsterrClassic")
        handles = set(driver.window_handles)
        chrome_script("""
const policy = WebExtensionPolicy.getByID(arguments[0]);
gBrowser.addTab(policy.getURL('/popup.html'), {
    triggeringPrincipal: Services.scriptSecurityManager.getSystemPrincipal(), inBackground: true
});
""")
        # Let the popup resolve the still-active song tab before focusing it.
        time.sleep(1)
        popup = (set(driver.window_handles) - handles).pop()
        driver.switch_to.window(popup)
        wait.until(lambda d: d.find_element(By.TAG_NAME, "body").get_attribute("data-state") == "off")
        click("toggle")
        wait.until(lambda d: d.find_element(By.TAG_NAME, "body").get_attribute("data-state") == "on")
        driver.switch_to.window(song)
        wait.until(lambda d: d.execute_script("return document.documentElement?.dataset.songsterrClassic") == "july-2026")
        wait.until(lambda d: d.execute_script("return !!globalThis.songsterrClassicTransport"))
        assert driver.execute_script("return JSON.parse(document.getElementById('state').textContent).user") == original_user
        checks.append("Packaged Classic boot and page adapter; account bootstrap unchanged")
        click("control-mixer")
        [e for e in driver.find_elements(By.XPATH, "//*[text()='John Frusciante | Gretsch White Falcon | Lead Guitar']") if e.is_displayed()][-1].click()
        click("control-source")
        click("control-play")
        time.sleep(6)
        assert driver.find_element(By.ID, "control-play").get_attribute("aria-pressed") == "true"
        assert driver.find_element(By.ID, "control-play").get_attribute("data-can-play") == "true"
        click("control-play")
        checks.append("Mixer selection and synth play/pause")
        click("control-editor")
        wait.until(lambda d: any(e.is_displayed() for e in d.find_elements(By.ID, "control-import")))
        for _ in range(3):
            for element in driver.find_elements(By.XPATH, "//*[text()='Not now']"):
                if element.is_displayed():
                    element.click()
                    time.sleep(.5)
        # Pointer and keyboard events exercise the actual score-worker editor.
        driver.execute_script("window.scrollTo(0,0)")
        from selenium.webdriver.common.actions.action_builder import ActionBuilder
        actions = ActionBuilder(driver)
        actions.pointer_action.move_to_location(264, 438)
        actions.pointer_action.click()
        actions.perform()
        time.sleep(.6)
        before = snapshot("note-before")
        ActionChains(driver).send_keys("7").perform()
        time.sleep(1)
        after = snapshot("note-after")
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("z").key_up(Keys.CONTROL).perform()
        time.sleep(1)
        undone = snapshot("note-undone")
        differences = lambda a, b: sum(any(pixel) for pixel in ImageChops.difference(a, b).get_flattened_data())
        assert differences(before, after) > 10, "Note did not visibly change"
        assert differences(before, undone) <= 1, "Undo did not restore the fret"
        ActionChains(driver).key_down(Keys.CONTROL).key_down(Keys.SHIFT).send_keys("z").key_up(Keys.SHIFT).key_up(Keys.CONTROL).perform()
        time.sleep(1)
        redone = snapshot("note-redone")
        assert differences(after, redone) <= 1, "Redo did not restore the changed fret"
        ActionChains(driver).key_down(Keys.CONTROL).send_keys("z").key_up(Keys.CONTROL).perform()
        checks.append("Local 0-to-7 note entry, exact visual undo and redo; server writes blocked")
        driver.switch_to.window(popup)
        click("toggle")
        wait.until(lambda d: d.find_element(By.TAG_NAME, "body").get_attribute("data-state") == "off")
        driver.switch_to.window(song)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
        wait.until(lambda d: not d.execute_script("return document.documentElement?.dataset.songsterrClassic"))
        checks.append("OFF restores current UI")
        driver.switch_to.window(popup)
        click("toggle")
        wait.until(lambda d: d.find_element(By.TAG_NAME, "body").get_attribute("data-state") == "on")
        driver.switch_to.window(song)
        wait.until(lambda d: d.execute_script("return document.documentElement?.dataset.songsterrClassic") == "july-2026")
        checks.append("Repeat activation succeeds")
    finally:
        driver.execute("UNINSTALL_ADDON", {"id": GUARD})
        if popup:
            driver.switch_to.window(popup)
            driver.close()
        if song:
            driver.switch_to.window(song)
            driver.get(SONG)
        (output / "receipt.json").write_text(json.dumps({"checks": checks, "guard_removed": True}, indent=2) + "\n")
    print(json.dumps(checks))


if __name__ == "__main__":
    main()
