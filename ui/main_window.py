# File: ui/main_window.py
# CCTV_AI_SYSTEM PRO
# Main Window Professional Version

import sys
import json
import os
import socket
from PySide6.QtCore import QTimer
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import subprocess
import platform

import psutil
import shutil

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel,
    QPushButton, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QStackedWidget
)

from ui.camera_config import CameraConfigPage


CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"cameras": []}

    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

LOG_FILE = "logs/camera_events.log"

def write_log(camera_name, status):
    os.makedirs("logs", exist_ok=True)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = f"{now} | {camera_name} | {status}\n"

    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line)


def ping_host(ip):
    try:
        system = platform.system().lower()

        if system == "windows":
            cmd = ["ping", "-n", "1", "-w", "1000", ip]
        else:
            cmd = ["ping", "-c", "1", "-W", "1", ip]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True
        )

        output = result.stdout.lower()

        if f"reply from {ip}".lower() in output:
            latency = 1

            for line in output.splitlines():
                if "time=" in line:
                    try:
                        part = line.split("time=")[1]
                        latency = int(part.split("ms")[0].replace("<","").strip())
                    except:
                        pass

            return True, latency

        return False, 0

    except:
        return False, 0

def check_camera(ip):
    try:
        socket.setdefaulttimeout(2)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((ip, 554))
        return True
    except:
        return False
    

# ===================================
# CARD CAMERA STATUS
# ===================================
class CameraCard(QFrame):
    def __init__(self, name, status="ONLINE"):
        super().__init__()

        self.setMinimumHeight(130)
        self.setStyleSheet("""
            QFrame{
                background:#1c1c1c;
                border:1px solid #2a2a2a;
                border-radius:12px;
            }
        """)

        self.lbl_name = QLabel(name)
        self.lbl_name.setFont(QFont("Segoe UI", 11, QFont.Bold))

        self.lbl_status = QLabel()
        self.lbl_order = QLabel("Sẵn sàng")

        self.set_status(status)

        layout = QVBoxLayout(self)
        layout.addWidget(self.lbl_name)
        layout.addWidget(self.lbl_status)
        layout.addWidget(self.lbl_order)
        layout.addStretch()
    



    def set_status(self, status):
        if status == "ONLINE":
            self.lbl_status.setText("🟢 ONLINE")
        elif status == "OFFLINE":
            self.lbl_status.setText("⚫ OFFLINE")
        elif status == "CHECKING":
            self.lbl_status.setText("🟡 CHECKING")
        else:
            self.lbl_status.setText("🟡 WAITING")

    

# ===================================
# DASHBOARD PAGE
# ===================================
class DashboardPage(QWidget):
    def __init__(self):
        super().__init__()

        self.title = QLabel("TỔNG QUAN HỆ THỐNG")
        self.title.setFont(QFont("Segoe UI", 18, QFont.Bold))

        self.lbl_online = QLabel("Camera Online: 0")
        self.lbl_offline = QLabel("Camera Offline: 0")
        self.lbl_total = QLabel("Tổng camera: 0")
        self.lbl_cpu = QLabel("CPU: 0%")
        self.lbl_ram = QLabel("RAM: 0%")
        self.lbl_disk = QLabel("Ổ D: 0%")

        for lbl in [
            self.lbl_online,
            self.lbl_offline,
            self.lbl_total,
            self.lbl_cpu,
            self.lbl_ram,
            self.lbl_disk
        ]:
            lbl.setFont(QFont("Segoe UI", 12))

        layout = QVBoxLayout(self)
        layout.addWidget(self.title)
        layout.addSpacing(15)

        layout.addWidget(self.lbl_online)
        layout.addWidget(self.lbl_offline)
        layout.addWidget(self.lbl_total)
        layout.addWidget(self.lbl_cpu)
        layout.addWidget(self.lbl_ram)
        layout.addWidget(self.lbl_disk)

        layout.addStretch()

    def update_stats(self, runtime_status):
        total = len(runtime_status)
        online = sum(1 for v in runtime_status.values() if v)
        offline = total - online

        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent

        disk = shutil.disk_usage("D:/")
        used_percent = round((disk.used / disk.total) * 100)

        self.lbl_online.setText(f"Camera Online: {online}")
        self.lbl_offline.setText(f"Camera Offline: {offline}")
        self.lbl_total.setText(f"Tổng camera: {total}")
        self.lbl_cpu.setText(f"CPU: {cpu}%")
        self.lbl_ram.setText(f"RAM: {ram}%")
        self.lbl_disk.setText(f"Ổ D: {used_percent}%")

# ===================================
# CAMERA GRID PAGE
# ===================================
class CameraGridPage(QWidget):
    def __init__(self):
        super().__init__()

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
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def reload_data(self, runtime_status=None):
        self.clear_grid()

        data = load_config()
        cams = data["cameras"]

        if not cams:
            card = CameraCard("CHƯA CÓ CAMERA", "OFFLINE")
            card.lbl_order.setText("Vào cấu hình để thêm camera")
            self.grid.addWidget(card, 0, 0)
            return

        for i, cam in enumerate(cams):

            status = "CHECKING"
            latency = 0
            last_check = "-"
            online = False

            if runtime_status is not None:
                info = runtime_status.get(cam["id"], {})

                online = info.get("online", False)
                status = info.get("status", "CHECKING")
                latency = info.get("latency", 0)
                last_check = info.get("last_check", "-")

            card = CameraCard(cam["name"], status)
            card.lbl_order.setText(
                f"{cam['ip']} | {latency}ms | {last_check}"
            )

            row = i // 4
            col = i % 4
            self.grid.addWidget(card, row, col)

# ===================================
# MAIN WINDOW
# ===================================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("CCTV_AI_SYSTEM PRO")
        self.resize(1600, 900)

        self.setStyleSheet("""
            QMainWindow{
                background:#111111;
            }
            QLabel{
                color:#eeeeee;
            }
            QPushButton{
                background:#1b1b1b;
                color:#dddddd;
                border:none;
                padding:12px;
                border-radius:8px;
                text-align:left;
                font-size:14px;
            }
            QPushButton:hover{
                background:#2b2b2b;
            }
            QPushButton:checked{
                background:#0f62fe;
                color:white;
            }
        """)

        root = QWidget()
        self.setCentralWidget(root)

        main_layout = QHBoxLayout(root)
        main_layout.setContentsMargins(0,0,0,0)

        # ================= Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("""
            QFrame{
                background:#161616;
                border-right:1px solid #222;
            }
        """)

        side_layout = QVBoxLayout(sidebar)

        logo = QLabel("CCTV AI SYSTEM")
        logo.setFont(QFont("Segoe UI", 15, QFont.Bold))

        side_layout.addWidget(logo)
        side_layout.addSpacing(10)

        self.btn_camera = QPushButton("🎥 Camera")
        self.btn_dashboard = QPushButton("🏠 Tổng quan")
        self.btn_config = QPushButton("⚙️ Cấu hình Camera")
        self.btn_search = QPushButton("🔍 Tra cứu")
        self.btn_video = QPushButton("📁 Video")

        buttons = [
            self.btn_camera,
            self.btn_dashboard,
            self.btn_config,
            self.btn_search,
            self.btn_video
        ]

        for b in buttons:
            b.setCheckable(True)
            side_layout.addWidget(b)

        side_layout.addStretch()

        # ================= Pages
        self.stack = QStackedWidget()

        self.page_camera = CameraGridPage()
        self.page_dashboard = DashboardPage()
        self.page_config = CameraConfigPage()

        self.stack.addWidget(self.page_camera)     # index 0
        self.stack.addWidget(self.page_dashboard) # index 1
        self.stack.addWidget(self.page_config)    # index 2
        self.stack.addWidget(QLabel("Tra cứu đơn hàng")) # index 3
        self.stack.addWidget(QLabel("Danh sách video"))  # index 4

        # default page = Camera
        self.btn_camera.setChecked(True)
        self.stack.setCurrentIndex(0)

        self.btn_camera.clicked.connect(lambda: self.switch_page(0))
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(1))
        self.btn_config.clicked.connect(lambda: self.switch_page(2))
        self.btn_search.clicked.connect(lambda: self.switch_page(3))
        self.btn_video.clicked.connect(lambda: self.switch_page(4))

        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.stack)

        self.camera_status = {}
        data = load_config()
        for cam in data["cameras"]:
            self.camera_status[cam["id"]] = {
                "online": False,
                "status": "CHECKING",
                "latency": 0,
                "last_check": "-"
            }


        self.timer = QTimer()
        self.timer.timeout.connect(self.auto_check_camera)
        self.timer.start(5000)

    def switch_page(self, index):
        for b in [
            self.btn_camera,
            self.btn_dashboard,
            self.btn_config,
            self.btn_search,
            self.btn_video
        ]:
            b.setChecked(False)

        sender = self.sender()
        if sender:
            sender.setChecked(True)

        if index == 0:
            self.page_camera.reload_data(self.camera_status)

        self.stack.setCurrentIndex(index)


    def auto_check_camera(self):
        data = load_config()
        cams = data["cameras"]

        def worker(cam):
            online, latency = ping_host(cam["ip"])
            return cam["id"], cam["name"], online, latency

        changed = False

        with ThreadPoolExecutor(max_workers=20) as executor:
            results = executor.map(worker, cams)

            for cam_id, cam_name, online, latency in results:
                old = self.camera_status.get(cam_id, {})

                now = datetime.now().strftime("%H:%M:%S")

                new_status = {
                    "online": online,
                    "status": "ONLINE" if online else "OFFLINE",
                    "latency": latency,
                    "last_check": now
                }

                if old.get("online") != online:
                    write_log(cam_name, new_status["status"])
                    changed = True

                self.camera_status[cam_id] = new_status

        self.page_camera.reload_data(self.camera_status)
        self.page_dashboard.update_stats(self.camera_status)

        
# ===================================
# RUN APP
# ===================================
def run_app():
    app = QApplication(sys.argv)

    win = MainWindow()
    win.show()

    sys.exit(app.exec())