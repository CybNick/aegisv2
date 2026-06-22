import asyncio
import time
from backend.monitoring.state import StateManager
import logging

logger = logging.getLogger(__name__)

class MonitoringScheduler:
    def __init__(self, state_manager: StateManager, scan_callback, detect_callback):
        self.state_manager = state_manager
        self._scan_callback = scan_callback
        self._detect_callback = detect_callback
        self._task = None
        self._stop_event = asyncio.Event()

    def start(self):
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Monitoring Scheduler started.")

    def stop(self):
        self._stop_event.set()
        if self._task:
            self._task.cancel()
        logger.info("Monitoring Scheduler stopped.")

    async def _run_loop(self):
        try:
            while not self._stop_event.is_set():
                config = self.state_manager.config
                if not config.enabled:
                    await asyncio.sleep(10)
                    continue

                state = self.state_manager.status
                now = time.time()
                
                next_scan = state.next_scan_time or now

                if now >= next_scan:
                    # Time to run!
                    prev_time = state.last_scan_time or now
                    self.state_manager.set_scan_status(is_scanning=True)
                    
                    # Run the scans
                    try:
                        self._scan_callback(config.targets)
                        curr_time = time.time()
                        self.state_manager.set_scan_status(is_scanning=False, last_scan_time=curr_time)
                        
                        # Trigger detection
                        self._detect_callback(prev_time, curr_time)
                        
                    except Exception as e:
                        logger.error(f"Error during scheduled scan: {e}")
                        self.state_manager.set_scan_status(is_scanning=False)

                await asyncio.sleep(30)
        except asyncio.CancelledError:
            pass
