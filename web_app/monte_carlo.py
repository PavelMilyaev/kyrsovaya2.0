import random
import math
import time
from collections import deque


class MonteCarloCalculator:
    """Класс для вычисления π методом Монте-Карло"""

    def __init__(self, total_points=10000):
        self.total_points = total_points
        self.points_processed = 0
        self.points_in_circle = 0
        self.pi_estimate = 0
        self.is_running = False

        # Храним последние результаты
        self.latest_results = {}
        self.latest_points = deque(maxlen=1000)  # Ограничиваем для производительности

    def calculate(self):
        """Выполнить расчет"""
        self.is_running = True
        self.points_processed = 0
        self.points_in_circle = 0
        self.pi_estimate = 0

        for i in range(self.total_points):
            if not self.is_running:
                break

            # Генерация случайной точки
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)

            # Проверка, попадает ли точка в круг
            distance = x ** 2 + y ** 2
            in_circle = distance <= 1.0

            if in_circle:
                self.points_in_circle += 1

            self.points_processed += 1

            # Расчет π
            if self.points_processed > 0:
                self.pi_estimate = 4 * self.points_in_circle / self.points_processed

            # Сохраняем точку для визуализации (каждую 10-ю для производительности)
            if i % 10 == 0:
                self.latest_points.append({
                    'x': x,
                    'y': y,
                    'in_circle': in_circle
                })

            # Обновляем результаты каждые 100 точек
            if i % 100 == 0:
                self.latest_results = {
                    'points_processed': self.points_processed,
                    'points_in_circle': self.points_in_circle,
                    'pi_estimate': self.pi_estimate,
                    'progress': (i + 1) / self.total_points * 100
                }

            # Небольшая задержка для визуализации
            if self.total_points <= 10000:
                time.sleep(0.001)

        # Финальное обновление
        self.latest_results = {
            'points_processed': self.points_processed,
            'points_in_circle': self.points_in_circle,
            'pi_estimate': self.pi_estimate,
            'progress': 100
        }

        self.is_running = False

    def stop(self):
        """Остановить расчет"""
        self.is_running = False

    def get_progress(self):
        """Получить прогресс расчета"""
        if self.total_points > 0:
            return (self.points_processed / self.total_points) * 100
        return 0

    def get_latest_results(self):
        """Получить последние результаты"""
        return self.latest_results.copy()

    def get_latest_points(self):
        """Получить последние точки"""
        points = list(self.latest_points)
        self.latest_points.clear()  # Очищаем после получения
        return points