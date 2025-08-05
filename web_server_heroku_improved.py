from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import hashlib
from datetime import datetime, time
import os
import logging
from database.db import init_db

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, static_folder='static')
CORS(app, supports_credentials=True, origins=['*'])

# Configurações para produção
app.secret_key = os.environ.get('SECRET_KEY', 'pdv_restaurant_secret_key_2024')
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('FLASK_ENV') == 'production'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# Inicializar banco de dados
try:
    init_db()
    logger.info("✅ Banco de dados inicializado com sucesso!")
except Exception as e:
    logger.error(f"⚠️ Erro ao inicializar banco: {e}")

def get_db_connection():
    """Conexão com o banco de dados SQLite"""
    try:
        conn = sqlite3.connect('database/restaurant.db')
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        logger.error(f"Erro ao conectar com banco: {e}")
        raise

def format_metical(value):
    """Formata valor em Meticais"""
    return f"{value:,.2f} MT"

def hash_password(password):
    """Hash da senha usando SHA256"""
    return hashlib.sha256(password.encode()).hexdigest()

# Rotas de páginas estáticas
@app.route('/styles.css')
def styles():
    return send_from_directory('static', 'styles.css')

@app.route('/config.js')
def config_js():
    return send_from_directory('static', 'config.js')

@app.route('/cliente.js')
def cliente_js():
    return send_from_directory('static', 'cliente.js')

@app.route('/images/<path:filename>')
def images(filename):
    return send_from_directory('static/images', filename)

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

# Health check para o Heroku
@app.route('/test')
def test():
    """Rota de teste para verificar se a aplicação está funcionando"""
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
            'message': 'PDV Restaurante API funcionando!',
            'database_info': {
                'tables': tables,
                'total_orders': total_orders,
                'total_users': total_users,
                'total_products': total_products
            },
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Erro no health check: {e}")
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@app.route('/api')
def api_info():
    """Informações sobre a API"""
    return jsonify({
        'status': 'ok',
        'message': 'PDV Restaurante API funcionando!',
        'version': '1.0.0',
        'endpoints': [
            '/api/categorias',
            '/api/produtos',
            '/api/mesas',
            '/api/pedidos',
            '/api/login',
            '/api/restaurant-status',
            '/test'
        ]
    })

# API Routes
@app.route('/api/categorias')
def get_categorias():
    """Retorna todas as categorias"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories ORDER BY name')
        categorias = [{'id': row['id'], 'name': row['name']} for row in cursor.fetchall()]
        conn.close()
        return jsonify(categorias)
    except Exception as e:
        logger.error(f"Erro ao buscar categorias: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/produtos')
def get_produtos():
    """Retorna todos os produtos ativos"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.name, p.description, p.price, p.stock, p.image_url, 
                   c.name as category_name
            FROM products p
            LEFT JOIN categories c ON p.category_id = c.id
            WHERE p.is_active = 1 AND p.stock > 0
            ORDER BY p.name
        ''')
        produtos = []
        for row in cursor.fetchall():
            produtos.append({
                'id': row['id'],
                'name': row['name'],
                'description': row['description'] or '',
                'price': row['price'],
                'price_formatted': format_metical(row['price']),
                'stock': row['stock'],
                'image_url': row['image_url'],
                'category': row['category_name'] or 'Sem categoria',
                'has_variations': False
            })
        conn.close()
        return jsonify(produtos)
    except Exception as e:
        logger.error(f"Erro ao buscar produtos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/mesas')
def get_mesas():
    """Retorna todas as mesas"""
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
        logger.error(f"Erro ao buscar mesas: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/fazer_pedido', methods=['POST'])
def fazer_pedido():
    """Cria um novo pedido"""
    try:
        data = request.get_json()
        mesa_id = data.get('mesa_id')
        itens = data.get('itens', [])
        
        if not itens:
            return jsonify({'success': False, 'message': 'Nenhum item no pedido'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Criar pedido
        cursor.execute('''
            INSERT INTO orders (table_id, status, created_at) 
            VALUES (?, "pendente", ?)
        ''', (mesa_id, datetime.now()))
        order_id = cursor.lastrowid
        total = 0
        
        # Adicionar itens
        for item in itens:
            product_id = item.get('product_id')
            quantity = item.get('quantity', 1)
            
            cursor.execute('SELECT price, stock FROM products WHERE id = ?', (product_id,))
            product = cursor.fetchone()
            if product:
                unit_price = product['price']
                item_total = unit_price * quantity
                total += item_total
                
                # Verificar estoque
                if product['stock'] < quantity:
                    conn.rollback()
                    conn.close()
                    return jsonify({
                        'success': False, 
                        'message': f'Estoque insuficiente para o produto ID {product_id}'
                    }), 400
                
                # Inserir item do pedido
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price) 
                    VALUES (?, ?, ?, ?)
                ''', (order_id, product_id, quantity, unit_price))
                
                # Atualizar estoque
                cursor.execute('''
                    UPDATE products SET stock = stock - ? WHERE id = ?
                ''', (quantity, product_id))
        
        # Atualizar total do pedido
        cursor.execute('UPDATE orders SET total_amount = ? WHERE id = ?', (total, order_id))
        
        # Atualizar status da mesa
        if mesa_id:
            cursor.execute('UPDATE tables SET status = ? WHERE id = ?', ('ocupada', mesa_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"Pedido {order_id} criado com sucesso - Total: {total}")
        return jsonify({
            'success': True, 
            'order_id': order_id, 
            'total': format_metical(total),
            'message': 'Pedido criado com sucesso!'
        })
        
    except Exception as e:
        logger.error(f"Erro ao criar pedido: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/login', methods=['POST'])
def login():
    """Autenticação de usuário"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Usuário e senha são obrigatórios'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        hashed_password = hash_password(password)
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
            session['name'] = user['name']
            session['role'] = user['role']
            
            logger.info(f"Usuário {username} logado com sucesso")
            return jsonify({
                'success': True, 
                'redirect': '/funcionario/pedidos',
                'user': {
                    'name': user['name'],
                    'role': user['role']
                }
            })
        else:
            logger.warning(f"Tentativa de login falhou para usuário: {username}")
            return jsonify({'success': False, 'message': 'Usuário ou senha inválidos'}), 401
            
    except Exception as e:
        logger.error(f"Erro no login: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/restaurant-status')
def get_restaurant_status():
    """Status do restaurante (aberto/fechado)"""
    return jsonify({
        'status': 'aberto', 
        'message': 'Aberto para pedidos', 
        'is_open': True,
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/user-info')
def get_user_info():
    """Informações do usuário logado"""
    if 'user_id' not in session:
        return jsonify({'logged_in': False}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, username, name, role, active 
            FROM users 
            WHERE id = ? AND active = 1
        ''', (session['user_id'],))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return jsonify({
                'logged_in': True,
                'user': {
                    'id': user['id'],
                    'username': user['username'],
                    'name': user['name'],
                    'role': user['role']
                }
            })
        else:
            session.clear()
            return jsonify({'logged_in': False}), 401
            
    except Exception as e:
        logger.error(f"Erro ao buscar usuário: {e}")
        return jsonify({'logged_in': False, 'error': str(e)}), 500

@app.route('/api/pedidos')
def get_pedidos():
    """Retorna todos os pedidos"""
    if 'user_id' not in session:
        return jsonify({'error': 'Usuário não logado'}), 401
    
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
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
        for row in cursor.fetchall():
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
        
        conn.close()
        return jsonify(pedidos)
        
    except Exception as e:
        logger.error(f"Erro ao buscar pedidos: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/logout')
def logout():
    """Logout do usuário"""
    session.clear()
    return jsonify({'success': True, 'message': 'Logout realizado com sucesso'})

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Erro interno: {error}")
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    logger.info(f"🚀 Iniciando servidor na porta {port}")
    logger.info(f"🔧 Modo debug: {debug}")
    
    app.run(host='0.0.0.0', port=port, debug=debug) 