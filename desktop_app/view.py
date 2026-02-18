import math
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGraphicsView,
    QGraphicsScene, QGraphicsEllipseItem, QGraphicsRectItem,
    QPushButton, QLabel, QSpinBox, QProgressBar,
    QGroupBox, QGridLayout, QGraphicsSimpleTextItem
)
from PySide6.QtGui import QPainter, QPen, QColor, QBrush, QFont
from PySide6.QtCore import Qt, QRectF


class MonteCarloView(QGraphicsView):
    """Виджет для отображения точек Монте-Карло (View)"""

    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)

        # Настройка отображения
        self.setMinimumSize(500, 500)
        self.scene.setSceneRect(0, 0, 400, 400)

        # Масштабируем координаты [-1,1] -> [0,400]
        self.scale_x = 200  # масштаб по X
        self.scale_y = 200  # масштаб по Y
        self.center_x = 200  # центр по X
        self.center_y = 200  # центр по Y

        # Рисуем круг и квадрат
        self.draw_shapes()

        # Счетчики точек
        self.circle_points_count = 0
        self.square_points_count = 0

    def draw_shapes(self):
        """Рисуем круг и квадрат для визуализации"""
        # Квадрат (от -1 до 1 по обеим осям)
        square_size = 400
        square = QGraphicsRectItem(0, 0, square_size, square_size)
        square.setPen(QPen(Qt.black, 2))
        square.setBrush(QBrush(Qt.transparent))
        self.scene.addItem(square)

        # Круг (радиус 200, центр в (200, 200))
        circle = QGraphicsEllipseItem(0, 0, 400, 400)
        circle.setPen(QPen(Qt.red, 2))
        circle.setBrush(QBrush(Qt.transparent))
        self.scene.addItem(circle)

        # Добавляем координатные оси
        self.draw_axes()

    def draw_axes(self):
        """Рисуем координатные оси"""
        # Горизонтальная ось
        axis_x = self.scene.addLine(0, 200, 400, 200, QPen(Qt.gray, 1, Qt.DashLine))
        # Вертикальная ось
        axis_y = self.scene.addLine(200, 0, 200, 400, QPen(Qt.gray, 1, Qt.DashLine))

        # Подписи осей
        font = QFont("Arial", 10)

        # Левая подпись
        left_text = QGraphicsSimpleTextItem("-1")
        left_text.setFont(font)
        left_text.setPos(5, 190)
        self.scene.addItem(left_text)

        # Правая подпись
        right_text = QGraphicsSimpleTextItem("1")
        right_text.setFont(font)
        right_text.setPos(385, 190)
        self.scene.addItem(right_text)

        # Верхняя подпись
        top_text = QGraphicsSimpleTextItem("1")
        top_text.setFont(font)
        top_text.setPos(190, 5)
        self.scene.addItem(top_text)

        # Нижняя подпись
        bottom_text = QGraphicsSimpleTextItem("-1")
        bottom_text.setFont(font)
        bottom_text.setPos(190, 385)
        self.scene.addItem(bottom_text)

        # Центр
        center_text = QGraphicsSimpleTextItem("0")
        center_text.setFont(font)
        center_text.setPos(195, 195)
        self.scene.addItem(center_text)

    def add_point(self, x, y, in_circle):
        """Добавление точки на график"""
        # Преобразуем координаты из [-1,1] в [0,400]
        plot_x = self.center_x + x * self.scale_x
        plot_y = self.center_y - y * self.scale_y  # инвертируем Y

        if in_circle:
            color = QColor(0, 100, 255)  # Синий для точек внутри круга
            self.circle_points_count += 1
        else:
            color = QColor(255, 100, 0)  # Оранжевый для точек вне круга
            self.square_points_count += 1

        # Создаем точку (маленький круг)
        point_size = 3  # размер точки
        point = QGraphicsEllipseItem(
            plot_x - point_size / 2,
            plot_y - point_size / 2,
            point_size,
            point_size
        )
        point.setBrush(QBrush(color))
        point.setPen(QPen(Qt.NoPen))
        self.scene.addItem(point)

    def clear_points(self):
        """Очистка всех точек"""
        items_to_remove = []
        for item in self.scene.items():
            # Удаляем только точки (эллипсы), но не фигуры и текст
            if isinstance(item, QGraphicsEllipseItem) and item.rect().width() < 10:
                items_to_remove.append(item)

        for item in items_to_remove:
            self.scene.removeItem(item)

        self.circle_points_count = 0
        self.square_points_count = 0

    def get_points_count(self):
        """Получение количества точек"""
        return self.circle_points_count + self.square_points_count


class MainWindow(QMainWindow):
    """Главное окно приложения (View)"""

    def __init__(self, controller=None):
        super().__init__()
        self.controller = controller
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """Инициализация интерфейса"""
        self.setWindowTitle("Вычисление числа π методом Монте-Карло")
        self.setGeometry(100, 100, 1000, 700)

        # Центральный виджет
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Основной макет
        main_layout = QHBoxLayout(central_widget)

        # Левая панель - график
        left_panel = QVBoxLayout()

        # Заголовок графика
        graph_label = QLabel("Визуализация метода Монте-Карло")
        graph_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        graph_label.setAlignment(Qt.AlignCenter)
        left_panel.addWidget(graph_label)

        self.graphics_view = MonteCarloView()
        left_panel.addWidget(self.graphics_view)

        # Легенда
        legend_layout = QHBoxLayout()
        legend_layout.addStretch()

        # Легенда для точек в круге
        circle_legend = QLabel()
        circle_legend.setStyleSheet(
            "background-color: rgb(0, 100, 255); width: 20px; height: 20px; border-radius: 10px;")
        legend_layout.addWidget(circle_legend)
        legend_layout.addWidget(QLabel(" - точки в круге"))

        # Легенда для точек вне круга
        square_legend = QLabel()
        square_legend.setStyleSheet(
            "background-color: rgb(255, 100, 0); width: 20px; height: 20px; border-radius: 10px;")
        legend_layout.addWidget(square_legend)
        legend_layout.addWidget(QLabel(" - точки вне круга"))

        legend_layout.addStretch()
        left_panel.addLayout(legend_layout)

        # Правая панель - управление и статистика
        right_panel = QVBoxLayout()

        # Группа управления
        control_group = QGroupBox("Управление")
        control_layout = QVBoxLayout()

        # Выбор количества точек
        points_layout = QHBoxLayout()
        points_layout.addWidget(QLabel("Количество точек:"))
        self.points_spinbox = QSpinBox()
        self.points_spinbox.setRange(100, 1000000)
        self.points_spinbox.setValue(10000)
        self.points_spinbox.setSingleStep(1000)
        self.points_spinbox.setMaximumWidth(150)
        points_layout.addWidget(self.points_spinbox)
        points_layout.addStretch()
        control_layout.addLayout(points_layout)

        # Кнопки управления
        self.start_button = QPushButton("▶ Начать расчет")
        self.start_button.clicked.connect(self.on_start_clicked)
        self.start_button.setStyleSheet("font-weight: bold; padding: 8px;")
        control_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("⏸ Пауза")
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("padding: 8px;")
        control_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("⏹ Остановить")
        self.stop_button.clicked.connect(self.on_stop_clicked)
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("padding: 8px;")
        control_layout.addWidget(self.stop_button)

        self.clear_button = QPushButton("🗑 Очистить график")
        self.clear_button.clicked.connect(self.on_clear_clicked)
        self.clear_button.setStyleSheet("padding: 8px;")
        control_layout.addWidget(self.clear_button)

        control_group.setLayout(control_layout)
        right_panel.addWidget(control_group)

        # Группа статистики
        stats_group = QGroupBox("Статистика")
        stats_layout = QGridLayout()

        # Текущее значение π
        stats_layout.addWidget(QLabel("Текущее π:"), 0, 0)
        self.pi_label = QLabel("0.000000")
        self.pi_label.setStyleSheet("font-weight: bold; font-size: 16px; color: blue;")
        stats_layout.addWidget(self.pi_label, 0, 1)

        # Точное значение π
        stats_layout.addWidget(QLabel("Точное π:"), 1, 0)
        self.true_pi_label = QLabel(f"{math.pi:.6f}")
        self.true_pi_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.true_pi_label, 1, 1)

        # Погрешность
        stats_layout.addWidget(QLabel("Погрешность:"), 2, 0)
        self.error_label = QLabel("0.000000")
        self.error_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.error_label, 2, 1)

        # Обработанные точки
        stats_layout.addWidget(QLabel("Обработано точек:"), 3, 0)
        self.processed_label = QLabel("0")
        self.processed_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.processed_label, 3, 1)

        # Точки в круге
        stats_layout.addWidget(QLabel("Точек в круге:"), 4, 0)
        self.in_circle_label = QLabel("0")
        self.in_circle_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.in_circle_label, 4, 1)

        # Отношение точек
        stats_layout.addWidget(QLabel("Отношение (в круге/всего):"), 5, 0)
        self.ratio_label = QLabel("0.0000")
        self.ratio_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.ratio_label, 5, 1)

        # Время выполнения
        stats_layout.addWidget(QLabel("Время выполнения:"), 6, 0)
        self.time_label = QLabel("0.000 с")
        self.time_label.setStyleSheet("font-size: 14px;")
        stats_layout.addWidget(self.time_label, 6, 1)

        # Прогресс бар
        stats_layout.addWidget(QLabel("Прогресс:"), 7, 0, 1, 2)
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("QProgressBar { height: 20px; }")
        stats_layout.addWidget(self.progress_bar, 8, 0, 1, 2)

        stats_group.setLayout(stats_layout)
        right_panel.addWidget(stats_group)

        # Группа теории
        theory_group = QGroupBox("О методе Монте-Карло")
        theory_layout = QVBoxLayout()
        theory_text = QLabel(
            "<b>Принцип метода:</b><br>"
            "1. Рассматриваем квадрат со стороной 2 и вписанный в него круг радиусом 1<br>"
            "2. Отношение площадей: Sкруга/Sквадрата = πr²/(2r)² = π/4<br>"
            "3. Генерируем случайные точки в квадрате<br>"
            "4. Отношение точек в круге к общему числу точек ≈ π/4<br>"
            "5. π ≈ 4 × (точки в круге) / (все точки)<br><br>"
            "<i>Чем больше точек, тем точнее результат!</i>"
        )
        theory_text.setWordWrap(True)
        theory_text.setStyleSheet("font-size: 12px;")
        theory_layout.addWidget(theory_text)
        theory_group.setLayout(theory_layout)
        right_panel.addWidget(theory_group)

        # Добавляем растягивающийся элемент для выравнивания
        right_panel.addStretch()

        # Добавляем панели в основной макет
        main_layout.addLayout(left_panel, 3)  # График занимает больше места
        main_layout.addLayout(right_panel, 2)

    def on_start_clicked(self):
        """Обработка нажатия кнопки старта"""
        if self.controller:
            self.controller.start_calculation()

    def on_pause_clicked(self):
        """Обработка нажатия кнопки паузы"""
        if self.controller:
            self.controller.pause_calculation()

    def on_stop_clicked(self):
        """Обработка нажатия кнопки остановки"""
        if self.controller:
            self.controller.stop_calculation()

    def on_clear_clicked(self):
        """Обработка нажатия кнопки очистки"""
        if self.controller:
            self.controller.clear_graph()

    def get_points_count(self):
        """Получение количества точек из spinbox"""
        return self.points_spinbox.value()

    def set_start_button_enabled(self, enabled):
        """Включение/отключение кнопки старта"""
        self.start_button.setEnabled(enabled)

    def set_pause_button_enabled(self, enabled):
        """Включение/отключение кнопки паузы"""
        self.pause_button.setEnabled(enabled)

    def set_stop_button_enabled(self, enabled):
        """Включение/отключение кнопки остановки"""
        self.stop_button.setEnabled(enabled)

    def set_pause_button_text(self, text):
        """Установка текста кнопки паузы"""
        self.pause_button.setText(text)

    def set_points_spinbox_enabled(self, enabled):
        """Включение/отключение spinbox"""
        self.points_spinbox.setEnabled(enabled)

    def update_stats(self, processed, in_circle, pi_estimate, elapsed_time):
        """Обновление статистики"""
        self.pi_label.setText(f"{pi_estimate:.6f}")
        self.processed_label.setText(f"{processed}")
        self.in_circle_label.setText(f"{in_circle}")
        self.time_label.setText(f"{elapsed_time:.3f} с")

        # Вычисляем погрешность
        error = abs(pi_estimate - math.pi)
        self.error_label.setText(f"{error:.6f}")

        # Вычисляем отношение
        if processed > 0:
            ratio = in_circle / processed
            self.ratio_label.setText(f"{ratio:.4f}")

        # Обновляем прогресс бар
        progress = int(processed / self.get_points_count() * 100)
        self.progress_bar.setValue(progress)

    def reset_stats(self):
        """Сброс статистики"""
        self.pi_label.setText("0.000000")
        self.error_label.setText("0.000000")
        self.processed_label.setText("0")
        self.in_circle_label.setText("0")
        self.ratio_label.setText("0.0000")
        self.time_label.setText("0.000 с")
        self.progress_bar.setValue(0)

    def add_point_to_view(self, x, y, in_circle):
        """Добавление точки на график"""
        self.graphics_view.add_point(x, y, in_circle)

    def clear_graphics_view(self):
        """Очистка графического виджета"""
        self.graphics_view.clear_points()

    def print_final_result(self, pi_estimate, elapsed_time):
        """Вывод финального результата в консоль"""
        print(f"Расчет завершен: π ≈ {pi_estimate:.6f}")
        print(f"Точное значение: π = {math.pi:.6f}")
        print(f"Погрешность: {abs(pi_estimate - math.pi):.6f}")
        print(f"Время выполнения: {elapsed_time:.3f} с")