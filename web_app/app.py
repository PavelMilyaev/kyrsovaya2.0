from flask import Flask, render_template, jsonify, request
import json
import time
import threading
from monte_carlo import MonteCarloCalculator

app = Flask(__name__)

# Глобальный объект для хранения состояния вычислений
calculations = {}
calculation_lock = threading.Lock()


@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')


@app.route('/api/start', methods=['POST'])
def start_calculation():
    """Начать новое вычисление"""
    data = request.json
    total_points = int(data.get('total_points', 10000))

    # Создаем уникальный ID для расчета
    calc_id = str(int(time.time() * 1000))

    # Создаем и запускаем калькулятор в отдельном потоке
    calculator = MonteCarloCalculator(total_points)

    with calculation_lock:
        calculations[calc_id] = {
            'calculator': calculator,
            'status': 'running',
            'start_time': time.time(),
            'results': [],
            'points': [],
            'last_update': time.time()
        }

    # Запускаем расчет в отдельном потоке
    thread = threading.Thread(
        target=run_calculation,
        args=(calc_id, calculator)
    )
    thread.daemon = True
    thread.start()

    return jsonify({
        'success': True,
        'calc_id': calc_id,
        'message': 'Расчет начат'
    })


@app.route('/api/stop/<calc_id>', methods=['POST'])
def stop_calculation(calc_id):
    """Остановить вычисление"""
    with calculation_lock:
        if calc_id in calculations:
            calculations[calc_id]['status'] = 'stopped'
            return jsonify({'success': True, 'message': 'Расчет остановлен'})
    return jsonify({'success': False, 'message': 'Расчет не найден'})


@app.route('/api/status/<calc_id>')
def get_status(calc_id):
    """Получить статус вычисления"""
    with calculation_lock:
        if calc_id in calculations:
            calc_data = calculations[calc_id]

            # Получаем последние результаты
            results = calc_data['calculator'].get_latest_results()
            points = calc_data['calculator'].get_latest_points()

            status = {
                'status': calc_data['status'],
                'progress': calc_data['calculator'].get_progress(),
                'current_pi': results.get('pi_estimate', 0),
                'points_processed': results.get('points_processed', 0),
                'points_in_circle': results.get('points_in_circle', 0),
                'elapsed_time': time.time() - calc_data['start_time'],
                'points': points,
                'error': abs(results.get('pi_estimate', 0) - 3.141592653589793)
            }

            # Сохраняем результаты
            if results:
                calc_data['results'].append(results)
                calc_data['points'].extend(points)
                calc_data['last_update'] = time.time()

            return jsonify(status)

    return jsonify({
        'status': 'not_found',
        'message': 'Расчет не найден'
    })


def run_calculation(calc_id, calculator):
    """Запуск расчета в отдельном потоке"""
    calculator.calculate()


if __name__ == '__main__':
    app.run(debug=True, port=5000)