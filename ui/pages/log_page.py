from PySide6.QtWidgets import QWidget, QVBoxLayout, QTextEdit
from PySide6.QtCore import QTimer
import os


class LogPage(QWidget):
    def __init__(self):
        super().__init__()

        self.log_file = "logs/camera_events.log"
        self.last_size = 0

        layout = QVBoxLayout(self)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        self.log_box.setStyleSheet("""
            background-color: #0b0f14;
            color: #00ff9c;
            font-family: Consolas;
            font-size: 12px;
            border: 1px solid #222;
        """)

        layout.addWidget(self.log_box)

        # timer đọc file
        self.timer = QTimer()
        self.timer.timeout.connect(self.load_logs)

    def showEvent(self, e):
        self.load_logs()
        self.timer.start(1000)

    def hideEvent(self, e):
        self.timer.stop()

    def load_logs(self):
        if not os.path.exists(self.log_file):
            return

        size = os.path.getsize(self.log_file)

        if size < self.last_size:
            self.last_size = 0
            self.log_box.clear()

        if size == self.last_size:
            return

        with open(self.log_file, "r", encoding="utf-8") as f:
            f.seek(self.last_size)
            data = f.read()

        self.last_size = size

        if data:
            self.log_box.append(data.strip())

            cursor = self.log_box.textCursor()
            from PySide6.QtGui import QTextCursor
            cursor.movePosition(QTextCursor.End)
            self.log_box.setTextCursor(cursor)