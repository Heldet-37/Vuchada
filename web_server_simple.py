from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime, time
import os
from database.db import init_db

app = Flask(__name__, static_folder='static')
CORS(app)  # Permitir CORS para todas as origens
app.secret_key = 'pdv_restaurant_secret_key_2024'

# Inicializar banco de dados
try:
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao inicializar banco: {e}")

def get_db_connection():
    conn = sqlite3.connect('database/restaurant.db')
    conn.row_factory = sqlite3.Row
    return conn

def format_metical(value):
    return f"{value:,.2f} MT"

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/cliente')
def cliente():
    return send_from_directory('static', 'cliente.html')

@app.route('/funcionario')
def funcionario():
    return send_from_directory('static', 'funcionario.html')

@app.route('/funcionario/pedidos')
def funcionario_pedidos():
    return send_from_directory('static', 'funcionario_pedidos.html')

@app.route('/servicos')
def servicos():
    return send_from_directory('static', 'servicos.html')

@app.route('/sobre')
def sobre():
    return send_from_directory('static', 'sobre.html')

@app.route('/api')
def api_info():
    return jsonify({
        'status': 'ok',
        'message': 'PDV Restaurante API funcionando!',
        'endpoints': [
            '/api/categorias',
            '/api/produtos',
            '/api/mesas',
            '/test'
        ]
    })

@app.route('/test')
def test():
    return jsonify({'status': 'ok', 'message': 'Aplicação funcionando!'})

@app.route('/api/categorias')
def get_categorias():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories ORDER BY name')
        categorias = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        conn.close()
        return jsonify(categorias)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/produtos')
def get_produtos():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name, description, price, stock, image_url FROM products WHERE stock > 0')
        produtos = []
        for row in cursor.fetchall():
            produtos.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'] or '',
                'price': row['price'],
                'price_formatted': format_metical(row['price']),
                'stock': row['stock'],
                'image_url': row['image_url'] or '',
                'has_variations': False
            })
        conn.close()
        return jsonify(produtos)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mesas')
def get_mesas():
    try:
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        
        print(f"🔐 Tentativa de login: {username}")
        
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(password)
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ?', (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            print(f"✅ Login bem-sucedido: {user['name']} (ID: {user['id']})")
            return jsonify({'success': True, 'redirect': '/funcionario/pedidos'})
        else:
            print(f"❌ Login falhou para: {username}")
            return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'})
            
    except Exception as e:
        print(f"❌ Erro no login: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/restaurant-status')
def get_restaurant_status():
    return jsonify({'status': 'aberto', 'message': 'Aberto para pedidos', 'is_open': True})

@app.route('/api/user-info')
def get_user_info():
    print(f"🔍 Verificando usuário - Session user_id: {session.get('user_id')}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'logged_in': False})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name, role FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            print(f"✅ Usuário encontrado: {user['name']} - Role: {user['role']}")
            return jsonify({
                'logged_in': True, 
                'name': user['name'],
                'role': user['role']
            })
        else:
            print("❌ Usuário não encontrado no banco")
            return jsonify({'logged_in': False})
            
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        return jsonify({'logged_in': False})

@app.route('/api/pedidos')
def get_pedidos():
    print(f"🔍 Verificando pedidos - Session user_id: {session.get('user_id')}")
    print(f"🔍 Session completa: {dict(session)}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'error': 'Usuário não logado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se existem pedidos na tabela
        cursor.execute('SELECT COUNT(*) as total FROM orders')
        total_orders = cursor.fetchone()['total']
        print(f"📊 Total de pedidos na tabela: {total_orders}")
        
        cursor.execute('''
            SELECT o.id, o.status, o.total_amount, o.created_at,
                   t.number as table_number, t.capacity,
                   'Mesa ' || t.number as table_name
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            ORDER BY o.created_at DESC
        ''')
        
        pedidos = []
        rows = cursor.fetchall()
        print(f"📊 Encontrados {len(rows)} pedidos")
        
        for row in rows:
            pedido = {
                'id': row['id'],
                'status': row['status'],
                'total': row['total_amount'],
                'total_formatted': format_metical(row['total_amount']),
                'created_at': row['created_at'],
                'table_name': row['table_name'],
                'table_number': row['table_number'],
                'capacity': row['capacity']
            }
            pedidos.append(pedido)
            print(f"📋 Pedido {row['id']}: Mesa {row['table_name']}, Status: {row['status']}")
        
        conn.close()
        print(f"✅ Retornando {len(pedidos)} pedidos")
        return jsonify(pedidos)
        
    except Exception as e:
        print(f"❌ Erro ao buscar pedidos: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pedido/<int:order_id>/itens')
def get_pedido_itens(order_id):
    print(f"🔍 Buscando itens do pedido {order_id}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'error': 'Usuário não logado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT oi.quantity, oi.unit_price, p.name, p.description
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        
        itens = []
        rows = cursor.fetchall()
        print(f"📊 Encontrados {len(rows)} itens para o pedido {order_id}")
        
        for row in rows:
            item = {
                'name': row['name'],
                'description': row['description'] or '',
                'quantity': row['quantity'],
                'unit_price': row['unit_price'],
                'unit_price_formatted': format_metical(row['unit_price']),
                'total': row['quantity'] * row['unit_price'],
                'total_formatted': format_metical(row['quantity'] * row['unit_price'])
            }
            itens.append(item)
            print(f"📋 Item: {row['name']} x{row['quantity']}")
        
        conn.close()
        print(f"✅ Retornando {len(itens)} itens")
        return jsonify(itens)
        
    except Exception as e:
        print(f"❌ Erro ao buscar itens do pedido: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/pedido/<int:order_id>/status', methods=['PUT'])
def update_pedido_status(order_id):
    print(f"🔄 Alterando status do pedido {order_id}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'success': False, 'message': 'Usuário não logado'}), 401
    
    try:
        data = request.get_json()
        new_status = data.get('status')
        
        if not new_status:
            return jsonify({'success': False, 'message': 'Status não fornecido'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se o pedido existe
        cursor.execute('SELECT id FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Pedido não encontrado'}), 404
        
        # Atualizar status
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (new_status, order_id))
        conn.commit()
        conn.close()
        
        print(f"✅ Status do pedido {order_id} alterado para: {new_status}")
        return jsonify({'success': True, 'message': f'Status alterado para {new_status}'})
        
    except Exception as e:
        print(f"❌ Erro ao alterar status do pedido: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"🚀 Iniciando servidor na porta {port}")
    app.run(host='0.0.0.0', port=port, debug=False) 