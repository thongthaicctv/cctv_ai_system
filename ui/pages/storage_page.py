from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.config_manager import load_config, save_config


class StoragePage(QWidget):
    settings_saved = Signal(dict)

    def __init__(self):
        super().__init__()
        self.cameras = []

        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(18)

        title = QLabel("CAI DAT LUU VIDEO")
        title.setStyleSheet("font-size:26px;font-weight:bold;color:white;")
        layout.addWidget(title)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Tu dong dung ghi hinh (giay):"))

        self.spin_stop = QSpinBox()
        self.spin_stop.setRange(10, 7200)
        self.spin_stop.setValue(300)
        self.spin_stop.setFixedWidth(180)

        row1.addStretch()
        row1.addWidget(self.spin_stop)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Thu muc goc luu video:"))

        self.txt_path = QLineEdit()
        row2.addWidget(self.txt_path, 1)

        btn_browse = QPushButton("Chon")
        btn_browse.clicked.connect(self.pick_folder)
        btn_browse.setFixedWidth(110)
        row2.addWidget(btn_browse)

        layout.addLayout(row2)

        self.btn_save = QPushButton("Luu cau hinh")
        self.btn_save.clicked.connect(self.save_data)
        layout.addWidget(self.btn_save)

        mapping_title = QLabel("Bang Mapping Scan -> Record")
        mapping_title.setStyleSheet("font-size:18px;font-weight:bold;color:white;")
        layout.addWidget(mapping_title)

        mapping_hint = QLabel("Hang = camera quet QR | Cot = camera ghi hinh main stream")
        mapping_hint.setStyleSheet("color:#9ca3af;font-size:12px;")
        layout.addWidget(mapping_hint)

        table_wrap = QFrame()
        table_wrap.setStyleSheet("""
            QFrame{
                background:#101010;
                border:1px solid #2a2a2a;
                border-radius:10px;
            }
        """)
        table_layout = QVBoxLayout(table_wrap)
        table_layout.setContentsMargins(10, 10, 10, 10)

        self.mapping_table = QTableWidget()
        self.mapping_table.setStyleSheet("""
            QTableWidget{
                background:#141414;
                color:white;
                gridline-color:#333333;
                border:none;
            }
            QHeaderView::section{
                background:#1e1e1e;
                color:white;
                border:1px solid #333333;
                padding:6px;
                font-weight:bold;
            }
        """)
        self.mapping_table.setAlternatingRowColors(False)
        self.mapping_table.verticalHeader().setDefaultSectionSize(34)
        self.mapping_table.horizontalHeader().setDefaultSectionSize(72)
        table_layout.addWidget(self.mapping_table)

        layout.addWidget(table_wrap, 1)

        self.load_data()

    def load_data(self):
        data = load_config()
        self.cameras = list(data.get("cameras", []))

        self.spin_stop.setValue(data.get("record_auto_stop_seconds", 300))
        self.txt_path.setText(data.get("storage_path", "videos"))
        self._build_mapping_table(data.get("record_mapping", {}))

    def _build_mapping_table(self, mapping):
        cameras = self.cameras
        labels = [cam.get("name", cam.get("id", "")) for cam in cameras]

        self.mapping_table.clear()
        self.mapping_table.setRowCount(len(cameras))
        self.mapping_table.setColumnCount(len(cameras))
        self.mapping_table.setVerticalHeaderLabels(labels)
        self.mapping_table.setHorizontalHeaderLabels(labels)

        for row, scan_cam in enumerate(cameras):
            scan_id = str(scan_cam.get("id", ""))
            target_ids = {str(target) for target in mapping.get(scan_id, [])}

            for col, record_cam in enumerate(cameras):
                record_id = str(record_cam.get("id", ""))
                item = QTableWidgetItem()
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsUserCheckable)
                item.setCheckState(
                    Qt.Checked if record_id in target_ids else Qt.Unchecked
                )
                self.mapping_table.setItem(row, col, item)

    def _read_mapping(self):
        mapping = {}

        for row, scan_cam in enumerate(self.cameras):
            scan_id = str(scan_cam.get("id", ""))
            targets = []

            for col, record_cam in enumerate(self.cameras):
                item = self.mapping_table.item(row, col)
                if item and item.checkState() == Qt.Checked:
                    targets.append(str(record_cam.get("id", "")))

            mapping[scan_id] = targets

        return mapping

    def pick_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Chon thu muc luu video",
        )

        if folder:
            self.txt_path.setText(folder)

    def save_data(self):
        data = load_config()
        data["record_auto_stop_seconds"] = self.spin_stop.value()
        data["storage_path"] = self.txt_path.text().strip()
        data["record_mapping"] = self._read_mapping()

        save_config(data)
        self.settings_saved.emit(load_config())
