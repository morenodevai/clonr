"""Entry point — launch the Clonr GUI."""
import sys
from PyQt6.QtWidgets import QApplication
from gui.app import ClonrWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Clonr")
    window = ClonrWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
