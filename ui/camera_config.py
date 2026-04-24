# File: ui/camera_config.py
# Module: Camera Config Pro
# Python 3.10+
# pip install PySide6

import json
import os
import socket

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QMessageBox, QFileDialog, QDialog,
    QFormLayout
)

CONFIG_FILE = "config.json"


# =============================
# LOAD / SAVE CONFIG
# =============================
def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"cameras": []}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# =============================
# CAMERA FORM
# =============================
class CameraDialog(QDialog):
    def __init__(self, camera=None):
        super().__init__()

        self.setWindowTitle("Cấu hình Camera")
        self.resize(500, 300)

        self.id_input = QLineEdit()
        self.name_input = QLineEdit()
        self.ip_input = QLineEdit()
        self.rtsp_input = QLineEdit()
        self.area_input = QLineEdit()

        form = QFormLayout()
        form.addRow("ID Camera:", self.id_input)
        form.addRow("Tên hiển thị:", self.name_input)
        form.addRow("IP:", self.ip_input)
        form.addRow("RTSP:", self.rtsp_input)
        form.addRow("Khu vực:", self.area_input)

        btn_save = QPushButton("Lưu")
        btn_cancel = QPushButton("Hủy")

        btn_save.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)

        buttons = QHBoxLayout()
        buttons.addWidget(btn_save)
        buttons.addWidget(btn_cancel)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addStretch()
        layout.addLayout(buttons)

        if camera:
            self.id_input.setText(camera["id"])
            self.name_input.setText(camera["name"])
            self.ip_input.setText(camera["ip"])
            self.rtsp_input.setText(camera["rtsp"])
            self.area_input.setText(camera.get("area", ""))

    def get_data(self):
        return {
            "id": self.id_input.text().strip(),
            "name": self.name_input.text().strip(),
            "ip": self.ip_input.text().strip(),
            "rtsp": self.rtsp_input.text().strip(),
            "area": self.area_input.text().strip(),
            "enabled": True
        }


# =============================
# MAIN CONFIG PAGE
# =============================
class CameraConfigPage(QWidget):
    def __init__(self):
        super().__init__()

        self.data = load_config()

        title = QLabel("QUẢN LÝ CAMERA")
        title.setStyleSheet("font-size:20px;font-weight:bold;")

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "ID", "Tên camera", "IP", "RTSP", "Khu vực", "Trạng thái"
        ])

        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        # Buttons
        self.btn_add = QPushButton("➕ Thêm")
        self.btn_edit = QPushButton("✏️ Sửa")
        self.btn_delete = QPushButton("🗑️ Xóa")
        self.btn_test = QPushButton("📡 Test")
        self.btn_import = QPushButton("📥 Import")
        self.btn_export = QPushButton("📤 Export")

        btn_row = QHBoxLayout()
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_edit)
        btn_row.addWidget(self.btn_delete)
        btn_row.addWidget(self.btn_test)
        btn_row.addStretch()
        btn_row.addWidget(self.btn_import)
        btn_row.addWidget(self.btn_export)

        layout = QVBoxLayout(self)
        layout.addWidget(title)
        layout.addLayout(btn_row)
        layout.addWidget(self.table)

        # events
        self.btn_add.clicked.connect(self.add_camera)
        self.btn_edit.clicked.connect(self.edit_camera)
        self.btn_delete.clicked.connect(self.delete_camera)
        self.btn_test.clicked.connect(self.test_camera)
        self.btn_import.clicked.connect(self.import_json)
        self.btn_export.clicked.connect(self.export_json)

        self.refresh_table()

    # =============================
    # TABLE
    # =============================
    def refresh_table(self):
        cams = self.data["cameras"]
        self.table.setRowCount(len(cams))

        for row, cam in enumerate(cams):
            self.table.setItem(row, 0, QTableWidgetItem(cam["id"]))
            self.table.setItem(row, 1, QTableWidgetItem(cam["name"]))
            self.table.setItem(row, 2, QTableWidgetItem(cam["ip"]))
            self.table.setItem(row, 3, QTableWidgetItem(cam["rtsp"]))
            self.table.setItem(row, 4, QTableWidgetItem(cam.get("area", "")))

            status = "Bật" if cam.get("enabled", True) else "Tắt"
            self.table.setItem(row, 5, QTableWidgetItem(status))

    def get_selected_index(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        return row

    # =============================
    # ACTIONS
    # =============================
    def add_camera(self):
        dlg = CameraDialog()
        if dlg.exec():
            cam = dlg.get_data()
            self.data["cameras"].append(cam)
            save_config(self.data)
            self.refresh_table()

    def edit_camera(self):
        idx = self.get_selected_index()
        if idx is None:
            return

        cam = self.data["cameras"][idx]
        dlg = CameraDialog(cam)

        if dlg.exec():
            self.data["cameras"][idx] = dlg.get_data()
            save_config(self.data)
            self.refresh_table()

    def delete_camera(self):
        idx = self.get_selected_index()
        if idx is None:
            return

        reply = QMessageBox.question(
            self,
            "Xác nhận",
            "Xóa camera đã chọn?"
        )

        if reply == QMessageBox.Yes:
            self.data["cameras"].pop(idx)
            save_config(self.data)
            self.refresh_table()

    def test_camera(self):
        idx = self.get_selected_index()
        if idx is None:
            return

        cam = self.data["cameras"][idx]
        ip = cam["ip"]

        try:
            socket.setdefaulttimeout(2)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((ip, 554))

            cam["enabled"] = True
            save_config(self.data)
            self.refresh_table()

            QMessageBox.information(
                self,
                "Kết quả",
                f"{cam['name']}\nONLINE"
            )

        except:
            cam["enabled"] = False
            save_config(self.data)
            self.refresh_table()

            QMessageBox.warning(
                self,
                "Kết quả",
                f"{cam['name']}\nOFFLINE"
            )

    def import_json(self):
        file, _ = QFileDialog.getOpenFileName(
            self,
            "Import Config",
            "",
            "JSON Files (*.json)"
        )

        if not file:
            return

        with open(file, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        save_config(self.data)
        self.refresh_table()

    def export_json(self):
        file, _ = QFileDialog.getSaveFileName(
            self,
            "Export Config",
            "camera_config.json",
            "JSON Files (*.json)"
        )

        if not file:
            return

        with open(file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, indent=4, ensure_ascii=False)

        QMessageBox.information(self, "Thành công", "Đã xuất cấu hình.")