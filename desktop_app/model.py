import random
import time
from PySide6.QtCore import QThread, Signal


class MonteCarloWorker(QThread):
    """Класс для выполнения вычислений Монте-Карло в отдельном потоке (Model)"""
    progress_updated = Signal(int, int, float, float)  # сигнал обновления прогресса
    calculation_finished = Signal(float, float, list, list)  # сигнал завершения расчета
    point_plotted = Signal(float, float, bool)  # сигнал для отрисовки точек

    def __init__(self, total_points=10000):
        super().__init__()
        self.total_points = total_points
        self.points_in_circle = 0
        self.points_processed = 0
        self.pi_estimate = 0
        self.circle_points = []
        self.square_points = []
        self.running = True

    def run(self):
        """Основной метод потока - выполняет расчет"""
        self.points_in_circle = 0
        self.points_processed = 0
        self.circle_points = []
        self.square_points = []

        start_time = time.time()

        for i in range(self.total_points):
            if not self.running:
                break

            # Генерация случайных точек
            x = random.uniform(-1, 1)
            y = random.uniform(-1, 1)

            # Проверка, попадает ли точка в круг
            distance = x ** 2 + y ** 2
            in_circle = distance <= 1.0

            if in_circle:
                self.points_in_circle += 1
                self.circle_points.append((x, y))
            else:
                self.square_points.append((x, y))

            self.points_processed += 1

            # Расчет текущего значения π
            if self.points_processed > 0:
                self.pi_estimate = 4 * self.points_in_circle / self.points_processed

            # Отправка сигналов для обновления интерфейса
            self.point_plotted.emit(x, y, in_circle)

            # Отправка сигнала прогресса каждые 100 точек
            if self.points_processed % 100 == 0:
                elapsed_time = time.time() - start_time
                self.progress_updated.emit(
                    self.points_processed,
                    self.points_in_circle,
                    self.pi_estimate,
                    elapsed_time
                )

            # Небольшая задержка для визуализации процесса
            if self.total_points <= 10000:
                time.sleep(0.001)

        # Финальное обновление
        elapsed_time = time.time() - start_time
        self.progress_updated.emit(
            self.points_processed,
            self.points_in_circle,
            self.pi_estimate,
            elapsed_time
        )
        self.calculation_finished.emit(
            self.pi_estimate,
            elapsed_time,
            self.circle_points,
            self.square_points
        )

    def stop(self):
        """Остановка вычислений"""
        self.running = False

    def set_total_points(self, total_points):
        """Установка общего количества точек"""
        self.total_points = total_points