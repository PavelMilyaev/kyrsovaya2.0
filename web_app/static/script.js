class MonteCarloWebApp {
    constructor() {
        this.calcId = null;
        this.isRunning = false;
        this.isPaused = false;
        this.points = [];
        this.canvas = document.getElementById('monteCarloCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.animationId = null;

        this.initCanvas();
        this.bindEvents();
        this.loadHistory();
    }

    initCanvas() {
        // Очищаем canvas
        this.ctx.fillStyle = 'white';
        this.ctx.fillRect(0, 0, this.canvas.width, this.canvas.height);

        // Рисуем квадрат
        this.ctx.strokeStyle = '#333';
        this.ctx.lineWidth = 2;
        this.ctx.strokeRect(50, 50, 400, 400);

        // Рисуем круг
        this.ctx.beginPath();
        this.ctx.arc(250, 250, 200, 0, 2 * Math.PI);
        this.ctx.strokeStyle = '#dc3545';
        this.ctx.stroke();

        // Рисуем оси
        this.ctx.strokeStyle = '#ccc';
        this.ctx.lineWidth = 1;
        this.ctx.setLineDash([5, 3]);

        // Вертикальная ось
        this.ctx.beginPath();
        this.ctx.moveTo(250, 50);
        this.ctx.lineTo(250, 450);
        this.ctx.stroke();

        // Горизонтальная ось
        this.ctx.beginPath();
        this.ctx.moveTo(50, 250);
        this.ctx.lineTo(450, 250);
        this.ctx.stroke();

        this.ctx.setLineDash([]);

        // Подписи
        this.ctx.fillStyle = '#666';
        this.ctx.font = '12px Arial';
        this.ctx.fillText('1', 230, 40);
        this.ctx.fillText('-1', 230, 465);
        this.ctx.fillText('1', 460, 240);
        this.ctx.fillText('-1', 35, 240);
        this.ctx.fillText('0', 240, 240);
    }

    bindEvents() {
        // Кнопки управления
        document.getElementById('startBtn').addEventListener('click', () => this.startCalculation());
        document.getElementById('pauseBtn').addEventListener('click', () => this.togglePause());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopCalculation());
        document.getElementById('clearBtn').addEventListener('click', () => this.clearCanvas());

        // Синхронизация слайдера и поля ввода
        const pointsRange = document.getElementById('pointsRange');
        const pointsCount = document.getElementById('pointsCount');

        pointsRange.addEventListener('input', (e) => {
            pointsCount.value = e.target.value;
        });

        pointsCount.addEventListener('input', (e) => {
            let value = Math.min(Math.max(100, parseInt(e.target.value) || 100), 1000000);
            pointsCount.value = value;
            pointsRange.value = value;
        });
    }

    async startCalculation() {
        if (this.isRunning) return;

        const pointsCount = parseInt(document.getElementById('pointsCount').value);

        try {
            const response = await fetch('/api/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ total_points: pointsCount })
            });

            const data = await response.json();

            if (data.success) {
                this.calcId = data.calc_id;
                this.isRunning = true;
                this.isPaused = false;

                // Обновляем UI
                document.getElementById('startBtn').disabled = true;
                document.getElementById('pauseBtn').disabled = false;
                document.getElementById('stopBtn').disabled = false;
                document.getElementById('pointsCount').disabled = true;
                document.getElementById('pointsRange').disabled = true;

                // Запускаем обновление статуса
                this.updateStatus();
                this.animate();
            }
        } catch (error) {
            console.error('Ошибка при запуске расчета:', error);
            alert('Ошибка при запуске расчета');
        }
    }

    async togglePause() {
        if (!this.isRunning) return;

        this.isPaused = !this.isPaused;

        if (this.isPaused) {
            document.getElementById('pauseBtn').innerHTML = '<i class="fas fa-play"></i> Продолжить';
        } else {
            document.getElementById('pauseBtn').innerHTML = '<i class="fas fa-pause"></i> Пауза';
            this.updateStatus();
        }
    }

    async stopCalculation() {
        if (!this.calcId) return;

        try {
            await fetch(`/api/stop/${this.calcId}`, {
                method: 'POST'
            });

            this.isRunning = false;
            this.isPaused = false;

            // Обновляем UI
            document.getElementById('startBtn').disabled = false;
            document.getElementById('pauseBtn').disabled = true;
            document.getElementById('stopBtn').disabled = true;
            document.getElementById('pointsCount').disabled = false;
            document.getElementById('pointsRange').disabled = false;
            document.getElementById('pauseBtn').innerHTML = '<i class="fas fa-pause"></i> Пауза';

            // Загружаем историю
            this.loadHistory();
        } catch (error) {
            console.error('Ошибка при остановке расчета:', error);
        }
    }

    async updateStatus() {
        if (!this.calcId || this.isPaused) return;

        try {
            const response = await fetch(`/api/status/${this.calcId}`);
            const data = await response.json();

            if (data.status === 'running' || data.status === 'stopped') {
                // Обновляем статистику
                document.getElementById('currentPi').textContent = data.current_pi.toFixed(6);
                document.getElementById('error').textContent = data.error.toFixed(6);
                document.getElementById('pointsProcessed').textContent = data.points_processed.toLocaleString();
                document.getElementById('pointsInCircle').textContent = data.points_in_circle.toLocaleString();
                document.getElementById('elapsedTime').textContent = data.elapsed_time.toFixed(3) + ' с';
                document.getElementById('progressPercent').textContent = data.progress.toFixed(1) + '%';

                // Обновляем формулу
                const ratio = data.points_in_circle / data.points_processed || 0;
                document.getElementById('ratioFormula').textContent = data.points_in_circle;
                document.getElementById('totalFormula').textContent = data.points_processed;
                document.getElementById('piFormula').textContent = data.current_pi.toFixed(6);

                // Обновляем отношение
                document.getElementById('ratio').textContent = ratio.toFixed(4);

                // Обновляем прогресс бар
                document.getElementById('progressFill').style.width = data.progress + '%';

                // Добавляем точки на canvas
                if (data.points && data.points.length > 0) {
                    data.points.forEach(point => {
                        this.addPoint(point.x, point.y, point.in_circle);
                    });
                }

                // Если расчет завершен, останавливаем обновление
                if (data.status === 'stopped') {
                    this.stopCalculation();
                } else {
                    // Продолжаем обновление
                    setTimeout(() => this.updateStatus(), 100);
                }
            }
        } catch (error) {
            console.error('Ошибка при обновлении статуса:', error);
            // Продолжаем попытки обновления
            if (this.isRunning && !this.isPaused) {
                setTimeout(() => this.updateStatus(), 1000);
            }
        }
    }

    addPoint(x, y, inCircle) {
        // Преобразуем координаты из [-1, 1] в [0, 400]
        const plotX = 250 + x * 200;
        const plotY = 250 - y * 200; // Инвертируем Y

        // Рисуем точку
        this.ctx.beginPath();
        this.ctx.arc(plotX, plotY, 2, 0, 2 * Math.PI);
        this.ctx.fillStyle = inCircle ? '#0066ff' : '#ff6600';
        this.ctx.fill();
    }

    clearCanvas() {
        // Останавливаем текущий расчет
        if (this.isRunning) {
            this.stopCalculation();
        }

        // Очищаем canvas
        this.initCanvas();
        this.points = [];

        // Сбрасываем статистику
        document.getElementById('currentPi').textContent = '0.000000';
        document.getElementById('error').textContent = '0.000000';
        document.getElementById('pointsProcessed').textContent = '0';
        document.getElementById('pointsInCircle').textContent = '0';
        document.getElementById('ratio').textContent = '0.0000';
        document.getElementById('elapsedTime').textContent = '0.000 с';
        document.getElementById('progressPercent').textContent = '0%';
        document.getElementById('progressFill').style.width = '0%';

        // Сбрасываем формулу
        document.getElementById('ratioFormula').textContent = '0';
        document.getElementById('totalFormula').textContent = '0';
        document.getElementById('piFormula').textContent = '0';
    }

    async loadHistory() {
        try {
            const response = await fetch('/api/history');
            const history = await response.json();

            const historyList = document.getElementById('historyList');

            if (history.length === 0) {
                historyList.innerHTML = '<div class="empty-history">Расчетов пока нет</div>';
                return;
            }

            let html = '';
            history.forEach(item => {
                html += `
                    <div class="history-item">
                        <div class="history-item-header">
                            <span class="history-id">Расчет #${item.id.slice(-6)}</span>
                            <span class="history-status ${item.status === 'running' ? 'status-running' : 'status-completed'}">
                                ${item.status === 'running' ? 'В процессе' : 'Завершен'}
                            </span>
                        </div>
                        <div class="history-stats">
                            Точек: ${item.total_points.toLocaleString()} |
                            π: ${item.final_pi.toFixed(6)} |
                            Погрешность: ${item.error.toFixed(6)} |
                            Время: ${item.time_spent.toFixed(2)} с
                        </div>
                    </div>
                `;
            });

            historyList.innerHTML = html;
        } catch (error) {
            console.error('Ошибка при загрузке истории:', error);
        }
    }

    animate() {
        if (!this.isRunning || this.isPaused) return;

        // Здесь можно добавить анимацию, если нужно
        this.animationId = requestAnimationFrame(() => this.animate());
    }
}

// Инициализация приложения при загрузке страницы
document.addEventListener('DOMContentLoaded', () => {
    window.monteCarloApp = new MonteCarloWebApp();
});