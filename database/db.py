import sqlite3
from pathlib import Path
import hashlib
from datetime import datetime

DB_PATH = Path(__file__).parent / "restaurant.db"


def get_connection():
    return sqlite3.connect(DB_PATH)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    # Tabela de usuários
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'funcionario')),
            active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de categorias
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            price REAL NOT NULL,
            category_id INTEGER,
            stock INTEGER DEFAULT 0,
            min_stock INTEGER DEFAULT 0,
            cost_price REAL DEFAULT 0.0,
            image_url TEXT,
            is_active INTEGER DEFAULT 1,
            has_variations INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(category_id) REFERENCES categories(id)
        )
    ''')
    
    # Tabela de variações de produtos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS product_variations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            variation_name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER DEFAULT 0,
            cost_price REAL DEFAULT 0.0,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    ''')
    
    # Tabela de mesas
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            number INTEGER UNIQUE NOT NULL,
            capacity INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'livre' CHECK(status IN ('livre', 'ocupada', 'reservada', 'limpeza')),
            current_order_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de pedidos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_id INTEGER,
            customer_name TEXT,
            status TEXT NOT NULL DEFAULT 'pendente' CHECK(status IN ('pendente', 'preparando', 'pronto', 'entregue', 'cancelado')),
            total_amount REAL DEFAULT 0.0,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(table_id) REFERENCES tables(id)
        )
    ''')
    
    # Tabela de itens do pedido
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            product_id INTEGER,
            quantity INTEGER NOT NULL,
            unit_price REAL NOT NULL,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # Tabela de vendas (para histórico)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            user_id INTEGER,
            payment_method TEXT NOT NULL,
            total_amount REAL NOT NULL,
            discount REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(order_id) REFERENCES orders(id),
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
    ''')
    
    # Tabela de entradas de estoque (compras)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS stock_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL,
            unit_cost REAL NOT NULL,
            total_cost REAL NOT NULL,
            supplier TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(product_id) REFERENCES products(id)
        )
    ''')
    
    # Tabela de despesas
    cursor.execute('''CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TEXT NOT NULL,
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    user_id INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
)''')
    
    # Configurações gerais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key TEXT UNIQUE NOT NULL,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Inserir dados iniciais
    insert_initial_data(cursor)
    
    conn.commit()
    conn.close()


def insert_initial_data(cursor):
    # Verificar se já existem categorias antes de inserir
    cursor.execute('SELECT COUNT(*) FROM categories')
    if cursor.fetchone()[0] == 0:
        # Inserir usuário admin padrão
        admin_password = hash_password("842384")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, name, role, active)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Alves37", admin_password, "Administrador", "admin", 1))
        
        # Inserir categorias padrão
        default_categories = [
            ("Entradas", "Pratos de entrada e aperitivos"),
            ("Pratos Principais", "Pratos principais do cardápio"),
            ("Sobremesas", "Sobremesas e doces"),
            ("Bebidas", "Bebidas e refrigerantes"),
            ("Café", "Cafés e expressos")
        ]
        
        for name, description in default_categories:
            cursor.execute('''
                INSERT INTO categories (name, description, is_active)
                VALUES (?, ?, ?)
            ''', (name, description, 1))
    else:
        # Se já existem categorias, apenas garantir que o admin exista
        admin_password = hash_password("842384")
        cursor.execute('''
            INSERT OR IGNORE INTO users (username, password, name, role, active)
            VALUES (?, ?, ?, ?, ?)
        ''', ("Alves37", admin_password, "Administrador", "admin", 1)) 