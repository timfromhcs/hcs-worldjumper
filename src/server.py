import http.server
import socketserver
import os
import sys

PORT = 8080
DIRECTORY = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()

    def do_POST(self):
        if self.path == '/api/save_render':
            import json, base64
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)
            try:
                data = json.loads(body.decode('utf-8'))
                save_path = os.path.normpath(os.path.join(DIRECTORY, data['path']))
                # ensure inside DIRECTORY
                if not save_path.startswith(DIRECTORY):
                    self.send_error(403, "Access denied")
                    return
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                img_data = data['image']
                if ',' in img_data:
                    img_data = img_data.split(',', 1)[1]
                with open(save_path, 'wb') as f:
                    f.write(base64.b64decode(img_data))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
                return
            except Exception as e:
                self.send_error(500, str(e))
                return
        self.send_error(404, "Not found")

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

class ThreadingServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True

if __name__ == "__main__":
    os.chdir(DIRECTORY)
    ThreadingServer.allow_reuse_address = True
    with ThreadingServer(("", PORT), Handler) as httpd:
        print(f"Server started at http://localhost:{PORT} serving {DIRECTORY}", flush=True)
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("Server stopped.")
