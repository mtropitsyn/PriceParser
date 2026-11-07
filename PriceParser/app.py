from flask import Flask, render_template, request, jsonify
from database import get_connection, init_database
from parser import parse_product
import time

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/add_product', methods=['POST'])
def add_product():
    url = request.form.get('url', '').strip()
    if not url.startswith('http'):
        return jsonify({'success': False, 'message': 'Некорректный URL'})

    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id FROM products WHERE url = ?', (url,))
        if cursor.fetchone():
            conn.close()
            return jsonify({'success': False, 'message': 'Товар уже добавлен'})

        # Сразу пытаемся спарсить название и цену
        product_data = parse_product(url)
        name = product_data['name'] if product_data else url.split('/')[-1]

        cursor.execute('INSERT INTO products (url, name) VALUES (?, ?)', (url, name))
        product_id = cursor.lastrowid

        if product_data and product_data['price'] > 0:
            cursor.execute('INSERT INTO prices (product_id, price, shop) VALUES (?, ?, ?)',
                           (product_id, product_data['price'], 'vodoparad.ru'))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Товар добавлен и спарсен!'})

    except Exception as e:
        return jsonify({'success': False, 'message': f'Ошибка: {str(e)}'})

@app.route('/get_products')
def get_products():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.url, p.name,
                   (SELECT price FROM prices WHERE product_id = p.id ORDER BY parsed_at DESC LIMIT 1) as price,
                   (SELECT shop FROM prices WHERE product_id = p.id ORDER BY parsed_at DESC LIMIT 1) as shop
            FROM products p ORDER BY p.id DESC
        ''')
        rows = cursor.fetchall()
        conn.close()

        products = []
        for row in rows:
            products.append({
                'id': row[0],
                'url': row[1],
                'name': row[2] or "Товар без названия",
                'price': row[3],
                'shop': row[4] or 'vodoparad.ru'
            })
        return jsonify(products)
    except:
        return jsonify([])

@app.route('/run_parser', methods=['POST'])
def run_parser():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, url FROM products')
        products = cursor.fetchall()
        conn.close()

        if not products:
            return jsonify({'success': True, 'message': 'Нет товаров для парсинга'})

        success_count = 0
        for product_id, url in products:
            data = parse_product(url)
            if data and data['price'] > 0:
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute('INSERT INTO prices (product_id, price, shop) VALUES (?, ?, ?)',
                               (product_id, data['price'], 'vodoparad.ru'))
                cursor.execute('UPDATE products SET name = ? WHERE id = ?', (data['name'], product_id))
                conn.commit()
                conn.close()
                success_count += 1
            time.sleep(1)  # Вежливость к сайту

        return jsonify({
            'success': True,
            'message': f'Спаршено {success_count} из {len(products)} товаров'
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/update_product/<int:product_id>', methods=['POST'])
def update_single(product_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT url FROM products WHERE id = ?', (product_id,))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return jsonify({'success': False, 'message': 'Товар не найден'})

        url = row[0]
        data = parse_product(url)
        if not data or data['price'] <= 0:
            return jsonify({'success': False, 'message': 'Не удалось спарсить цену'})

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('INSERT INTO prices (product_id, price, shop) VALUES (?, ?, ?)',
                       (product_id, data['price'], 'vodoparad.ru'))
        cursor.execute('UPDATE products SET name = ? WHERE id = ?', (data['name'], product_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Обновлено', 'price': data['price']})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Удаляем цены
        cursor.execute('DELETE FROM prices WHERE product_id = ?', (product_id,))
        # Удаляем товар
        cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Товар удалён'})

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/get_logs')
def get_logs():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, product_url, status, price, shop_name, message, parsed_at
            FROM parsing_log
            ORDER BY parsed_at DESC
            LIMIT 50  -- Последние 50 записей для производительности
        ''')
        logs = []
        for row in cursor.fetchall():
            logs.append({
                'id': row[0],
                'url': row[1],
                'status': row[2],
                'price': row[3],
                'shop': row[4],
                'message': row[5],
                'time': row[6]
            })
        conn.close()
        return jsonify(logs)
    except:
        return jsonify([])

if __name__ == '__main__':
    init_database()
    print("PriceParser: http://localhost:5000")
    app.run(host="127.0.0.1", port=5000)