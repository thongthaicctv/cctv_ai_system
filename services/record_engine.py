import threading

from services.record_worker import DEFAULT_RECORD_AUTO_STOP_SECONDS, RecordWorker


class RecordEngine:
    def __init__(self, state, storage_path, auto_stop_seconds=DEFAULT_RECORD_AUTO_STOP_SECONDS):
        self.state = state
        self.storage_path = storage_path
        self.auto_stop_seconds = auto_stop_seconds
        self.workers = {}
        self.threads = {}

    def start_camera(self, cam):
        if not cam.get("enabled", True):
            return

        cam_id = cam["id"]
        if cam_id in self.workers:
            return

        worker = RecordWorker(
            cam,
            self.state,
            self.storage_path,
            self.auto_stop_seconds,
        )

        thread = threading.Thread(
            target=worker.run,
            daemon=True,
        )
        thread.start()

        self.workers[cam_id] = worker
        self.threads[cam_id] = thread

    def stop_camera(self, cam_id):
        if cam_id not in self.workers:
            return

        self.workers[cam_id].stop()
        del self.workers[cam_id]
        self.threads.pop(cam_id, None)

    def start_all(self, cameras):
        for cam in cameras:
            self.start_camera(cam)

    def stop_all(self):
        for cam_id in list(self.workers.keys()):
            self.stop_camera(cam_id)
