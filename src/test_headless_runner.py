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
os.makedirs(OUT_DIR, exist_ok=True)

async def run_test():
    # 1. Launch Chrome
    user_data_dir = os.path.join(os.environ.get("TEMP", "C:/Temp"), "chrome_cdp_test")
    cmd = [
        CHROME_PATH,
        "--headless=new",
        "--remote-debugging-port=9222",
        f"--user-data-dir={user_data_dir}",
        "--disable-gpu-sandbox",
        "--enable-webgl",
        "--ignore-gpu-blocklist",
        "--window-size=1280,720",
        "about:blank"
    ]
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    time.sleep(1.5)

    try:
        # Get websocket debugger URL
        tabs_res = urllib.request.urlopen("http://localhost:9222/json")
        tabs = json.loads(tabs_res.read().decode("utf-8"))
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        print(f"Connected to Chrome CDP: {ws_url}")

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            msg_id = 0
            async def send(method, params=None):
                nonlocal msg_id
                msg_id += 1
                req = {"id": msg_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(req))
                return msg_id

            logs = []
            network_events = []

            # Enable domains
            await send("Page.enable")
            await send("Runtime.enable")
            await send("Log.enable")
            await send("Network.enable")

            screenshots = {}
            eval_results = {}

            # Listener loop in background
            async def listen():
                try:
                    async for raw in ws:
                        data = json.loads(raw)
                        mid = data.get("id")
                        if mid in req_map:
                            rtype = req_map[mid]
                            if rtype.startswith("ss_"):
                                screenshots[rtype] = data.get("result", {}).get("data")
                            elif rtype.startswith("eval_"):
                                eval_results[rtype] = data.get("result", {}).get("result", {}).get("value")
                        if data.get("method") == "Runtime.consoleAPICalled":
                            args = [a.get("value", a.get("description", "")) for a in data["params"]["args"]]
                            entry = f"[{data['params']['type'].upper()}] {' '.join(str(x) for x in args)}"
                            logs.append(entry)
                            print(f"[CONSOLE] {entry}")
                        elif data.get("method") == "Runtime.exceptionThrown":
                            exc = data["params"]["exceptionDetails"]
                            entry = f"[EXCEPTION] {exc.get('text')} {exc.get('exception', {}).get('description', '')}"
                            logs.append(entry)
                            print(f"[EXC] {entry}")
                        elif data.get("method") == "Network.responseReceived":
                            resp = data["params"]["response"]
                            network_events.append({
                                "url": resp["url"],
                                "status": resp["status"],
                                "mimeType": resp["mimeType"]
                            })
                except asyncio.CancelledError:
                    pass
                except Exception as e:
                    print("Listener error:", e)

            req_map = {}
            listener_task = asyncio.create_task(listen())

            # Navigate to Main Menu
            print("\n--- TEST 1: Loading Main Menu ---")
            await send("Page.navigate", {"url": f"{URL_BASE}/"})
            await asyncio.sleep(2.5)

            # Capture Screenshot 1
            s1_id = await send("Page.captureScreenshot", {"format": "png"})
            req_map[s1_id] = "ss_menu"
            e1_id = await send("Runtime.evaluate", {
                "expression": "JSON.stringify({ backend: window.HCS_APP ? window.HCS_APP.backendName : 'NO_APP', ui: Boolean(document.getElementById('screen-main-menu')), cards: document.querySelectorAll('.map-card').length })"
            })
            req_map[e1_id] = "eval_menu"
            await asyncio.sleep(1.0)

            # Navigate to World Selector
            print("\n--- TEST 2: Loading World Selector ---")
            await send("Page.navigate", {"url": f"{URL_BASE}/?screen=world_selector"})
            await asyncio.sleep(2.5)

            # Capture Screenshot 2
            s2_id = await send("Page.captureScreenshot", {"format": "png"})
            req_map[s2_id] = "ss_selector"
            e2_id = await send("Runtime.evaluate", {
                "expression": "JSON.stringify({ cards: document.querySelectorAll('.map-card').length, titles: Array.from(document.querySelectorAll('.card-title')).map(e => e.innerText) })"
            })
            req_map[e2_id] = "eval_selector"
            await asyncio.sleep(1.0)

            # Navigate to Gameplay (District Alpha)
            print("\n--- TEST 3: Loading Gameplay (map) ---")
            await send("Page.navigate", {"url": f"{URL_BASE}/?model=map"})
            await asyncio.sleep(4.0)

            # Capture Screenshot 3
            s3_id = await send("Page.captureScreenshot", {"format": "png"})
            req_map[s3_id] = "ss_gameplay"
            e3_id = await send("Runtime.evaluate", {
                "expression": "JSON.stringify({ activeColliders: window.HCS_APP ? window.HCS_APP.colliders.length : 0, pos: window.HCS_APP ? window.HCS_APP.controller.position : null, fps: window.HCS_APP ? window.HCS_APP.currentFps : 0 })"
            })
            req_map[e3_id] = "eval_gameplay"
            await asyncio.sleep(1.5)

            # Cancel listener
            listener_task.cancel()

            # Save screenshots
            for name, b64data in screenshots.items():
                if b64data:
                    fname = f"{name}.png"
                    with open(os.path.join(OUT_DIR, fname), "wb") as f:
                        f.write(base64.b64decode(b64data))
                    print(f"Saved screenshot {fname}")

            print("\nEvaluation results:")
            for k, v in eval_results.items():
                print(f"  {k}: {v}")

            # Save logs and network report
            with open(os.path.join(OUT_DIR, "hf_local_console.log"), "w", encoding="utf-8") as f:
                f.write("\n".join(logs))

            with open(os.path.join(OUT_DIR, "hf_network_report.json"), "w", encoding="utf-8") as f:
                json.dump(network_events, f, indent=2)

            print("\nSaved artifacts to artifacts/deployment/")
            print(f"Total console messages: {len(logs)}")
            print(f"Total network responses: {len(network_events)}")

    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(run_test())
