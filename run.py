import os
import sys
import webbrowser
import threading
import time
import uvicorn

def open_browser(host: str, port: int):
    time.sleep(1.5)
    target_host = "localhost" if host in ("0.0.0.0", "127.0.0.1") else host
    webbrowser.open(f"http://{target_host}:{port}")

if __name__ == "__main__":
    if sys.platform == "win32" and hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    # Read host and port from environment (Render provides PORT, e.g. 10000)
    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    is_production = os.getenv("RENDER") is not None or os.getenv("PORT") is not None

    print("\n" + "="*65)
    print("  🎓 SmartStudy AI — Adaptive Multi-Exam Study Planner")
    print("  Priority-Driven Scheduling • Spaced Revision • Active Recall")
    print("  Engineered for College Students Preparing for Multiple Exams")
    print("="*65)
    print(f"  🌐 Starting web server on http://{host}:{port} ...")

    # Only auto-launch browser when run locally (not in headless production/Render)
    if not is_production:
        print("  🚀 Launching SmartStudy AI in your browser now...\n")
        threading.Thread(target=open_browser, args=(host, port), daemon=True).start()

    # Run Uvicorn server bound to 0.0.0.0 and PORT
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
