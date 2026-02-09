import http.server
import socketserver

PORT = 8000

HTML = '''<!doctype html>
<html lang="ru">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Hello</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 0; padding: 2rem; background: #f6f7fb; color: #222; }
    .card { max-width: 520px; margin: 8vh auto; background: white; padding: 2rem; border-radius: 12px; box-shadow: 0 8px 24px rgba(0,0,0,.08); }
    h1 { margin-top: 0; }
  </style>
</head>
<body>
  <div class="card">
    <h1>Hello, world!</h1>
    <p>Это простая веб‑страница, отдаваемая Python HTTP‑сервером.</p>
  </div>
</body>
</html>
'''

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode("utf-8"))

if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"Serving on http://localhost:{PORT}")
        httpd.serve_forever()
