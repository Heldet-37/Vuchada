from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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

def is_restaurant_open():
    """Verifica se o restaurante está aberto baseado no horário atual"""
    current_time = datetime.now().time()
    
    # Horário de funcionamento: 6:00 às 22:00 (6 AM às 10 PM)
    opening_time = time(6, 0)  # 6:00 AM
    closing_time = time(22, 0)  # 10:00 PM
    
    return opening_time <= current_time <= closing_time

def get_restaurant_status():
    """Retorna o status do restaurante (aberto/fechado)"""
    if is_restaurant_open():
        return {
            'status': 'aberto',
            'message': 'Aberto para pedidos',
            'is_open': True
        }
    else:
        return {
            'status': 'fechado',
            'message': 'Fechado - Horário: 6:00 às 22:00',
            'is_open': False
        }

@app.route('/')
def index():
    status = get_restaurant_status()
    return render_template('index.html', restaurant_status=status)

@app.route('/simple')
def simple():
    return render_template('simple_index.html')

@app.route('/cliente')
def cliente():
    # Verifica se o restaurante está aberto
    status = get_restaurant_status()
    return render_template('cliente.html', restaurant_status=status)

@app.route('/funcionario')
def funcionario():
    return render_template('funcionario.html')

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')

@app.route('/servicos')
def servicos():
    return render_template('servicos.html')

@app.route('/api/categorias')
def get_categorias():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, name FROM categories WHERE active = 1 ORDER BY name')
    except:
        # Se não existir coluna active, pega todas as categorias
        cursor.execute('SELECT id, name FROM categories ORDER BY name')
    categorias = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(categorias)

@app.route('/api/produtos')
def get_produtos():
    categoria_id = request.args.get('categoria_id')
    busca = request.args.get('busca', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if categoria_id and categoria_id != 'todos':
        try:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock, has_variations
                FROM products 
                WHERE category_id = ? AND active = 1 AND stock > 0
                ORDER BY name
            ''', (categoria_id,))
        except:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock, has_variations
                FROM products 
                WHERE category_id = ? AND stock > 0
                ORDER BY name
            ''', (categoria_id,))
    else:
        try:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock, has_variations
                FROM products 
                WHERE active = 1 AND stock > 0
                ORDER BY name
            ''')
        except:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock, has_variations
                FROM products 
                WHERE stock > 0
                ORDER BY name
            ''')
    
    produtos = cursor.fetchall()
    conn.close()
    
    # Filtrar por busca
    if busca:
        produtos = [p for p in produtos if busca.lower() in p['name'].lower()]
    
    produtos_json = []
    for produto in produtos:
        # Se o produto tem variações, buscar as variações
        variations = []
        if produto['has_variations']:
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute('''
                    SELECT id, variation_name, price, stock
                    FROM product_variations 
                    WHERE product_id = ? AND is_active = 1 AND stock > 0
                    ORDER BY variation_name
                ''', (produto['id'],))
                variations = cursor.fetchall()
            except:
                # Se a tabela não existir, não mostrar variações
                pass
            conn.close()
        
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
    
    return jsonify(produtos_json)

@app.route('/api/produto/<int:product_id>/variacoes')
def get_produto_variacoes(product_id):
    """Retorna as variações de um produto específico"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, variation_name, price, stock
            FROM product_variations 
            WHERE product_id = ? AND is_active = 1
            ORDER BY variation_name
        ''', (product_id,))
        variacoes = cursor.fetchall()
        
        variacoes_json = [{
            'id': v['id'],
            'name': v['variation_name'],
            'price': v['price'],
            'price_formatted': format_metical(v['price']),
            'stock': v['stock']
        } for v in variacoes]
        
        conn.close()
        return jsonify(variacoes_json)
    except:
        conn.close()
        return jsonify([])

@app.route('/api/fazer_pedido', methods=['POST'])
def fazer_pedido():
    data = request.json
    mesa_id = data.get('mesa_id')
    itens = data.get('itens', [])
    
    if not itens:
        return jsonify({'success': False, 'message': 'Nenhum item no pedido'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Verificar capacidade da mesa
        cursor.execute('''
            SELECT t.capacity, t.status, COUNT(o.id) as active_orders
            FROM tables t
            LEFT JOIN orders o ON t.id = o.table_id AND o.status IN ('pendente', 'preparando', 'pronto')
            WHERE t.id = ?
            GROUP BY t.id, t.capacity, t.status
        ''', (mesa_id,))
        
        mesa_info = cursor.fetchone()
        if not mesa_info:
            return jsonify({'success': False, 'message': 'Mesa não encontrada'})
        
        capacity, status, active_orders = mesa_info
        
        # Verificar se a mesa está lotada
        if active_orders >= capacity:
            return jsonify({
                'success': False, 
                'message': f'Mesa lotada! Capacidade: {capacity} pessoas. Pedidos ativos: {active_orders}'
            })
        
        # Criar pedido
        cursor.execute('''
            INSERT INTO orders (table_id, status, created_at)
            VALUES (?, 'pendente', ?)
        ''', (mesa_id, datetime.now()))
        
        order_id = cursor.lastrowid
        
        # Adicionar itens
        total = 0
        for item in itens:
            # Verificar se é uma variação ou produto normal
            if item.get('variation_id'):
                # É uma variação
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price, notes)
                    VALUES (?, ?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'], item['price'], f"Variação: {item.get('variation_name', '')}"))
                
                # Baixar estoque da variação
                cursor.execute('''
                    UPDATE product_variations 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (item['quantity'], item['variation_id']))
            else:
                # É um produto normal
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'], item['price']))
                
                # Baixar estoque do produto
                cursor.execute('''
                    UPDATE products 
                    SET stock = stock - ? 
                    WHERE id = ?
                ''', (item['quantity'], item['product_id']))
            
            total += item['price'] * item['quantity']
        
        # Atualizar total do pedido
        cursor.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (total, order_id))
        
        # Marcar mesa como ocupada se estiver livre
        cursor.execute('SELECT status FROM tables WHERE id = ?', (mesa_id,))
        mesa_status = cursor.fetchone()['status']
        if mesa_status == 'livre':
            cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('ocupada', mesa_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': f'Pedido #{order_id} criado com sucesso!',
            'order_id': order_id,
            'total': format_metical(total)
        })
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao criar pedido: {str(e)}'})

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'})
    
    hashed_password = hash_password(password)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, username, name, role, active 
        FROM users 
        WHERE username = ? AND password = ? AND active = 1
    ''', (username, hashed_password))
    
    user = cursor.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['user_name'] = user['name']
        session['user_role'] = user['role']
        return jsonify({'success': True, 'redirect': '/funcionario/pedidos'})
    else:
        return jsonify({'success': False, 'message': 'Usuário ou senha incorretos'})

@app.route('/funcionario/pedidos')
def funcionario_pedidos():
    if 'user_id' not in session:
        return redirect('/funcionario')
    
    return render_template('funcionario_pedidos.html')

@app.route('/api/pedidos')
def get_pedidos():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    status_filter = request.args.get('status', '')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if status_filter:
        cursor.execute('''
            SELECT o.id, o.status, o.created_at,
                   t.number as table_number
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            WHERE o.status = ?
            ORDER BY o.created_at DESC
        ''', (status_filter,))
    else:
        cursor.execute('''
            SELECT o.id, o.status, o.created_at,
                   t.number as table_number
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            ORDER BY o.created_at DESC
        ''')
    
    pedidos = cursor.fetchall()
    
    pedidos_json = []
    for pedido in pedidos:
        # Calcular total dos itens do pedido
        cursor.execute('''
            SELECT SUM(quantity * unit_price) as total
            FROM order_items 
            WHERE order_id = ?
        ''', (pedido['id'],))
        
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result['total'] else 0
        
        pedidos_json.append({
            'id': pedido['id'],
            'status': pedido['status'],
            'created_at': pedido['created_at'],
            'total': total,
            'total_formatted': format_metical(total),
            'observations': '',  # Campo não existe na tabela
            'table_name': f"Mesa {pedido['table_number']}" if pedido['table_number'] else 'Balcão'
        })
    
    conn.close()
    return jsonify(pedidos_json)

@app.route('/api/pedido/<int:pedido_id>/itens')
def get_pedido_itens(pedido_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT oi.quantity, oi.unit_price, p.name, p.description
        FROM order_items oi
        JOIN products p ON oi.product_id = p.id
        WHERE oi.order_id = ?
    ''', (pedido_id,))
    
    itens = cursor.fetchall()
    conn.close()
    
    itens_json = []
    for item in itens:
        itens_json.append({
            'name': item['name'],
            'description': item['description'],
            'quantity': item['quantity'],
            'unit_price': item['unit_price'],
            'unit_price_formatted': format_metical(item['unit_price']),
            'total': item['quantity'] * item['unit_price'],
            'total_formatted': format_metical(item['quantity'] * item['unit_price'])
        })
    
    return jsonify(itens_json)

@app.route('/api/pedido/<int:pedido_id>/status', methods=['PUT'])
def atualizar_status_pedido(pedido_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    data = request.json
    novo_status = data.get('status')
    
    if not novo_status:
        return jsonify({'success': False, 'message': 'Status é obrigatório'})
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Se cancelando, restaurar estoque
        if novo_status == 'cancelado':
            cursor.execute('''
                SELECT oi.product_id, oi.quantity
                FROM order_items oi
                WHERE oi.order_id = ?
            ''', (pedido_id,))
            
            itens = cursor.fetchall()
            for item in itens:
                cursor.execute('''
                    UPDATE products 
                    SET stock = stock + ? 
                    WHERE id = ?
                ''', (item['quantity'], item['product_id']))
        
        # Atualizar status do pedido
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (novo_status, pedido_id))
        
        # Se cancelando ou finalizando, liberar mesa se não houver outros pedidos ativos
        if novo_status in ['cancelado', 'finalizado']:
            cursor.execute('''
                SELECT table_id FROM orders WHERE id = ?
            ''', (pedido_id,))
            table_id = cursor.fetchone()['table_id']
            
            if table_id:
                cursor.execute('''
                    SELECT COUNT(*) as count
                    FROM orders 
                    WHERE table_id = ? AND status IN ('pendente', 'preparando')
                ''', (table_id,))
                
                active_orders = cursor.fetchone()['count']
                if active_orders == 0:
                    cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('livre', table_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': f'Status atualizado para {novo_status}'})
        
    except Exception as e:
        conn.rollback()
        conn.close()
        return jsonify({'success': False, 'message': f'Erro ao atualizar status: {str(e)}'})

@app.route('/api/user-info')
def get_user_info():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Não autorizado'})
    
    return jsonify({
        'success': True,
        'id': session['user_id'],
        'username': session['username'],
        'name': session['user_name'],
        'role': session['user_role']
    })

@app.route('/api/restaurant-status')
def get_restaurant_status_api():
    """API para verificar o status do restaurante"""
    return jsonify(get_restaurant_status())

@app.route('/api/mesas')
def get_mesas():
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('SELECT id, number, capacity, status FROM tables WHERE active = 1 ORDER BY number')
    except:
        cursor.execute('SELECT id, number, capacity, status FROM tables ORDER BY number')
    mesas = [{'id': row['id'], 'name': f'Mesa {row["number"]}', 'capacity': row['capacity'], 'status': row['status']} for row in cursor.fetchall()]
    conn.close()
    return jsonify(mesas)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route('/api/pedido/<int:order_id>/pagar', methods=['POST'])
def process_payment(order_id):
    try:
        data = request.get_json()
        payment_method = data.get('payment_method')
        amount_paid = data.get('amount_paid', 0)
        
        if not payment_method:
            return jsonify({'success': False, 'message': 'Método de pagamento não fornecido'})
        
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        # Buscar informações do pedido
        cursor.execute('SELECT total_amount, table_id FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Pedido não encontrado'})
        
        total_amount, table_id = order
        
        # Validar pagamento em dinheiro
        if payment_method == 'dinheiro' and amount_paid < total_amount:
            conn.close()
            return jsonify({'success': False, 'message': 'Valor pago insuficiente'})
        
        # Baixar estoque dos produtos do pedido
        cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (order_id,))
        for prod_id, qty in cursor.fetchall():
            cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, prod_id))
        
        # Registrar venda
        cursor.execute('''
            INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, session.get('user_id'), payment_method, total_amount, datetime.now().isoformat()))
        
        # Atualizar status do pedido para entregue
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ("entregue", order_id))
        
        # Liberar mesa se houver
        if table_id:
            cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (table_id,))
        
        conn.commit()
        conn.close()
        
        return jsonify({'success': True, 'message': 'Pagamento processado com sucesso'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/pedido/<int:order_id>/finalizar-venda', methods=['POST'])
def finalize_sale(order_id):
    try:
        print(f"[DEBUG] Finalizando venda para pedido {order_id}")
        data = request.get_json()
        payment_method = data.get('payment_method')
        amount_paid = data.get('amount_paid', 0)
        
        print(f"[DEBUG] Método: {payment_method}, Valor pago: {amount_paid}")
        
        if not payment_method:
            return jsonify({'success': False, 'message': 'Método de pagamento não fornecido'})
        
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        # Buscar informações do pedido
        cursor.execute('SELECT total_amount, table_id FROM orders WHERE id = ?', (order_id,))
        order = cursor.fetchone()
        
        if not order:
            conn.close()
            return jsonify({'success': False, 'message': 'Pedido não encontrado'})
        
        total_amount, table_id = order
        print(f"[DEBUG] Total: {total_amount}, Mesa: {table_id}")
        
        # Validar pagamento em dinheiro
        if payment_method == 'dinheiro' and amount_paid < total_amount:
            conn.close()
            return jsonify({'success': False, 'message': 'Valor pago insuficiente'})
        
        # Baixar estoque dos produtos do pedido (se ainda não foi baixado)
        cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (order_id,))
        for prod_id, qty in cursor.fetchall():
            cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, prod_id))
            print(f"[DEBUG] Baixando estoque: produto {prod_id}, quantidade {qty}")
        
        # Registrar venda
        cursor.execute('''
            INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (order_id, session.get('user_id'), payment_method, total_amount, datetime.now().isoformat()))
        print(f"[DEBUG] Venda registrada na tabela sales")
        
        # Atualizar status do pedido para entregue
        cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ("entregue", order_id))
        print(f"[DEBUG] Status atualizado para 'entregue'")
        
        # Liberar mesa se houver
        if table_id:
            cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (table_id,))
            print(f"[DEBUG] Mesa {table_id} liberada")
        
        conn.commit()
        conn.close()
        
        print(f"[DEBUG] Venda finalizada com sucesso")
        return jsonify({'success': True, 'message': 'Venda finalizada com sucesso'})
        
    except Exception as e:
        print(f"[ERROR] Erro ao finalizar venda: {e}")
        return jsonify({'success': False, 'message': str(e)})

if __name__ == '__main__':
    # Criar pasta templates se não existir
    if not os.path.exists('templates'):
        os.makedirs('templates')
    
    # Criar pasta static se não existir
    if not os.path.exists('static'):
        os.makedirs('static')
    
    print("🌐 Servidor do Cardápio Digital iniciado!")
    print("📱 Acesse: http://localhost:5000")
    print("📱 Para acessar de outros dispositivos na rede: http://[SEU_IP]:5000")
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True) 