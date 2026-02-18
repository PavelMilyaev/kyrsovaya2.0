# tests/desktop/test_view.py
"""Тесты для представления (view.py)"""
import pytest
from unittest.mock import Mock, patch
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from desktop_app.view import MainWindow, MonteCarloView
import math


@pytest.fixture(scope="session")
def qapp():
    """Фикстура для QApplication"""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


class TestMonteCarloView:
    """Тесты для виджета отображения MonteCarloView"""

    def test_initialization(self, qapp):
        """Тест инициализации представления"""
        view = MonteCarloView()
        
        assert view.scene is not None
        assert view.circle_points_count == 0
        assert view.square_points_count == 0
        
        # Проверяем, что размер сцены установлен правильно
        assert view.scene.sceneRect().width() == 400
        assert view.scene.sceneRect().height() == 400
        
        # Не проверяем точную ширину виджета, так как она может зависеть от настроек
        assert view.width() > 0
        assert view.height() > 0

    def test_draw_shapes(self, qapp):
        """Тест отрисовки фигур"""
        view = MonteCarloView()
        
        # Проверяем наличие элементов в сцене
        items = view.scene.items()
        
        # Должны быть как минимум: квадрат, круг, оси и подписи
        assert len(items) >= 6
        
        # Ищем квадрат (QGraphicsRectItem)
        squares = [item for item in items if isinstance(item, type(view.scene.addRect(0,0,1,1)))]
        assert len(squares) >= 1
        
        # Ищем круг (QGraphicsEllipseItem)
        circles = [item for item in items if isinstance(item, type(view.scene.addEllipse(0,0,1,1)))]
        assert len(circles) >= 1

    def test_add_point_inside_circle(self, qapp):
        """Тест добавления точки внутри круга"""
        view = MonteCarloView()
        initial_points = view.get_points_count()
        
        # Добавляем точку внутри круга
        view.add_point(0.2, 0.3, in_circle=True)
        
        assert view.get_points_count() == initial_points + 1
        assert view.circle_points_count == 1
        assert view.square_points_count == 0

    def test_add_point_outside_circle(self, qapp):
        """Тест добавления точки вне круга"""
        view = MonteCarloView()
        initial_points = view.get_points_count()
        
        # Добавляем точку вне круга
        view.add_point(0.8, 0.8, in_circle=False)
        
        assert view.get_points_count() == initial_points + 1
        assert view.circle_points_count == 0
        assert view.square_points_count == 1

    def test_clear_points(self, qapp):
        """Тест очистки точек"""
        view = MonteCarloView()
        
        # Добавляем несколько точек
        view.add_point(0.1, 0.1, True)
        view.add_point(0.8, 0.8, False)
        view.add_point(0.3, 0.3, True)
        
        assert view.get_points_count() == 3
        
        view.clear_points()
        
        assert view.get_points_count() == 0
        assert view.circle_points_count == 0
        assert view.square_points_count == 0

    def test_coordinate_transformation(self, qapp):
        """Тест преобразования координат"""
        view = MonteCarloView()
        
        # Точка с координатами (1,1) должна преобразоваться в (400,0) на экране
        # (инвертирование Y)
        with patch.object(view.scene, 'addItem') as mock_add_item:
            view.add_point(1.0, 1.0, True)
            
            # Получаем созданный эллипс
            args = mock_add_item.call_args[0][0]
            rect = args.rect()
            
            # Проверяем координаты (центр точки должен быть в (400,0))
            expected_x = view.center_x + 1.0 * view.scale_x
            expected_y = view.center_y - 1.0 * view.scale_y
            
            # Центр эллипса должен быть в вычисленных координатах
            # Добавляем допуск из-за размеров точки
            assert abs(rect.x() + rect.width()/2 - expected_x) < 2
            assert abs(rect.y() + rect.height()/2 - expected_y) < 2


class TestMainWindow:
    """Тесты для главного окна"""

    def test_initialization(self, qapp):
        """Тест инициализации главного окна"""
        window = MainWindow()
        
        assert window.windowTitle() == "Вычисление числа π методом Монте-Карло"
        assert window.graphics_view is not None
        assert window.start_button is not None
        assert window.pause_button is not None
        assert window.stop_button is not None
        assert window.clear_button is not None

    def test_initial_button_states(self, qapp):
        """Тест начального состояния кнопок"""
        window = MainWindow()
        
        assert window.start_button.isEnabled() is True
        assert window.pause_button.isEnabled() is False
        assert window.stop_button.isEnabled() is False
        assert window.points_spinbox.isEnabled() is True

    def test_points_spinbox_range(self, qapp):
        """Тест диапазона значений spinbox"""
        window = MainWindow()
        
        assert window.points_spinbox.minimum() == 100
        assert window.points_spinbox.maximum() == 1000000
        assert window.points_spinbox.value() == 10000

    def test_get_points_count(self, qapp):
        """Тест получения количества точек"""
        window = MainWindow()
        window.points_spinbox.setValue(50000)
        
        assert window.get_points_count() == 50000

    def test_update_stats(self, qapp):
        """Тест обновления статистики"""
        window = MainWindow()
        
        processed = 1000
        in_circle = 785
        pi_estimate = 3.14159  # Используем значение близкое к π
        elapsed_time = 1.5
        
        window.update_stats(processed, in_circle, pi_estimate, elapsed_time)
        
        assert window.pi_label.text() == f"{pi_estimate:.6f}"
        assert window.processed_label.text() == str(processed)
        assert window.in_circle_label.text() == str(in_circle)
        assert window.time_label.text() == f"{elapsed_time:.3f} с"
        
        # Проверяем вычисление погрешности с разумным допуском
        expected_error = abs(pi_estimate - math.pi)
        actual_error = float(window.error_label.text())
        
        # Используем относительную погрешность 1e-3 вместо 1e-6 из-за округления до 6 знаков
        assert abs(actual_error - expected_error) < 1e-6
        
        # Проверяем отношение
        expected_ratio = in_circle / processed
        assert float(window.ratio_label.text()) == pytest.approx(expected_ratio, rel=1e-4)
        
        # Проверяем прогресс бар
        expected_progress = int(processed / window.get_points_count() * 100)
        assert window.progress_bar.value() == expected_progress

    def test_reset_stats(self, qapp):
        """Тест сброса статистики"""
        window = MainWindow()
        
        # Устанавливаем некоторые значения
        window.update_stats(1000, 785, 3.14159, 1.5)
        
        # Сбрасываем
        window.reset_stats()
        
        assert window.pi_label.text() == "0.000000"
        assert window.error_label.text() == "0.000000"
        assert window.processed_label.text() == "0"
        assert window.in_circle_label.text() == "0"
        assert window.ratio_label.text() == "0.0000"
        assert window.time_label.text() == "0.000 с"
        assert window.progress_bar.value() == 0

    def test_button_enabling(self, qapp):
        """Тест включения/отключения кнопок"""
        window = MainWindow()
        
        window.set_start_button_enabled(False)
        assert window.start_button.isEnabled() is False
        window.set_start_button_enabled(True)
        assert window.start_button.isEnabled() is True
        
        window.set_pause_button_enabled(True)
        assert window.pause_button.isEnabled() is True
        window.set_pause_button_enabled(False)
        assert window.pause_button.isEnabled() is False
        
        window.set_stop_button_enabled(True)
        assert window.stop_button.isEnabled() is True
        window.set_stop_button_enabled(False)
        assert window.stop_button.isEnabled() is False
        
        window.set_points_spinbox_enabled(False)
        assert window.points_spinbox.isEnabled() is False
        window.set_points_spinbox_enabled(True)
        assert window.points_spinbox.isEnabled() is True

    def test_pause_button_text(self, qapp):
        """Тест изменения текста кнопки паузы"""
        window = MainWindow()
        
        window.set_pause_button_text("▶ Продолжить")
        assert window.pause_button.text() == "▶ Продолжить"
        
        window.set_pause_button_text("⏸ Пауза")
        assert window.pause_button.text() == "⏸ Пауза"

    def test_clear_graphics_view(self, qapp):
        """Тест очистки графического представления"""
        window = MainWindow()
        
        # Добавляем точки
        window.graphics_view.add_point(0.1, 0.1, True)
        window.graphics_view.add_point(0.8, 0.8, False)
        
        assert window.graphics_view.get_points_count() == 2
        
        window.clear_graphics_view()
        
        assert window.graphics_view.get_points_count() == 0

    def test_update_stats_edge_cases(self, qapp):
        """Тест обновления статистики в граничных случаях"""
        window = MainWindow()
        
        # Тест с нулевым количеством обработанных точек
        window.update_stats(0, 0, 0, 0)
        assert window.ratio_label.text() == "0.0000"
        assert window.pi_label.text() == "0.000000"
        assert window.progress_bar.value() == 0
        
        # Тест с максимальным прогрессом
        window.points_spinbox.setValue(1000)
        window.update_stats(1000, 785, 3.14159, 1.5)
        assert window.progress_bar.value() == 100

    def test_update_stats_formats(self, qapp):
        """Тест форматирования значений в статистике"""
        window = MainWindow()
        
        # Проверяем форматирование больших чисел
        window.update_stats(1000000, 785398, 3.14159, 123.456)
        assert window.processed_label.text() == "1000000"
        assert window.time_label.text() == "123.456 с"
        
        # Проверяем форматирование малых чисел
        window.update_stats(1, 0, 0.0, 0.001)
        assert window.pi_label.text() == "0.000000"
        assert window.time_label.text() == "0.001 с"