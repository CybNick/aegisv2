"""Entrypoint for the API module."""
import uvicorn
from backend.core import get_settings
import webbrowser
import threading
import time

def _open_browser(url: str) -> None:
    time.sleep(1.5)  # Wait for uvicorn to bind
    webbrowser.open(url)

def main() -> None:
    settings = get_settings()
    url = f"http://{settings.host}:{settings.port}/"
    threading.Thread(target=_open_browser, args=(url,), daemon=True).start()
    
    uvicorn.run(
        "backend.api.app:app",
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
        reload=settings.reload,
    )

if __name__ == "__main__":
    main()
