from .db import get_connection
import hashlib

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

# Usuários

def create_user(username, password, name, role):
    conn = get_connection()
    cursor = conn.cursor()
    hashed_password = hash_password(password)
    cursor.execute(
        "INSERT INTO users (username, password, name, role) VALUES (?, ?, ?, ?)",
        (username, hashed_password, name, role)
    )
    conn.commit()
    conn.close()

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

# Produtos

def create_product(name, description, price, stock, min_stock=0, image_url=None, cost_price=0.0, is_active=1, category_id=None, has_variations=False):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO products (name, description, price, stock, min_stock, image_url, cost_price, is_active, category_id, has_variations) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (name, description, price, stock, min_stock, image_url, cost_price, is_active, category_id, has_variations)
    )
    product_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return product_id

def get_products(show_inactive=False):
    conn = get_connection()
    cursor = conn.cursor()
    if show_inactive:
        cursor.execute("SELECT * FROM products")
    else:
        cursor.execute("SELECT * FROM products WHERE is_active = 1")
    products = cursor.fetchall()
    conn.close()
    return products

def update_product(id, name, description, price, image_url=None, category_id=None, stock=0, min_stock=0, cost_price=0.0):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET name = ?, description = ?, price = ?, image_url = ?, category_id = ?, stock = ?, min_stock = ?, cost_price = ? WHERE id = ?",
        (name, description, price, image_url, category_id, stock, min_stock, cost_price, id)
    )
    conn.commit()
    conn.close()

def set_product_active(id, active):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE products SET is_active = ? WHERE id = ?",
        (1 if active else 0, id)
    )
    conn.commit()
    conn.close()

def delete_product(id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products WHERE id = ?", (id,))
    conn.commit()
    conn.close()

def delete_all_products():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products")
    conn.commit()
    conn.close()

def get_product_by_id(product_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = ?", (product_id,))
    product = cursor.fetchone()
    conn.close()
    return product

# Outras funções podem ser adicionadas conforme necessidade para sales, sales_items, tables, config. 

# Variações de Produtos

def create_product_variation(product_id, variation_name, price, stock=0, cost_price=0.0):
    """Cria uma variação para um produto"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO product_variations (product_id, variation_name, price, stock, cost_price) VALUES (?, ?, ?, ?, ?)",
        (product_id, variation_name, price, stock, cost_price)
    )
    # Marcar produto como tendo variações
    cursor.execute("UPDATE products SET has_variations = 1 WHERE id = ?", (product_id,))
    conn.commit()
    conn.close()

def get_product_variations(product_id):
    """Retorna todas as variações de um produto"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM product_variations WHERE product_id = ? AND is_active = 1 ORDER BY variation_name", (product_id,))
    variations = cursor.fetchall()
    conn.close()
    return variations

def update_product_variation(variation_id, variation_name, price, stock, cost_price):
    """Atualiza uma variação de produto"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE product_variations SET variation_name = ?, price = ?, stock = ?, cost_price = ? WHERE id = ?",
        (variation_name, price, stock, cost_price, variation_id)
    )
    conn.commit()
    conn.close()

def delete_product_variation(variation_id):
    """Remove uma variação de produto"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM product_variations WHERE id = ?", (variation_id,))
    conn.commit()
    conn.close()

def get_products_with_variations():
    """Retorna produtos que têm variações"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE has_variations = 1 AND is_active = 1")
    products = cursor.fetchall()
    conn.close()
    return products

def get_products_by_category_with_variations(category_id=None):
    """Retorna produtos com suas variações por categoria"""
    conn = get_connection()
    cursor = conn.cursor()
    
    if category_id:
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.category_id = ? AND p.is_active = 1 
            ORDER BY p.name
        """, (category_id,))
    else:
        cursor.execute("""
            SELECT p.*, c.name as category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id 
            WHERE p.is_active = 1 
            ORDER BY p.name
        """)
    
    products = cursor.fetchall()
    
    # Para cada produto, buscar suas variações
    for product in products:
        if product['has_variations']:
            cursor.execute("""
                SELECT * FROM product_variations 
                WHERE product_id = ? AND is_active = 1 
                ORDER BY variation_name
            """, (product['id'],))
            product['variations'] = cursor.fetchall()
        else:
            product['variations'] = []
    
    conn.close()
    return products

def add_stock_entry(product_id, quantity, unit_cost, supplier=None, notes=None, update_product_stock=True):
    conn = get_connection()
    cursor = conn.cursor()
    total_cost = quantity * unit_cost
    cursor.execute(
        "INSERT INTO stock_entries (product_id, quantity, unit_cost, total_cost, supplier, notes) VALUES (?, ?, ?, ?, ?, ?)",
        (product_id, quantity, unit_cost, total_cost, supplier, notes)
    )
    if update_product_stock:
        cursor.execute(
            "UPDATE products SET stock = stock + ? WHERE id = ?",
            (quantity, product_id)
        )
    conn.commit()
    conn.close()


def get_stock_entries(product_id=None, start_date=None, end_date=None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT id, product_id, quantity, unit_cost, total_cost, supplier, notes, created_at FROM stock_entries WHERE 1=1"
    params = []
    if product_id:
        query += " AND product_id = ?"
        params.append(product_id)
    if start_date:
        query += " AND date(created_at) >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date(created_at) <= ?"
        params.append(end_date)
    query += " ORDER BY created_at DESC"
    cursor.execute(query, params)
    entries = cursor.fetchall()
    conn.close()
    return entries 

def register_missing_stock_entries():
    conn = get_connection()
    cursor = conn.cursor()
    # Buscar todos os produtos
    cursor.execute("SELECT id, stock, cost_price FROM products")
    products = cursor.fetchall()
    for pid, stock, cost_price in products:
        # Verificar se já existe entrada para o produto
        cursor.execute("SELECT COUNT(*) FROM stock_entries WHERE product_id = ?", (pid,))
        count = cursor.fetchone()[0]
        if count == 0 and stock > 0:
            cursor.execute(
                "INSERT INTO stock_entries (product_id, quantity, unit_cost, total_cost, supplier, notes) VALUES (?, ?, ?, ?, ?, ?)",
                (pid, stock, cost_price or 0, (stock * (cost_price or 0)), None, "Entrada retroativa para produto já cadastrado")
            )
    conn.commit()
    conn.close() 

def fix_invalid_image_urls():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, image_url FROM products")
    for pid, image_url in cursor.fetchall():
        if not isinstance(image_url, str) or not image_url.startswith("static/"):
            cursor.execute("UPDATE products SET image_url = NULL WHERE id = ?", (pid,))
    conn.commit()
    conn.close() 

def fix_sales_missing_user_id(default_user_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    # Se não passar um user_id, tenta pegar o admin
    if default_user_id is None:
        cursor.execute("SELECT id FROM users WHERE role = 'admin' ORDER BY id LIMIT 1")
        row = cursor.fetchone()
        if row:
            default_user_id = row[0]
        else:
            raise Exception('Nenhum usuário admin encontrado para atribuir às vendas antigas.')
    # Atualiza todas as vendas sem user_id
    cursor.execute("UPDATE sales SET user_id = ? WHERE user_id IS NULL", (default_user_id,))
    conn.commit()
    conn.close() 