from PySide6.QtWidgets import (
    QWidget,
    QLabel,
    QVBoxLayout,
    QGridLayout,
    QLineEdit
)
from PySide6.QtGui import QFont

from core.config_manager import load_config
from ui.widgets.camera_card import CameraCard
from ui.preview_window import PreviewWindow
from utils.url_helper import camera_rtsp_url

from log_panel import LogPanel
from system_logger import log

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

        # ===== CMD BAR =====
        self.cmd_input = QLineEdit()

        self.cmd_input.setPlaceholderText(
            "Hướng dẫn: c01stop=dừng; c01emp:NV001=Gán NV001; c01abcd1234xyz=Ghi với mã đơn hàng abcd1234xyz"
        )

        self.cmd_input.setFixedHeight(38)

        self.cmd_input.setStyleSheet("""
        QLineEdit{
            background:#0b0f14;
            color:#00ff99;

            border:2px solid #00aa66;
            border-radius:8px;

            padding-left:12px;

            font-size:14px;
            font-weight:bold;

            selection-background-color:#00aa66;
        }

        QLineEdit:focus{
            border:2px solid #00ff99;
            background:#101820;
        }
        """)

        self.cmd_input.returnPressed.connect(
            self.send_cmd
        )

        layout.addWidget(self.cmd_input)

        # ===== LOG PANEL =====
        self.log_panel = LogPanel()
        self.log_panel.setFixedHeight(120)

        layout.addWidget(self.log_panel)

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

            log(f"Preview {cam['name']}")

            self.open_preview(cam["name"], rtsp)

        return handler
    
    def manual_stop(self, cam_id):
        log(f"Manual stop CAM-{cam_id}")

        self.state.stop_record(
            cam_id,
            clear_employee=False
        )


    def send_cmd(self):
        text = self.cmd_input.text().strip()

        if not text:
            return

        try:
            from services.qr_engine import manual_qr_command

            manual_qr_command(text)

            log(f"CMD {text}")

        except Exception as e:
            log(f"CMD ERROR {e}")

        self.cmd_input.clear()