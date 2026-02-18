# tests/desktop/test_model.py
"""Тесты для модели (model.py)"""
import pytest
import time
from unittest.mock import Mock, patch, call
from desktop_app.model import MonteCarloWorker


class TestMonteCarloWorker:
    """Тесты для класса MonteCarloWorker"""

    def test_initialization(self):
        """Тест инициализации worker"""
        worker = MonteCarloWorker(total_points=5000)

        assert worker.total_points == 5000
        assert worker.points_in_circle == 0
        assert worker.points_processed == 0
        assert worker.pi_estimate == 0
        assert worker.circle_points == []
        assert worker.square_points == []
        assert worker.running is True

    def test_set_total_points(self):
        """Тест установки количества точек"""
        worker = MonteCarloWorker()
        worker.set_total_points(20000)
        assert worker.total_points == 20000

    def test_stop_calculation(self):
        """Тест остановки вычислений"""
        worker = MonteCarloWorker()
        assert worker.running is True

        worker.stop()
        assert worker.running is False

    @pytest.mark.slow
    def test_calculation_with_small_points(self):
        """Тест расчета с малым количеством точек"""
        worker = MonteCarloWorker(total_points=100)

        # Запускаем расчет
        worker.run()

        # Проверяем базовые результаты
        assert worker.points_processed == 100
        assert worker.points_in_circle >= 0
        assert worker.pi_estimate > 0

        # Проверяем, что π находится в разумных пределах
        assert 2.0 <= worker.pi_estimate <= 4.0

        # Проверяем, что точки распределены корректно
        assert len(worker.circle_points) + len(worker.square_points) == 100

    def test_calculation_mathematics(self):
        """Тест математической корректности вычислений"""
        worker = MonteCarloWorker(total_points=1000)

        # Мокаем random.uniform для предсказуемых результатов
        with patch('random.uniform') as mock_uniform:
            # Все точки внутри круга
            mock_uniform.return_value = 0.5
            worker.run()

            # Должны получить π ≈ 4 * 1000/1000 = 4
            assert worker.pi_estimate == 4.0
            assert len(worker.circle_points) == 1000
            assert len(worker.square_points) == 0

        # Сброс
        worker = MonteCarloWorker(total_points=1000)

        with patch('random.uniform') as mock_uniform:
            # Все точки вне круга (на границе и за ней)
            mock_uniform.return_value = 0.9
            worker.run()

            # Должны получить π ≈ 0
            assert worker.pi_estimate == 0
            assert len(worker.circle_points) == 0
            assert len(worker.square_points) == 1000

    def test_point_distribution(self):
        """Тест распределения точек по категориям"""
        worker = MonteCarloWorker(total_points=6)

        # Создаем предсказуемую последовательность точек
        test_points = [
            0.1, 0.1,  # (0.1, 0.1) - внутри круга
            0.9, 0.9,  # (0.9, 0.9) - вне круга
            0.5, 0.5,  # (0.5, 0.5) - внутри круга
            1.0, 0.0,  # (1.0, 0.0) - на границе (внутри)
            0.0, 0.0,  # (0.0, 0.0) - внутри круга
            0.8, 0.8,  # (0.8, 0.8) - вне круга
        ]

        with patch('random.uniform', side_effect=test_points):
            worker.run()

            # Проверяем результаты
            assert worker.points_processed == 6
            assert worker.points_in_circle == 4  # первые 3 + граница + центр
            assert len(worker.circle_points) == 4
            assert len(worker.square_points) == 2

            # Проверяем конкретные точки
            assert (0.1, 0.1) in worker.circle_points
            assert (0.9, 0.9) in worker.square_points
            assert (0.5, 0.5) in worker.circle_points
            # Проверяем, что (1.0, 0.0) в circle_points (на границе)
            assert any(abs(p[0] - 1.0) < 0.001 and abs(p[1]) < 0.001
                       for p in worker.circle_points)
            assert (0.0, 0.0) in worker.circle_points
            assert (0.8, 0.8) in worker.square_points

    def test_signal_emission(self):
        """Тест эмиссии сигналов"""
        # Создаем реальный worker
        worker = MonteCarloWorker(total_points=500)

        # Создаем моки для сигналов
        mock_progress = Mock()
        mock_finished = Mock()
        mock_point = Mock()

        # Подключаем моки к сигналам
        worker.progress_updated.connect(mock_progress)
        worker.calculation_finished.connect(mock_finished)
        worker.point_plotted.connect(mock_point)

        # Запускаем вычисления
        worker.run()

        # Проверяем, что сигналы вызывались
        assert mock_progress.called
        assert mock_finished.called
        assert mock_point.called

        # Проверяем количество вызовов point_plotted (должно быть 500)
        assert mock_point.call_count == 500

        # Проверяем количество вызовов progress_updated
        # Для 500 точек: каждые 100 точек (100,200,300,400,500) = 5 вызовов
        # Плюс финальный вызов после цикла = 6 вызовов
        expected_progress_calls = 6  # 5 в цикле + 1 финальный
        assert mock_progress.call_count == expected_progress_calls

        # Проверяем, что последние два вызова содержат правильные значения
        call_args_list = mock_progress.call_args_list

        # Предпоследний вызов (в цикле)
        second_last_args = call_args_list[-2][0]
        assert second_last_args[0] == 500

        # Последний вызов (финальный)
        last_args = call_args_list[-1][0]
        assert last_args[0] == 500

        # Проверяем, что значения совпадают
        assert second_last_args[1] == last_args[1]  # points_in_circle
        assert second_last_args[2] == last_args[2]  # pi_estimate

    def test_calculation_interruption(self):
        """Тест прерывания вычислений"""
        worker = MonteCarloWorker(total_points=10000)

        # Запускаем в отдельном потоке с прерыванием
        import threading

        def interrupt():
            time.sleep(0.1)
            worker.stop()

        thread = threading.Thread(target=interrupt)
        thread.start()

        worker.run()
        thread.join()

        # Проверяем, что вычисления были прерваны
        assert worker.points_processed < 10000
        assert worker.running is False

    @pytest.mark.parametrize("total_points", [100, 500, 1000, 5000])
    def test_calculation_with_different_sizes(self, total_points):
        """Тест расчета с разным количеством точек"""
        worker = MonteCarloWorker(total_points=total_points)
        worker.run()

        assert worker.points_processed == total_points
        assert len(worker.circle_points) + len(worker.square_points) == total_points

        # Проверяем, что pi_estimate вычислен
        assert worker.pi_estimate > 0

    def test_pi_accuracy(self):
        """Тест точности вычисления π"""
        import math

        worker = MonteCarloWorker(total_points=10000)
        worker.run()

        # Проверяем, что результат в пределах 0.1 от истинного значения
        error = abs(worker.pi_estimate - math.pi)
        assert error < 0.1, f"Погрешность {error} слишком велика"

        # Проверяем, что значение π в разумных пределах
        assert 3.0 <= worker.pi_estimate <= 3.3

    def test_boundary_conditions(self):
        """Тест граничных условий (точки на границе круга)"""
        worker = MonteCarloWorker(total_points=4)

        # Тестируем точки на границе круга
        boundary_points = [
            1.0, 0.0,  # на границе справа
            -1.0, 0.0,  # на границе слева
            0.0, 1.0,  # на границе сверху
            0.0, -1.0,  # на границе снизу
        ]

        with patch('random.uniform', side_effect=boundary_points):
            worker.run()

            # Все точки на границе должны считаться внутри круга
            assert worker.points_in_circle == 4
            assert worker.pi_estimate == 4.0

    def test_calculation_progress(self):
        """Тест обновления прогресса во время вычисления"""
        worker = MonteCarloWorker(total_points=1000)

        # Создаем список для отслеживания прогресса
        progress_values = []

        def track_progress(processed, in_circle, pi_estimate, elapsed):
            progress_values.append(processed)

        worker.progress_updated.connect(track_progress)

        worker.run()

        # Проверяем, что прогресс обновлялся каждые 100 точек
        # Должно быть: 100,200,300,400,500,600,700,800,900,1000,1000 (дубль в конце)
        expected_progress = [100, 200, 300, 400, 500, 600, 700, 800, 900, 1000, 1000]

        assert progress_values == expected_progress

        # Проверяем, что последние два значения равны 1000
        assert progress_values[-2] == 1000
        assert progress_values[-1] == 1000

    def test_elapsed_time_measurement(self):
        """Тест измерения времени выполнения"""
        worker = MonteCarloWorker(total_points=500)

        # Создаем список для хранения времени
        times = []

        def track_time(processed, in_circle, pi_estimate, elapsed):
            times.append(elapsed)

        worker.progress_updated.connect(track_time)

        start_real_time = time.time()
        worker.run()
        end_real_time = time.time()

        # Проверяем, что время увеличивается
        assert len(times) > 0
        assert all(times[i] <= times[i + 1] for i in range(len(times) - 1))

        # Проверяем, что измеренное время примерно соответствует реальному
        total_measured_time = times[-1] if times else 0
        real_time = end_real_time - start_real_time
        assert abs(total_measured_time - real_time) < 1.0  # допуск 1 секунда

    def test_progress_signal_pattern(self):
        """Тест паттерна сигналов прогресса"""
        worker = MonteCarloWorker(total_points=500)

        progress_values = []

        def track_progress(processed, *args):
            progress_values.append(processed)

        worker.progress_updated.connect(track_progress)
        worker.run()

        # Проверяем, что сигналы приходят в правильном порядке
        # Должны быть значения: 100,200,300,400,500,500 (дубль в конце)
        assert len(progress_values) == 6

        # Первые 5 значений должны быть уникальными
        assert len(set(progress_values[:-1])) == 5

        # Последние два значения должны быть одинаковыми (500)
        assert progress_values[-2] == 500
        assert progress_values[-1] == 500

        # Проверяем, что все значения кроме последнего уникальны
        for i in range(len(progress_values) - 2):
            assert progress_values[i] != progress_values[i + 1]