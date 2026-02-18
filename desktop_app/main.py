import sys
from PySide6.QtWidgets import QApplication

from view import MainWindow
from controller import AppController


def main():
    """Точка входа в приложение"""
    app = QApplication(sys.argv)

    # Создаем представление и контроллер
    view = MainWindow()
    controller = AppController(view)
    view.controller = controller  # Устанавливаем контроллер в представление

    # Показываем окно
    view.show()

    # Запускаем приложение
    sys.exit(app.exec())


if __name__ == "__main__":
    main()