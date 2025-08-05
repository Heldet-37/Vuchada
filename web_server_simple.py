from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime, time
import os
from database.db import init_db

app = Flask(__name__, static_folder='static')
CORS(app, supports_credentials=True)  # Permitir CORS com credenciais
app.secret_key = 'pdv_restaurant_secret_key_2024'
app.config['SESSION_COOKIE_SECURE'] = False  # Para desenvolvimento
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Inicializar banco de dados
try:
    init_db()
    print("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    print(f"⚠️ Erro ao inicializar banco: {e}")

def get_db_connection():
    # Usar o mesmo banco que o sistema principal
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
            '/api/pedidos',
            '/test'
        ]
    })

@app.route('/test')
def test():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row['name'] for row in cursor.fetchall()]
        
        # Verificar pedidos
        cursor.execute('SELECT COUNT(*) as total FROM orders')
        total_orders = cursor.fetchone()['total']
        
        # Verificar usuários
        cursor.execute('SELECT COUNT(*) as total FROM users')
        total_users = cursor.fetchone()['total']
        
        # Verificar produtos
        cursor.execute('SELECT COUNT(*) as total FROM products')
        total_products = cursor.fetchone()['total']
        
        conn.close()
        
        return jsonify({
            'status': 'ok', 
            'message': 'Aplicação funcionando!',
            'database_info': {
                'tables': tables,
                'total_orders': total_orders,
                'total_users': total_users,
                'total_products': total_products
            },
            'session_info': {
                'user_id': session.get('user_id'),
                'session_data': dict(session)
            }
        })
        
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/categorias')
def get_categorias():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name')
        categorias = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        conn.close()
        return jsonify(categorias)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/produtos')
def get_produtos():
    categoria_id = request.args.get('categoria_id')
    busca = request.args.get('busca', '')
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        if categoria_id and categoria_id != 'todos':
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock, has_variations
                FROM products 
                WHERE category_id = ? AND is_active = 1 AND stock > 0
                ORDER BY name
            ''', (categoria_id,))
        else:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock, has_variations
                FROM products 
                WHERE is_active = 1 AND stock > 0
                ORDER BY name
            ''')
        
        produtos = cursor.fetchall()
        
        # Filtrar por busca
        if busca:
            produtos = [p for p in produtos if busca.lower() in p['name'].lower()]
        
        produtos_json = []
        for produto in produtos:
            # Se o produto tem variações, buscar as variações
            variations = []
            if produto['has_variations']:
                cursor.execute('''
                    SELECT id, variation_name, price, stock
                    FROM product_variations 
                    WHERE product_id = ? AND is_active = 1 AND stock > 0
                    ORDER BY variation_name
                ''', (produto['id'],))
                variations = cursor.fetchall()
            
            produtos_json.append({
                'id': produto['id'],
                'name': produto['name'],
                'description': produto['description'] or 'Sem descrição',
                'price': produto['price'],
                'price_formatted': format_metical(produto['price']),
                'image_url': produto['image_url'] or '/static/default_product.png',
                'stock': produto['stock'],
                'has_variations': produto['has_variations'],
                'variations': [{
                    'id': v['id'],
                    'name': v['variation_name'],
                    'price': v['price'],
                    'price_formatted': format_metical(v['price']),
                    'stock': v['stock']
                } for v in variations]
            })
        
        conn.close()
        return jsonify(produtos_json)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/mesas')
def get_mesas():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, number, capacity, status
            FROM tables 
            ORDER BY number
        ''')
        mesas = []
        for row in cursor.fetchall():
            mesas.append({
                'id': row['id'],
                'name': f"Mesa {row['number']}",
                'number': row['number'],
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
        
        if not mesa_id or not itens:
            return jsonify({'success': False, 'message': 'Dados inválidos'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar pedido
        cursor.execute('''
            INSERT INTO orders (table_id, status, total_amount, created_at)
            VALUES (?, 'pendente', 0, ?)
        ''', (mesa_id, datetime.now()))
        
        order_id = cursor.lastrowid
        total = 0
        
        # Adicionar itens
        for item in itens:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            variation_id = item.get('variation_id')
            
            if variation_id:
                # Buscar preço da variação
                cursor.execute('SELECT price FROM product_variations WHERE id = ?', (variation_id,))
                variation = cursor.fetchone()
                if variation:
                    unit_price = variation['price']
                    # Atualizar estoque da variação
                    cursor.execute('''
                        UPDATE product_variations 
                        SET stock = stock - ? 
                        WHERE id = ?
                    ''', (quantity, variation_id))
            else:
                # Buscar preço do produto
            cursor.execute('SELECT price FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            if product:
                unit_price = product['price']
                    # Atualizar estoque do produto
                    cursor.execute('''
                        UPDATE products 
                        SET stock = stock - ? 
                        WHERE id = ?
                    ''', (quantity, product_id))
            
            # Adicionar item ao pedido
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                VALUES (?, ?, ?, ?)
            ''', (order_id, product_id, quantity, unit_price))
            
            total += quantity * unit_price
        
        # Atualizar total do pedido
        cursor.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (total, order_id))
        
        # Atualizar status da mesa
        cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('ocupada', mesa_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'order_id': order_id,
            'total': format_metical(total)
        })
        
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
        cursor.execute('SELECT * FROM users WHERE username = ? AND password = ? AND active = 1', (username, hashed_password))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_name'] = user['name']
            session['user_role'] = user['role']
            print(f"✅ Login bem-sucedido: {user['name']} (ID: {user['id']})")
            print(f"📋 Session data: {dict(session)}")
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
    print(f"🔍 Session completa: {dict(session)}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'logged_in': False, 'debug': 'No user_id in session'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT id, username, name, role, active FROM users WHERE id = ?', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            print(f"✅ Usuário encontrado: {user['name']} - Role: {user['role']}")
            return jsonify({
                'logged_in': True, 
                'name': user['name'],
                'role': user['role'],
                'debug': f'User ID: {session["user_id"]}'
            })
        else:
            print("❌ Usuário não encontrado no banco")
            return jsonify({'logged_in': False, 'debug': f'User ID {session["user_id"]} not found in database'})
            
    except Exception as e:
        print(f"❌ Erro ao buscar usuário: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'logged_in': False, 'debug': f'Error: {str(e)}'})

@app.route('/api/pedidos')
def get_pedidos():
    print(f"🔍 Verificando pedidos - Session user_id: {session.get('user_id')}")
    print(f"🔍 Session completa: {dict(session)}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'error': 'Usuário não logado', 'debug': 'No user_id in session'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se existem pedidos na tabela
        cursor.execute('SELECT COUNT(*) as total FROM orders')
        total_orders = cursor.fetchone()['total']
        print(f"📊 Total de pedidos na tabela: {total_orders}")
        
        # Buscar pedidos com informações completas
        cursor.execute('''
            SELECT o.id, o.status, o.total_amount, o.created_at, o.notes,
                   t.number as table_number, t.capacity,
                   CASE 
                       WHEN t.number IS NOT NULL THEN 'Mesa ' || t.number
                       ELSE 'Balcão'
                   END as table_name
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
                'total': row['total_amount'] or 0,
                'total_formatted': format_metical(row['total_amount'] or 0),
                'created_at': row['created_at'],
                'table_name': row['table_name'],
                'table_number': row['table_number'],
                'capacity': row['capacity'],
                'observations': row['notes'] or ''
            }
            pedidos.append(pedido)
            print(f"📋 Pedido {row['id']}: {row['table_name']}, Status: {row['status']}, Total: {row['total_amount']}")
        
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
    print(f"🔄 Atualizando status do pedido {order_id}")
    
    if 'user_id' not in session:
        print("❌ Usuário não logado")
        return jsonify({'success': False, 'message': 'Usuário não logado'}), 401
    
    try:
        data = request.get_json()
        novo_status = data.get('status')
        
        if not novo_status:
            return jsonify({'success': False, 'message': 'Status é obrigatório'})
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar se o pedido existe
        cursor.execute('SELECT id, table_id FROM orders WHERE id = ?', (order_id,))
        pedido = cursor.fetchone()
        
        if not pedido:
            conn.close()
            return jsonify({'success': False, 'message': 'Pedido não encontrado'})
        
        # Atualizar status
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (novo_status, order_id))
        
        # Se o pedido foi finalizado, liberar a mesa
        if novo_status in ['entregue', 'cancelado']:
            if pedido['table_id']:
                cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('livre', pedido['table_id']))
        
        conn.commit()
        conn.close()
        
        print(f"✅ Status do pedido {order_id} atualizado para: {novo_status}")
        return jsonify({'success': True, 'message': f'Status atualizado para: {novo_status}'})
        
    except Exception as e:
        print(f"❌ Erro ao atualizar status: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/pedido/<int:order_id>/pagar', methods=['POST'])
def process_payment(order_id):
    print(f"💳 Processando pagamento do pedido {order_id}")
    
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não logado'}), 401
    
    try:
        data = request.get_json()
        payment_method = data.get('payment_method')
        amount_paid = data.get('amount_paid', 0)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar pedido
        cursor.execute('SELECT id, total_amount, table_id FROM orders WHERE id = ?', (order_id,))
        pedido = cursor.fetchone()
        
        if not pedido:
            conn.close()
            return jsonify({'success': False, 'message': 'Pedido não encontrado'})
        
        # Registrar venda
        cursor.execute('''
            INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, session['user_id'], payment_method, pedido['total_amount'], datetime.now()))
        
        # Atualizar status do pedido
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('entregue', order_id))
        
        # Liberar mesa
        if pedido['table_id']:
            cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('livre', pedido['table_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Pagamento processado com sucesso!',
            'change': amount_paid - pedido['total_amount'] if amount_paid > pedido['total_amount'] else 0
        })
        
    except Exception as e:
        print(f"❌ Erro ao processar pagamento: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/pedido/<int:order_id>/finalizar-venda', methods=['POST'])
def finalize_sale(order_id):
    print(f"💰 Finalizando venda do pedido {order_id}")
    
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Usuário não logado'}), 401
    
    try:
        data = request.get_json()
        payment_method = data.get('payment_method')
        amount_paid = data.get('amount_paid', 0)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Buscar pedido
        cursor.execute('SELECT id, total_amount, table_id FROM orders WHERE id = ?', (order_id,))
        pedido = cursor.fetchone()
        
        if not pedido:
            conn.close()
            return jsonify({'success': False, 'message': 'Pedido não encontrado'})
        
        # Registrar venda
        cursor.execute('''
            INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, session['user_id'], payment_method, pedido['total_amount'], datetime.now()))
        
        # Atualizar status do pedido
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ('entregue', order_id))
        
        # Liberar mesa
        if pedido['table_id']:
            cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('livre', pedido['table_id']))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Venda finalizada com sucesso!',
            'change': amount_paid - pedido['total_amount'] if amount_paid > pedido['total_amount'] else 0
        })
        
    except Exception as e:
        print(f"❌ Erro ao finalizar venda: {e}")
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 