from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QGridLayout
from PySide6.QtGui import QFont

from core.config_manager import load_config
from ui.widgets.camera_card import CameraCard
from ui.preview_window import PreviewWindow
from utils.url_helper import camera_rtsp_url

class CameraGridPage(QWidget):
    def __init__(self, state):
        super().__init__()
        self.state = state

        self.title = QLabel("TRẠNG THÁI CAMERA")
        self.title.setFont(QFont("Segoe UI", 18, QFont.Bold))

        self.grid = QGridLayout()
        self.grid.setSpacing(10)

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addLayout(self.grid)

        self.reload_data()

    def clear_grid(self):
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def reload_data(self, runtime=None):
        self.clear_grid()

        cams = load_config()["cameras"]

        for i, cam in enumerate(cams):
            info = runtime.get(cam["id"], {}) if runtime else {}

            card = CameraCard(
                cam["name"],
                info.get("status", "CHECKING")
            )
            card.set_info(cam, info)

            card.btn_preview.clicked.connect(
                self.make_preview_handler(cam)
            )
            card.btn_stop.clicked.connect(
                lambda _, cid=cam["id"]: self.manual_stop(cid)
            )
            self.grid.addWidget(card, i // 4, i % 4)



    def open_preview(self, name, rtsp):

        if not hasattr(self, "preview_windows"):
            self.preview_windows = {}

        # nếu đã mở rồi → focus lại
        if name in self.preview_windows:
            self.preview_windows[name].raise_()
            self.preview_windows[name].activateWindow()
            return

        win = PreviewWindow(name, rtsp)
        win.show()

        self.preview_windows[name] = win

        # khi đóng thì remove
        def on_close():
            if name in self.preview_windows:
                del self.preview_windows[name]

        win.destroyed.connect(on_close)
    
    def make_preview_handler(self, cam):

        def handler():
            rtsp = camera_rtsp_url(cam, prefer="main")

            self.open_preview(cam["name"], rtsp)

        return handler
    
    def manual_stop(self, cam_id):
        self.state.stop_record(
            cam_id,
            clear_employee=False
        )
