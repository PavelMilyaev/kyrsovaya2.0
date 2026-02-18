"""Тесты для контроллера (controller.py)"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from desktop_app.controller import AppController
from desktop_app.model import MonteCarloWorker


class TestAppController:
    """Тесты для контроллера"""

    @pytest.fixture
    def mock_view(self):
        """Фикстура для мока представления"""
        view = Mock()
        view.get_points_count.return_value = 5000
        view.pause_button = Mock()
        view.pause_button.text.return_value = "⏸ Пауза"
        return view

    @pytest.fixture
    def controller(self, mock_view):
        """Фикстура для контроллера"""
        return AppController(mock_view)

    def test_initialization(self, controller, mock_view):
        """Тест инициализации контроллера"""
        assert controller.view == mock_view
        assert controller.worker is None

    def test_start_calculation(self, controller, mock_view):
        """Тест запуска расчета"""
        with patch('desktop_app.controller.MonteCarloWorker') as MockWorker:
            mock_worker = Mock()
            MockWorker.return_value = mock_worker

            controller.start_calculation()

            # Проверяем создание worker
            MockWorker.assert_called_once_with(5000)

            # Проверяем подключение сигналов
            mock_worker.progress_updated.connect.assert_called_once_with(mock_view.update_stats)
            mock_worker.calculation_finished.connect.assert_called_once()
            mock_worker.point_plotted.connect.assert_called_once_with(mock_view.add_point_to_view)

            # Проверяем изменение состояния UI
            mock_view.clear_graphics_view.assert_called_once()
            mock_view.set_start_button_enabled.assert_called_with(False)
            mock_view.set_pause_button_enabled.assert_called_with(True)
            mock_view.set_stop_button_enabled.assert_called_with(True)
            mock_view.set_points_spinbox_enabled.assert_called_with(False)
            mock_view.reset_stats.assert_called_once()

            # Проверяем запуск потока
            mock_worker.start.assert_called_once()

    def test_start_calculation_when_running(self, controller):
        """Тест запуска расчета, когда уже выполняется"""
        # Создаем worker, который уже запущен
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        controller.worker = mock_worker

        with patch('desktop_app.controller.MonteCarloWorker') as MockWorker:
            controller.start_calculation()

            # Не должен создавать новый worker
            MockWorker.assert_not_called()

    def test_pause_calculation(self, controller, mock_view):
        """Тест паузы расчета"""
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        controller.worker = mock_worker

        # Тест паузы
        mock_view.pause_button.text.return_value = "⏸ Пауза"
        controller.pause_calculation()

        mock_worker.stop.assert_called_once()
        mock_view.set_pause_button_text.assert_called_with("▶ Продолжить")

    def test_resume_calculation(self, controller, mock_view):
        """Тест возобновления расчета"""
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        controller.worker = mock_worker

        # Тест возобновления
        mock_view.pause_button.text.return_value = "▶ Продолжить"
        controller.pause_calculation()

        assert mock_worker.running is True
        mock_worker.start.assert_called_once()
        mock_view.set_pause_button_text.assert_called_with("⏸ Пауза")

    def test_stop_calculation(self, controller, mock_view):
        """Тест остановки расчета"""
        mock_worker = Mock()
        mock_worker.isRunning.return_value = True
        mock_worker.pi_estimate = 3.14
        controller.worker = mock_worker

        controller.stop_calculation()

        mock_worker.stop.assert_called_once()
        mock_worker.wait.assert_called_once()

    def test_clear_graph(self, controller, mock_view):
        """Тест очистки графика"""
        controller.clear_graph()

        mock_view.clear_graphics_view.assert_called_once()
        mock_view.reset_stats.assert_called_once()

    def test_calculation_done(self, controller, mock_view):
        """Тест завершения расчета"""
        pi_estimate = 3.14159
        elapsed_time = 2.5
        circle_points = [(0.1, 0.1), (0.2, 0.2)]
        square_points = [(0.8, 0.8)]

        controller.calculation_done(pi_estimate, elapsed_time, circle_points, square_points)

        # Проверяем обновление UI
        mock_view.set_start_button_enabled.assert_called_with(True)
        mock_view.set_pause_button_enabled.assert_called_with(False)
        mock_view.set_pause_button_text.assert_called_with("⏸ Пауза")
        mock_view.set_stop_button_enabled.assert_called_with(False)
        mock_view.set_points_spinbox_enabled.assert_called_with(True)

        # Проверяем обновление статистики
        mock_view.update_stats.assert_called_once_with(
            len(circle_points) + len(square_points),
            len(circle_points),
            pi_estimate,
            elapsed_time
        )

        mock_view.print_final_result.assert_called_once_with(pi_estimate, elapsed_time)

