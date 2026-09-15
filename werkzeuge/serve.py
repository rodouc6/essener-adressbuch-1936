"""Kleiner Server für die Kontrollkarte: python3 werkzeuge/serve.py → http://localhost:8765/werkzeuge/kontrollkarte.html"""
import http.server, os, sys
os.chdir(os.path.join(os.path.dirname(__file__), ".."))
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=int(sys.argv[1]) if len(sys.argv) > 1 else 8765)
