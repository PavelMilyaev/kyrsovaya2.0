# tests/web/test_monte_carlo.py
"""Тесты для класса MonteCarloCalculator"""
import threading

import pytest
import time
from unittest.mock import patch, Mock
import sys
import os

# Добавляем путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from web_app.monte_carlo import MonteCarloCalculator


class TestMonteCarloCalculator:
    """Тесты для класса MonteCarloCalculator"""

    def test_initialization(self):
        """Тест инициализации калькулятора"""
        calculator = MonteCarloCalculator(total_points=5000)

        assert calculator.total_points == 5000
        assert calculator.points_processed == 0
        assert calculator.points_in_circle == 0
        assert calculator.pi_estimate == 0
        assert calculator.is_running is False
        assert len(calculator.latest_points) == 0
        assert calculator.latest_results == {}

    def test_calculate_basic(self):
        """Тест базового расчета"""
        calculator = MonteCarloCalculator(total_points=100)
        calculator.calculate()

        assert calculator.points_processed == 100
        assert calculator.points_in_circle >= 0
        assert calculator.pi_estimate > 0
        assert calculator.is_running is False
        assert 2.0 <= calculator.pi_estimate <= 4.0

    def test_calculate_with_mock(self):
        """Тест расчета с моком для предсказуемых результатов"""
        calculator = MonteCarloCalculator(total_points=1000)

        with patch('random.uniform') as mock_uniform:
            # Все точки внутри круга
            mock_uniform.return_value = 0.5
            calculator.calculate()

            assert calculator.points_in_circle == 1000
            assert calculator.pi_estimate == 4.0

    def test_stop_calculation(self):
        """Тест остановки расчета"""
        calculator = MonteCarloCalculator(total_points=10000)

        # Запускаем в отдельном потоке
        import threading

        def stop_after_delay():
            time.sleep(0.1)
            calculator.stop()

        thread = threading.Thread(target=stop_after_delay)
        thread.start()

        calculator.calculate()
        thread.join()

        assert calculator.points_processed < 10000
        assert calculator.is_running is False

    def test_get_progress(self):
        """Тест получения прогресса"""
        calculator = MonteCarloCalculator(total_points=1000)
        
        # Запускаем расчет и сразу проверяем прогресс
        def run_in_thread():
            calculator.calculate()
        
        thread = threading.Thread(target=run_in_thread)
        thread.start()
        
        time.sleep(0.1)
        progress = calculator.get_progress()
        assert 0 <= progress <= 100
        
        calculator.stop()
        thread.join()

    def test_latest_results_update(self):
        """Тест обновления последних результатов"""
        calculator = MonteCarloCalculator(total_points=500)

        with patch('random.uniform') as mock_uniform:
            mock_uniform.return_value = 0.5
            calculator.calculate()

            results = calculator.get_latest_results()

            assert 'points_processed' in results
            assert 'points_in_circle' in results
            assert 'pi_estimate' in results
            assert 'progress' in results
            assert results['points_processed'] == 500
            assert results['progress'] == 100

    def test_latest_points_storage(self):
        """Тест хранения последних точек"""
        calculator = MonteCarloCalculator(total_points=200)  # Уменьшаем количество точек
        
        # Создаем список значений для random.uniform (по 2 значения на точку)
        # 200 точек = 400 значений
        mock_values = []
        for i in range(200):
            mock_values.extend([0.1, 0.2])  # x и y для каждой точки
        
        with patch('random.uniform', side_effect=mock_values):
            calculator.calculate()
            
            points = calculator.get_latest_points()
            
            # Проверяем, что точки сохраняются (каждая 10-я)
            # Для 200 точек должно быть 20 точек (200/10)
            assert len(points) == 20
            
            # Проверяем структуру точки
            if points:
                first_point = points[0]
                assert 'x' in first_point
                assert 'y' in first_point
                assert 'in_circle' in first_point
                assert isinstance(first_point['x'], float)
                assert isinstance(first_point['y'], float)
                assert isinstance(first_point['in_circle'], bool)
                
                # Проверяем, что первая точка имеет ожидаемые координаты
                assert first_point['x'] == 0.1
                assert first_point['y'] == 0.2

    def test_latest_points_storage_with_different_intervals(self):
        """Тест хранения точек с разными интервалами"""
        # Тест для проверки, что каждая 10-я точка сохраняется
        
        test_cases = [
            (100, 10),   # 100 точек, ожидаем 10 сохраненных (каждая 10-я)
            (150, 15),   # 150 точек, ожидаем 15 сохраненных
            (250, 25),   # 250 точек, ожидаем 25 сохраненных
        ]
        
        for total_points, expected_points in test_cases:
            calculator = MonteCarloCalculator(total_points=total_points)
            
            # Создаем уникальные значения для каждой точки
            mock_values = []
            for i in range(total_points):
                mock_values.extend([i/1000, (i+1)/1000])  # разные x и y
            
            with patch('random.uniform', side_effect=mock_values):
                calculator.calculate()
                points = calculator.get_latest_points()
                
                # Проверяем количество сохраненных точек
                assert len(points) == expected_points, \
                    f"Для {total_points} точек ожидалось {expected_points}, получено {len(points)}"

    def test_latest_points_clear_after_get(self):
        """Тест очистки точек после получения"""
        calculator = MonteCarloCalculator(total_points=100)
        
        # Создаем мок-значения
        mock_values = [0.1, 0.2] * 100  # 200 значений для 100 точек
        
        with patch('random.uniform', side_effect=mock_values):
            calculator.calculate()
            
            assert len(calculator.latest_points) > 0
            
            points = calculator.get_latest_points()
            assert len(points) > 0
            assert len(calculator.latest_points) == 0  # Очистилось после получения

    def test_latest_points_max_limit(self):
        """Тест ограничения на количество хранимых точек"""
        calculator = MonteCarloCalculator(total_points=20000)  # Больше чем maxlen=1000
        
        # Создаем мок-значения
        mock_values = [0.1, 0.2] * 20000
        
        with patch('random.uniform', side_effect=mock_values):
            calculator.calculate()
            
            points = calculator.get_latest_points()
            
            # Должно быть не больше 1000 точек (maxlen)
            assert len(points) <= 1000

    def test_boundary_conditions(self):
        """Тест граничных условий"""
        calculator = MonteCarloCalculator(total_points=4)

        boundary_points = [
            1.0, 0.0,   # на границе справа
            -1.0, 0.0,  # на границе слева
            0.0, 1.0,   # на границе сверху
            0.0, -1.0,  # на границе снизу
        ]

        with patch('random.uniform', side_effect=boundary_points):
            calculator.calculate()

            assert calculator.points_in_circle == 4
            assert calculator.pi_estimate == 4.0
            
            # Проверяем, что точки на границе помечены как внутри круга
            points = calculator.get_latest_points()
            for point in points:
                assert point['in_circle'] is True

    @pytest.mark.parametrize("total_points", [100, 500, 1000])
    def test_calculation_with_different_sizes(self, total_points):
        """Тест расчета с разным количеством точек"""
        calculator = MonteCarloCalculator(total_points=total_points)
        
        # Создаем достаточно мок-значений
        mock_values = [0.1, 0.2] * total_points
        
        with patch('random.uniform', side_effect=mock_values):
            calculator.calculate()
            
            assert calculator.points_processed == total_points
            # Количество сохраненных точек = total_points // 10 + (1 если total_points % 10 != 0)
            expected_points = total_points // 10 + (1 if total_points % 10 != 0 else 0)
            assert len(calculator.get_latest_points()) <= expected_points

    def test_calculation_with_real_random(self):
        """Тест расчета с реальными случайными числами (без мока)"""
        calculator = MonteCarloCalculator(total_points=1000)
        calculator.calculate()
        
        assert calculator.points_processed == 1000
        assert 3.0 <= calculator.pi_estimate <= 3.3  # Примерная оценка
        
        points = calculator.get_latest_points()
        assert len(points) > 0
        
        # Проверяем, что есть и точки внутри, и снаружи круга
        in_circle_count = sum(1 for p in points if p['in_circle'])
        assert 0 < in_circle_count < len(points)