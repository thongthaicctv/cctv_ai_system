import threading
from services.qr_worker import QRWorker


class QREngine:

    def __init__(self, state):
        self.state = state
        self.workers = {}
        self.threads = {}

    def start_camera(self, cam):
        if not cam.get("enabled", True):
            return

        cam_id = cam["id"]

        if cam_id in self.workers:
            return

        worker = QRWorker(cam, self.state)

        th = threading.Thread(
            target=worker.run,
            daemon=True
        )

        th.start()

        self.workers[cam_id] = worker
        self.threads[cam_id] = th

    def stop_camera(self, cam_id):
        if cam_id in self.workers:
            self.workers[cam_id].stop()
            del self.workers[cam_id]
            self.threads.pop(cam_id, None)

    def start_all(self, cameras):
        for cam in cameras:
            self.start_camera(cam)

    def stop_all(self):
        for cam_id in list(self.workers.keys()):
            self.stop_camera(cam_id)
