from flask import Flask, request, jsonify, session
import sqlite3
import hashlib
from datetime import datetime, time
import os

app = Flask(__name__)
app.secret_key = 'pdv_restaurant_secret_key_2024'

def get_db_connection():
    conn = sqlite3.connect('database/restaurant.db')
    conn.row_factory = sqlite3.Row
    return conn

def format_metical(value):
    return f"{value:,.2f} MT"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/api/categorias')
def get_categorias():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM categories ORDER BY name')
    categorias = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(categorias)

@app.route('/api/produtos')
def get_produtos():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name, description, price, stock FROM products WHERE stock > 0')
    produtos = []
    for row in cursor.fetchall():
        produtos.append({
            'id': row['id'],
            'name': row['name'],
            'description': row['description'] or '',
            'price': row['price'],
            'price_formatted': format_metical(row['price']),
            'stock': row['stock'],
            'has_variations': False
        })
    conn.close()
    return jsonify(produtos)

@app.route('/api/mesas')
def get_mesas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, number, capacity, status FROM tables ORDER BY number')
    mesas = []
    for row in cursor.fetchall():
        mesas.append({
            'id': row['id'],
            'name': f"Mesa {row['number']}",
            'capacity': row['capacity'],
            'status': row['status']
        })
    conn.close()
    return jsonify(mesas)

@app.route('/api/fazer_pedido', methods=['POST'])
def fazer_pedido():
    try:
        data = request.get_json()
        mesa_id = data.get('mesa_id')
        itens = data.get('itens', [])
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('INSERT INTO orders (table_id, status) VALUES (?, "pendente")', (mesa_id,))
        order_id = cursor.lastrowid
        total = 0
        
        for item in itens:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            cursor.execute('SELECT price FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            if product:
                unit_price = product['price']
                item_total = unit_price * quantity
                total += item_total
                
                cursor.execute('INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (?, ?, ?, ?)', 
                             (order_id, product_id, quantity, unit_price))
        
        cursor.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (total, order_id))
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'order_id': order_id, 'total': format_metical(total)})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            return jsonify({'success': True, 'redirect': '/funcionario/pedidos'})
        else:
            return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/restaurant-status')
def get_restaurant_status():
    return jsonify({'status': 'aberto', 'message': 'Aberto para pedidos', 'is_open': True})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False) 