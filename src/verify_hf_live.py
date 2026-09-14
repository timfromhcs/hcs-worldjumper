import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

CHROME_PATH = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
LIVE_URL = "https://timfromhcs-hcs-worldjumper.static.hf.space/index.html"
OUT_DIR = os.path.abspath("artifacts/deployment")
os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs("reports", exist_ok=True)

class CDPClient:
    def __init__(self, ws):
        self.ws = ws
        self.id = 0
        self.pending = {}
        self.events = []
        self.logs = []
        self.network = []

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
                        print(f"[LIVE CONSOLE] {entry}")
                    elif data["method"] == "Runtime.exceptionThrown":
                        exc = data["params"]["exceptionDetails"]
                        entry = f"[EXCEPTION] {exc.get('text')} {exc.get('exception', {}).get('description', '')}"
                        self.logs.append(entry)
                        print(f"[LIVE EXC] {entry}")
                    elif data["method"] == "Network.responseReceived":
                        resp = data["params"]["response"]
                        self.network.append({
                            "url": resp["url"],
                            "status": resp["status"],
                            "mimeType": resp["mimeType"]
                        })
        except asyncio.CancelledError:
            pass

async def main():
    print("=== TESTING LIVE HUGGING FACE STATIC SPACE DEPLOYMENT ===")
    user_data = os.path.join(os.environ.get("TEMP", "C:/Temp"), "chrome_cdp_live")
    proc = subprocess.Popen([
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9223",
        f"--user-data-dir={user_data}",
        "--disable-gpu-sandbox",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--window-size=1280,720",
        "about:blank"
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(2)

    matrix = {
        "verified_at": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "deployment_url": LIVE_URL,
        "environment": "Hugging Face Static Space",
        "tests": {}
    }

    try:
        tabs_res = urllib.request.urlopen("http://localhost:9223/json")
        tabs = json.loads(tabs_res.read().decode("utf-8"))
        pages = [t for t in tabs if t.get("type") == "page"]
        ws_url = pages[0]["webSocketDebuggerUrl"]
        print(f"Connected to Chrome page: {ws_url}")

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            client = CDPClient(ws)
            task = asyncio.create_task(client.listener())

            await client.send("Page.enable")
            await client.send("Runtime.enable")
            await client.send("Network.enable")

            # TEST 1: Main Menu
            print("\n[TEST 1] Loading Main Menu from Hugging Face...")
            await client.send("Page.navigate", {"url": LIVE_URL})
            await asyncio.sleep(4)

            s_menu = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_live_menu.png"), "wb") as f:
                f.write(base64.b64decode(s_menu["result"]["data"]))
            print("Saved artifacts/deployment/hf_live_menu.png")

            eval1 = await client.send("Runtime.evaluate", {
                "expression": "({ hasApp: Boolean(window.HCS_APP), backend: window.HCS_APP ? window.HCS_APP.backendName : null, title: document.title, uiRoot: Boolean(document.getElementById('ui-root')) })",
                "returnByValue": True
            })
            res_menu = eval1.get("result", {}).get("result", {}).get("value", {})
            print("Menu State:", res_menu)
            matrix["tests"]["main_menu"] = {
                "status": "PASS" if res_menu.get("hasApp") and res_menu.get("uiRoot") else "FAIL",
                "backend": res_menu.get("backend"),
                "title": res_menu.get("title")
            }

            # TEST 2: World Selector
            print("\n[TEST 2] Loading World Selector...")
            await client.send("Page.navigate", {"url": f"{LIVE_URL}?screen=world_selector"})
            await asyncio.sleep(3)

            s_sel = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_live_selector.png"), "wb") as f:
                f.write(base64.b64decode(s_sel["result"]["data"]))
            print("Saved artifacts/deployment/hf_live_selector.png")

            eval2 = await client.send("Runtime.evaluate", {
                "expression": "({ cards: document.querySelectorAll('.map-card').length, titles: Array.from(document.querySelectorAll('.card-title')).map(e => e.innerText) })",
                "returnByValue": True
            })
            res_sel = eval2.get("result", {}).get("result", {}).get("value", {})
            print("Selector State:", res_sel)
            matrix["tests"]["world_selector"] = {
                "status": "PASS" if res_sel.get("cards") == 3 else "FAIL",
                "cards_count": res_sel.get("cards"),
                "maps": res_sel.get("titles")
            }

            # TEST 3: Map 1 (District Alpha)
            print("\n[TEST 3] Loading Map 1 (map)...")
            await client.send("Page.navigate", {"url": f"{LIVE_URL}?model=map"})
            await asyncio.sleep(6)

            s_map1 = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_live_map1.png"), "wb") as f:
                f.write(base64.b64decode(s_map1["result"]["data"]))
            print("Saved artifacts/deployment/hf_live_map1.png")

            eval_map1 = await client.send("Runtime.evaluate", {
                "expression": "({ colliders: window.HCS_APP ? window.HCS_APP.colliders.length : 0, pos: window.HCS_APP ? window.HCS_APP.controller.position : null, fps: window.HCS_APP ? window.HCS_APP.currentFps : 0 })",
                "returnByValue": True
            })
            res_map1 = eval_map1.get("result", {}).get("result", {}).get("value", {})
            print("Map 1 State:", res_map1)
            matrix["tests"]["map1_district_alpha"] = {
                "status": "PASS" if res_map1.get("colliders", 0) > 1000 else "FAIL",
                "colliders": res_map1.get("colliders"),
                "position": res_map1.get("pos"),
                "fps": res_map1.get("fps")
            }

            # TEST 4: Map 2 (Highland Valley)
            print("\n[TEST 4] Loading Map 2 (map2)...")
            await client.send("Page.navigate", {"url": f"{LIVE_URL}?model=map2"})
            await asyncio.sleep(6)

            s_map2 = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_live_map2.png"), "wb") as f:
                f.write(base64.b64decode(s_map2["result"]["data"]))
            print("Saved artifacts/deployment/hf_live_map2.png")

            eval_map2 = await client.send("Runtime.evaluate", {
                "expression": "({ colliders: window.HCS_APP ? window.HCS_APP.colliders.length : 0, pos: window.HCS_APP ? window.HCS_APP.controller.position : null, fps: window.HCS_APP ? window.HCS_APP.currentFps : 0 })",
                "returnByValue": True
            })
            res_map2 = eval_map2.get("result", {}).get("result", {}).get("value", {})
            print("Map 2 State:", res_map2)
            matrix["tests"]["map2_highland_valley"] = {
                "status": "PASS" if res_map2.get("colliders", 0) > 1000 else "FAIL",
                "colliders": res_map2.get("colliders"),
                "position": res_map2.get("pos"),
                "fps": res_map2.get("fps")
            }

            # TEST 5: Map 3 (Oakridge Academy)
            print("\n[TEST 5] Loading Map 3 (schoolmap)...")
            await client.send("Page.navigate", {"url": f"{LIVE_URL}?model=schoolmap"})
            await asyncio.sleep(6)

            s_map3 = await client.send("Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(OUT_DIR, "hf_live_schoolmap.png"), "wb") as f:
                f.write(base64.b64decode(s_map3["result"]["data"]))
            print("Saved artifacts/deployment/hf_live_schoolmap.png")

            eval_map3 = await client.send("Runtime.evaluate", {
                "expression": "({ colliders: window.HCS_APP ? window.HCS_APP.colliders.length : 0, pos: window.HCS_APP ? window.HCS_APP.controller.position : null, fps: window.HCS_APP ? window.HCS_APP.currentFps : 0 })",
                "returnByValue": True
            })
            res_map3 = eval_map3.get("result", {}).get("result", {}).get("value", {})
            print("Map 3 State:", res_map3)
            matrix["tests"]["map3_oakridge_academy"] = {
                "status": "PASS" if res_map3.get("colliders", 0) > 1000 else "FAIL",
                "colliders": res_map3.get("colliders"),
                "position": res_map3.get("pos"),
                "fps": res_map3.get("fps")
            }

            # Save logs and network report
            with open(os.path.join(OUT_DIR, "hf_live_console.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(client.logs))

            with open(os.path.join(OUT_DIR, "hf_live_network_report.json"), "w", encoding="utf-8") as f:
                json.dump(client.network, f, indent=2)

            with open("reports/hf_deployment_matrix.json", "w", encoding="utf-8") as f:
                json.dump(matrix, f, indent=2)

            print("\n=== VERIFICATION COMPLETE: ALL 5 LIVE QUALITY GATES EVALUATED ===")
            task.cancel()

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(main())
