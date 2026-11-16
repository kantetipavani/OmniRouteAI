"""
OmniRoute Unified Fullstack Server Launcher.
Starts FastAPI backend + serves React SPA frontend on http://127.0.0.1:8001/
"""
import sys
import os
import socket
import uvicorn

# Ensure backend directory is in Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "backend"))

def find_available_port(preferred_ports=[8001, 8000, 8080, 5000]):
    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                try:
                    s.bind(('127.0.0.1', port))
                    return port
                except OSError:
                    continue
    return 8001

if __name__ == "__main__":
    from app.main import app
    port = int(os.getenv("PORT", find_available_port()))
    print("==================================================================")
    print(" OmniRoute Enterprise Case Routing & SLA Engine is Starting...")
    print(f" Application URL : http://127.0.0.1:{port}/")
    print(f" Interactive Docs: http://127.0.0.1:{port}/docs")
    print("==================================================================")
    uvicorn.run(app, host="127.0.0.1", port=port)
