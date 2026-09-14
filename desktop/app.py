import os
import sys
import threading
import time
import http.server
import socketserver
import webview

PORT = 8085
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class DesktopHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def guess_type(self, path):
        if path.endswith('.glb'):
            return 'model/gltf-binary'
        if path.endswith('.gltf'):
            return 'model/gltf+json'
        if path.endswith('.webp'):
            return 'image/webp'
        if path.endswith('.js'):
            return 'application/javascript'
        return super().guess_type(path)

def start_server():
    os.chdir(BASE_DIR)
    with socketserver.TCPServer(("", PORT), DesktopHandler) as httpd:
        print(f"[Desktop Launcher] Local server running on http://localhost:{PORT}")
        httpd.serve_forever()

def main():
    # Start embedded server in daemon thread
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    # Launch native window with WebGPU / Edge WebView2 acceleration
    url = f"http://localhost:{PORT}/index.html"
    window = webview.create_window(
        title="HCS WorldJumper",
        url=url,
        width=1440,
        height=900,
        resizable=True,
        fullscreen=False,
        confirm_close=True,
        background_color='#030712'
    )
    webview.start(gui='edgechromium' if sys.platform == 'win32' else 'gtk', debug=False)

if __name__ == "__main__":
    main()
