import time

from core.config_manager import load_config
from services.audio_service import employee_ok, order_ok, stop_ok
from services.qr_decoder import (
    decode_qr_texts,
    decode_qr_texts_fast,
    parse_qr_command,
)
from utils.url_helper import camera_rtsp_url, open_rtsp_capture


DEFAULT_SCAN_INTERVAL = 0.03
DEFAULT_DUPLICATE_SECONDS = 5
RECONNECT_DELAY_SECONDS = 2
MAX_RECONNECT_DELAY_SECONDS = 30
RTSP_OPEN_TIMEOUT_MSEC = 5000
RTSP_READ_TIMEOUT_MSEC = 5000
FULL_SCAN_EVERY_FRAMES = 5
SLOW_SCAN_EVERY_FRAMES = 25


class QRWorker:
    def __init__(self, cam, state):
        self.cam = cam
        self.state = state
        self.running = True

        self.last_seen = {}
        self.cap = None
        self.fail_count = 0
        self.frame_index = 0

    def run(self):
        cam_id = self.cam["id"]
        rtsp = camera_rtsp_url(self.cam, prefer="sub")

        if not rtsp:
            self.state.set_error(cam_id, "Missing RTSP URL")
            return

        print(f"[{cam_id}] QR stream: {rtsp}")

        while self.running:
            if not self._ensure_capture(rtsp, cam_id):
                self._sleep_after_failure()
                continue

            try:
                ok, frame = self.cap.read()
            except Exception as exc:
                self.state.set_error(cam_id, f"Read RTSP failed: {exc}")
                self._release_capture()
                self._sleep_after_failure()
                continue

            if not ok or frame is None:
                self.state.set_error(cam_id, "Lost RTSP frame")
                self._release_capture()
                self._sleep_after_failure()
                continue

            self.fail_count = 0
            self.state.clear_error(cam_id)
            self.frame_index += 1

            if self.frame_index % 100 == 0:
                self._clean_seen_cache()

            self._scan_frame(cam_id, frame)
            time.sleep(float(self.cam.get("qr_scan_interval", DEFAULT_SCAN_INTERVAL)))

        self._release_capture()

    def _ensure_capture(self, rtsp, cam_id):
        if self.cap is not None and self.cap.isOpened():
            return True

        self._release_capture()
        self.cap = open_rtsp_capture(
            rtsp,
            open_timeout_msec=self.cam.get("rtsp_open_timeout_msec", RTSP_OPEN_TIMEOUT_MSEC),
            read_timeout_msec=self.cam.get("rtsp_read_timeout_msec", RTSP_READ_TIMEOUT_MSEC),
        )

        if self.cap.isOpened():
            return True

        self.state.set_error(cam_id, "Cannot open RTSP stream for QR")
        self._release_capture()
        return False

    def _sleep_after_failure(self):
        delay = min(
            MAX_RECONNECT_DELAY_SECONDS,
            RECONNECT_DELAY_SECONDS * (2 ** min(self.fail_count, 4)),
        )
        self.fail_count += 1
        time.sleep(delay)

    def _release_capture(self):
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def _scan_frame(self, cam_id, frame):
        for region in self._fast_scan_regions(frame):
            if self._process_texts(cam_id, decode_qr_texts_fast(region)):
                return

        if self.frame_index % self._slow_scan_every_frames() != 0:
            return

        for region in self._slow_scan_regions(frame):
            if self._process_texts(cam_id, decode_qr_texts(region)):
                return

    def _process_texts(self, cam_id, texts):
        for text in texts:
            if not self._should_accept(text):
                return True

            print(f"[{cam_id}] SCAN: {text}")
            self.state.set_scan(cam_id, text)
            self._handle_command(cam_id, text)
            return True

        return False

    def _fast_scan_regions(self, frame):
        yield self._center_roi(frame)

        if self.frame_index % self._full_scan_every_frames() == 0:
            yield frame

    def _slow_scan_regions(self, frame):
        yield self._center_roi(frame)
        yield frame

    def _center_roi(self, frame):
        h, w = frame.shape[:2]
        x1 = int(w * 0.2)
        x2 = int(w * 0.8)
        y1 = int(h * 0.2)
        y2 = int(h * 0.8)
        return frame[y1:y2, x1:x2]

    def _full_scan_every_frames(self):
        return max(1, int(self.cam.get("qr_full_scan_every_frames", FULL_SCAN_EVERY_FRAMES)))

    def _slow_scan_every_frames(self):
        return max(1, int(self.cam.get("qr_slow_scan_every_frames", SLOW_SCAN_EVERY_FRAMES)))

    def _should_accept(self, text):
        now = time.time()
        duplicate_seconds = float(self.cam.get("qr_duplicate_seconds", DEFAULT_DUPLICATE_SECONDS))
        last_time = self.last_seen.get(text)
        if last_time and now - last_time < duplicate_seconds:
            return False

        self.last_seen[text] = now
        return True

    def _handle_command(self, scan_cam_id, text):
        command = parse_qr_command(text)
        action = command["action"]
        target_ids = self._target_camera_ids(scan_cam_id)

        if action == "stop":
            for target_id in target_ids:
                self.state.stop_record(target_id, clear_employee=True)
            stop_ok()
            return

        if action == "employee":
            for target_id in target_ids:
                self.state.assign_employee(
                    target_id,
                    employee_id=command.get("employee_id", ""),
                    employee_name=command.get("employee_name", ""),
                    shift_code=command.get("shift_code", ""),
                )
            employee_ok()
            return

        if action != "order":
            return

        order_code = command.get("order_code", "")
        if not order_code:
            return

        any_started = False
        for target_id in target_ids:
            state = self.state.get(target_id)
            if not state.get("employee_id"):
                self.state.set_error(target_id, "Scan EMP before order")
                continue

            if state.get("recording") and state.get("order_code") == order_code:
                continue

            self.state.start_record(target_id, order_code=order_code)
            any_started = True

        if any_started:
            order_ok()

    def _target_camera_ids(self, scan_cam_id):
        data = load_config()
        mapping = data.get("record_mapping", {})
        targets = mapping.get(str(scan_cam_id), [])
        return targets or [str(scan_cam_id)]

    def stop(self):
        self.running = False

    def _clean_seen_cache(self):
        now = time.time()
        self.last_seen = {k: v for k, v in self.last_seen.items() if now - v < 10}
