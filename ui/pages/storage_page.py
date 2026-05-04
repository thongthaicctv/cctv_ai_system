from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QFileDialog, QSpinBox
)

from core.config_manager import load_config, save_config


class StoragePage(QWidget):
    def __init__(self):
        super().__init__()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("CÀI ĐẶT LƯU VIDEO")
        title.setStyleSheet("font-size:26px;font-weight:bold;color:white;")
        layout.addWidget(title)

        # thời gian auto stop
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Tự động dừng ghi hình (giây):"))

        self.spin_stop = QSpinBox()
        self.spin_stop.setRange(10, 7200)
        self.spin_stop.setValue(300)

        row1.addWidget(self.spin_stop)
        layout.addLayout(row1)

        # thư mục lưu
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Thư mục gốc lưu video:"))

        self.txt_path = QLineEdit()
        row2.addWidget(self.txt_path)

        btn_browse = QPushButton("📂 Chọn")
        btn_browse.clicked.connect(self.pick_folder)
        row2.addWidget(btn_browse)

        layout.addLayout(row2)

        # save
        self.btn_save = QPushButton("💾 Lưu cấu hình")
        self.btn_save.clicked.connect(self.save_data)

        layout.addWidget(self.btn_save)
        layout.addStretch()

        self.load_data()

    def load_data(self):
        data = load_config()

        self.spin_stop.setValue(
            data.get("record_auto_stop_seconds", 300)
        )

        self.txt_path.setText(
            data.get("storage_path", "videos")
        )

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Chọn thư mục lưu video"
        )

        if folder:
            self.txt_path.setText(folder)

    def save_data(self):
        data = load_config()

        data["record_auto_stop_seconds"] = self.spin_stop.value()
        data["storage_path"] = self.txt_path.text().strip()

        save_config(data)