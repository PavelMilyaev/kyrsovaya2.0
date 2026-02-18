from desktop_app.model import MonteCarloWorker


class AppController:
    """Контроллер приложения (Controller)"""

    def __init__(self, view):
        self.view = view
        self.worker = None

    def start_calculation(self):
        """Запуск расчета"""
        if self.worker and self.worker.isRunning():
            return

        # Очищаем предыдущие точки
        self.view.clear_graphics_view()

        # Создаем и настраиваем поток
        self.worker = MonteCarloWorker(self.view.get_points_count())
        self.worker.progress_updated.connect(self.view.update_stats)
        self.worker.calculation_finished.connect(self.calculation_done)
        self.worker.point_plotted.connect(self.view.add_point_to_view)

        # Обновляем состояние кнопок
        self.view.set_start_button_enabled(False)
        self.view.set_pause_button_enabled(True)
        self.view.set_stop_button_enabled(True)
        self.view.set_points_spinbox_enabled(False)

        # Сбрасываем статистику
        self.view.reset_stats()

        # Запускаем поток
        self.worker.start()

    def pause_calculation(self):
        """Пауза/продолжение расчета"""
        if self.worker and self.worker.isRunning():
            if self.view.pause_button.text() == "⏸ Пауза":
                self.worker.stop()
                self.view.set_pause_button_text("▶ Продолжить")
            else:
                self.worker.running = True
                self.worker.start()
                self.view.set_pause_button_text("⏸ Пауза")

    def stop_calculation(self):
        """Остановка расчета"""
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.worker.wait()
            if self.worker.pi_estimate is not None:
                self.calculation_done(self.worker.pi_estimate, 0, [], [])

    def clear_graph(self):
        """Очистка графика"""
        self.view.clear_graphics_view()
        self.view.reset_stats()

    def calculation_done(self, pi_estimate, elapsed_time, circle_points, square_points):
        """Обработка завершения расчета"""
        # Обновляем состояние кнопок
        self.view.set_start_button_enabled(True)
        self.view.set_pause_button_enabled(False)
        self.view.set_pause_button_text("⏸ Пауза")
        self.view.set_stop_button_enabled(False)
        self.view.set_points_spinbox_enabled(True)

        # Финальное обновление статистики
        total_points = len(circle_points) + len(square_points)
        self.view.update_stats(
            total_points,
            len(circle_points),
            pi_estimate,
            elapsed_time
        )

        # Выводим финальный результат
        self.view.print_final_result(pi_estimate, elapsed_time)