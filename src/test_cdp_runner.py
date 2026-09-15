import asyncio
import json
import os
import subprocess
import time
import urllib.request
import websockets
import base64

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL_BASE = "http://localhost:4173"
OUT_DIR = os.path.abspath("artifacts/deployment")

class CDPClient:
    def __init__(self, ws):
        self.ws = ws
        self.id = 0
        self.pending = {}
        self.events = []
        self.logs = []

    async def send(self, method, params=None):
        self.id += 1
        req_id = self.id
        fut = asyncio.get_event_loop().create_future()
        self.pending[req_id] = fut
        req = {"id": req_id, "method": method, "params": params or {}}
        await self.ws.send(json.dumps(req))
        return await fut

    async def listener(self):
        try:
            async for raw in self.ws:
                data = json.loads(raw)
                if "id" in data and data["id"] in self.pending:
                    self.pending.pop(data["id"]).set_result(data)
                elif "method" in data:
                    self.events.append(data)
                    if data["method"] == "Runtime.consoleAPICalled":
                        args = [a.get("value", a.get("description", "")) for a in data["params"]["args"]]
                        entry = f"[{data['params']['type'].upper()}] {' '.join(str(x) for x in args)}"
                        self.logs.append(entry)
                        print(f"CONSOLE: {entry}")
                    elif data["method"] == "Runtime.exceptionThrown":
                        exc = data["params"]["exceptionDetails"]
                        entry = f"[EXCEPTION] {exc.get('text')} {exc.get('exception', {}).get('description', '')}"
                        self.logs.append(entry)
                        print(f"EXCEPTION: {entry}")
        except asyncio.CancelledError:
            pass

async def main():
    user_data = os.path.join(os.environ.get("TEMP", "C:/Temp"), "chrome_cdp_run")
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data}",
        "--disable-gpu-sandbox",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--window-size=1280,720",
        "about:blank"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)

    try:
        tabs_res = urllib.request.urlopen("http://localhost:9222/json")
        tabs = json.loads(tabs_res.read().decode("utf-8"))
        pages = [t for t in tabs if t.get("type") == "page"]
        if not pages:
            raise RuntimeError("No page tab found in Chrome targets!")
        ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"Connecting to target page: {pages[0]['id']} -> {ws_url}", flush=True)

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            client = CDPClient(ws)
            task = asyncio.create_task(client.listener())

            await client.send("Page.enable")
            await client.send("Runtime.enable")
            await client.send("Network.enable")

            # 1. Navigate to main page
            print("\nNavigating to http://localhost:8080/ ...")
            nav_res = await client.send("Page.navigate", {"url": "http://localhost:8080/"})
            print("Navigate response:", nav_res)

            # Wait for DOM and scripts to load
            await asyncio.sleep(4)

            # Capture menu screenshot
            s_menu = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_main_menu.png"), "wb") as f:
                f.write(base64.b64decode(s_menu["result"]["data"]))
            print("Saved hf_main_menu.png")

            # Evaluate state
            eval1 = await client.send("Runtime.evaluate", {
                "expression": "({ hasApp: Boolean(window.HCS_APP), backend: window.HCS_APP ? window.HCS_APP.backendName : null, title: document.title, htmlLen: document.body.innerHTML.length, uiRoot: Boolean(document.getElementById('ui-root')) })",
                "returnByValue": True
            })
            print("Menu eval:", eval1.get("result", {}).get("result", {}).get("value"))

            # 2. Navigate to World Selector
            print("\nNavigating to World Selector...")
            await client.send("Page.navigate", {"url": "http://localhost:8080/?screen=world_selector"})
            await asyncio.sleep(3)

            s_sel = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_world_selector.png"), "wb") as f:
                f.write(base64.b64decode(s_sel["result"]["data"]))
            print("Saved hf_world_selector.png")

            eval2 = await client.send("Runtime.evaluate", {
                "expression": "({ cardCount: document.querySelectorAll('.map-card').length, titles: Array.from(document.querySelectorAll('.card-title')).map(e => e.innerText) })",
                "returnByValue": True
            })
            print("Selector eval:", eval2.get("result", {}).get("result", {}).get("value"))

            # 3. Load Map 1
            print("\nNavigating to Map 1 (District Alpha)...")
            await client.send("Page.navigate", {"url": "http://localhost:8080/?model=map"})
            await asyncio.sleep(5)

            s_map1 = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_map1_gameplay.png"), "wb") as f:
                f.write(base64.b64decode(s_map1["result"]["data"]))
            print("Saved hf_map1_gameplay.png")

            eval3 = await client.send("Runtime.evaluate", {
                "expression": "({ colliders: window.HCS_APP ? window.HCS_APP.colliders.length : 0, fps: window.HCS_APP ? window.HCS_APP.currentFps : 0, pos: window.HCS_APP ? window.HCS_APP.controller.position : null })",
                "returnByValue": True
            })
            print("Map 1 eval:", eval3.get("result", {}).get("result", {}).get("value"))

            # Save console logs
            with open(os.path.join(OUT_DIR, "hf_local_console.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(client.logs))

            task.cancel()

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
