import sys

from PySide6.QtWidgets import QApplication, QMessageBox


from ui.main_window import MainWindow

from license.license_manager import LicenseManager


def main():

    app = QApplication(sys.argv)

    # =========================
    # LICENSE CHECK
    # =========================

    license_manager = LicenseManager()

    ok, msg = license_manager.check()

    print(msg)

    if not ok:
        QMessageBox.critical(None, "License", msg)
        sys.exit()
    # ========================= 
    # GLOBAL LICENSE MANAGER 
    # ========================= 
    app.license_manager = license_manager
    

    
    # =========================
    # MAIN WINDOW
    # =========================

    window = MainWindow()
    
    app.record_engine = window.record

    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()