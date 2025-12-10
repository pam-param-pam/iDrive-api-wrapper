import threading
import time
import logging

from ..downloader.state import ThrottleState

logger = logging.getLogger("iDrive")


class AutoScaler:
    def __init__(self, max_workers: int, throttle_state: ThrottleState):
        self.min = 1
        self.max = max_workers
        self.current = self.min
        self.ts = throttle_state
        self.lock = threading.Lock()
        self.stop_flag = False

        self._last_rate = 0.0
        self._no_improve_steps = 0

    # -------------------------------
    # Worker count management helpers
    # -------------------------------

    def _inc_workers(self, spawn_fn):
        if self.current < self.max:
            spawn_fn()
            self.current += 2
            logger.info(f"[AutoScaler] Scaled UP → workers={self.current}")
        else:
            logger.info(f"[AutoScaler] Wanted scale UP but already at max={self.max}")

    def _dec_workers(self, kill_fn):
        if self.current > self.min:
            kill_fn()
            self.current -= 1
            logger.info(f"[AutoScaler] Scaled DOWN → workers={self.current}")
        else:
            logger.info(f"[AutoScaler] Wanted scale DOWN but already at min={self.min}")

    # -------------------------------
    # Autoscaling loop
    # -------------------------------

    def start(self, spawn_fn, kill_fn):
        t = threading.Thread(target=self._loop, args=(spawn_fn, kill_fn), daemon=True)
        t.start()
        return t

    def _loop(self, spawn_fn, kill_fn):
        logger.info("[AutoScaler] Started autoscaling loop")

        while not self.stop_flag:
            time.sleep(1.5)

            retries = self.ts.retry_rate()
            hard_errors = self.ts.hard_error_rate()
            rate = self.ts.download_rate()

            logger.debug(
                f"[AutoScaler] workers={self.current}, retries={retries}, "
                f"hard_errors={hard_errors}, rate={rate:.1f} B/s"
            )

            with self.lock:
                # 1. hard throttling → immediate scale down
                if hard_errors > 0:
                    logger.warning(
                        f"[AutoScaler] Hard throttling ({hard_errors}) → scale DOWN"
                    )
                    self._dec_workers(kill_fn)
                    self._last_rate = rate
                    continue

                # 2. too many retries → scale down
                if retries >= 3:
                    logger.warning(
                        f"[AutoScaler] High retry rate ({retries}) → scale DOWN"
                    )
                    self._dec_workers(kill_fn)
                    self._last_rate = rate
                    continue

                # 3. throughput trend
                if rate <= self._last_rate * 1.02:  # < ~2% improvement
                    self._no_improve_steps += 1
                else:
                    self._no_improve_steps = 0

                if self._no_improve_steps >= 4 and self.current > self.min:
                    logger.info(
                        f"[AutoScaler] Throughput plateau (rate={rate:.1f}, "
                        f"prev={self._last_rate:.1f}) → scale DOWN"
                    )
                    self._dec_workers(kill_fn)
                    self._last_rate = rate
                    continue

                # 4. conditions for scaling UP
                if retries == 0 and hard_errors == 0:
                    if rate > self._last_rate * 1.10:  # >10% better
                        logger.info(
                            "[AutoScaler] Healthy & improving throughput → scale UP"
                        )
                        self._inc_workers(spawn_fn)

                self._last_rate = rate

        logger.info("[AutoScaler] Exiting autoscaling loop")

    def stop(self):
        logger.info("[AutoScaler] Stop requested")
        self.stop_flag = True
