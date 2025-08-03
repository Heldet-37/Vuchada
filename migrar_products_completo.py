#!/usr/bin/env python3
"""
Script para migrar produtos e adicionar variações
"""

import sqlite3
import os
from datetime import datetime

def migrate_database():
    """Migra o banco de dados para suportar variações"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    
    print("🔄 Migrando banco de dados...")
    
    # Verificar se a coluna has_variations existe
    try:
        cursor.execute("SELECT has_variations FROM products LIMIT 1")
        print("✅ Coluna has_variations já existe")
    except:
        print("➕ Adicionando coluna has_variations...")
        cursor.execute("ALTER TABLE products ADD COLUMN has_variations INTEGER DEFAULT 0")
    
    # Verificar se a tabela product_variations existe
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='product_variations'")
        if cursor.fetchone():
            print("✅ Tabela product_variations já existe")
        else:
            print("➕ Criando tabela product_variations...")
            cursor.execute('''
                CREATE TABLE product_variations (
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
    except Exception as e:
        print(f"❌ Erro ao criar tabela: {e}")
    
    conn.commit()
    conn.close()
    print("✅ Migração concluída!")

def add_sample_products_with_variations():
    """Adiciona produtos de exemplo com variações"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    
    print("🍕 Adicionando produtos de exemplo com variações...")
    
    # Buscar categoria de pizzas ou criar uma
    cursor.execute("SELECT id FROM categories WHERE name LIKE '%pizza%' OR name LIKE '%Pizza%'")
    pizza_category = cursor.fetchone()
    
    if not pizza_category:
        print("➕ Criando categoria 'Pizzas'...")
        cursor.execute("INSERT INTO categories (name, description, is_active) VALUES (?, ?, ?)", 
                      ("Pizzas", "Pizzas artesanais", 1))
        pizza_category_id = cursor.lastrowid
    else:
        pizza_category_id = pizza_category[0]
    
    # Produto Pizza com variações
    pizza_product = {
        'name': 'Pizza Artesanal',
        'description': 'Pizza artesanal com massa fresca e ingredientes selecionados',
        'price': 150.00,  # Preço base
        'category_id': pizza_category_id,
        'stock': 0,  # Estoque será controlado pelas variações
        'image_url': '/static/default_product.png'
    }
    
    # Verificar se já existe
    cursor.execute("SELECT id FROM products WHERE name = ?", (pizza_product['name'],))
    existing_pizza = cursor.fetchone()
    
    if existing_pizza:
        print("✅ Produto Pizza já existe")
        pizza_id = existing_pizza[0]
    else:
        print("➕ Criando produto Pizza...")
        cursor.execute("""
            INSERT INTO products (name, description, price, category_id, stock, image_url, has_variations, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            pizza_product['name'], pizza_product['description'], pizza_product['price'],
            pizza_product['category_id'], pizza_product['stock'], pizza_product['image_url'], 1, 1
        ))
        pizza_id = cursor.lastrowid
    
    # Variações de pizza
    pizza_variations = [
        {'name': 'Margherita', 'price': 150.00, 'stock': 10},
        {'name': 'Pepperoni', 'price': 180.00, 'stock': 8},
        {'name': 'Quatro Queijos', 'price': 170.00, 'stock': 12},
        {'name': 'Calabresa', 'price': 160.00, 'stock': 15},
        {'name': 'Frango com Catupiry', 'price': 175.00, 'stock': 9},
        {'name': 'Portuguesa', 'price': 165.00, 'stock': 11},
    ]
    
    # Adicionar variações
    for variation in pizza_variations:
        cursor.execute("SELECT id FROM product_variations WHERE product_id = ? AND variation_name = ?", 
                      (pizza_id, variation['name']))
        if not cursor.fetchone():
            print(f"➕ Adicionando variação: {variation['name']}")
            cursor.execute("""
                INSERT INTO product_variations (product_id, variation_name, price, stock, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (pizza_id, variation['name'], variation['price'], variation['stock'], 1))
    
    # Produto Hambúrguer com variações
    burger_product = {
        'name': 'Hambúrguer Gourmet',
        'description': 'Hambúrguer artesanal com pão brioche e ingredientes premium',
        'price': 120.00,
        'category_id': pizza_category_id,  # Usar mesma categoria por simplicidade
        'stock': 0,
        'image_url': '/static/default_product.png'
    }
    
    cursor.execute("SELECT id FROM products WHERE name = ?", (burger_product['name'],))
    existing_burger = cursor.fetchone()
    
    if existing_burger:
        print("✅ Produto Hambúrguer já existe")
        burger_id = existing_burger[0]
    else:
        print("➕ Criando produto Hambúrguer...")
        cursor.execute("""
            INSERT INTO products (name, description, price, category_id, stock, image_url, has_variations, is_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            burger_product['name'], burger_product['description'], burger_product['price'],
            burger_product['category_id'], burger_product['stock'], burger_product['image_url'], 1, 1
        ))
        burger_id = cursor.lastrowid
    
    # Variações de hambúrguer
    burger_variations = [
        {'name': 'Clássico', 'price': 120.00, 'stock': 20},
        {'name': 'Bacon', 'price': 140.00, 'stock': 15},
        {'name': 'Queijo', 'price': 130.00, 'stock': 18},
        {'name': 'Duplo', 'price': 160.00, 'stock': 12},
        {'name': 'Vegetariano', 'price': 110.00, 'stock': 8},
    ]
    
    # Adicionar variações
    for variation in burger_variations:
        cursor.execute("SELECT id FROM product_variations WHERE product_id = ? AND variation_name = ?", 
                      (burger_id, variation['name']))
        if not cursor.fetchone():
            print(f"➕ Adicionando variação: {variation['name']}")
            cursor.execute("""
                INSERT INTO product_variations (product_id, variation_name, price, stock, is_active)
                VALUES (?, ?, ?, ?, ?)
            """, (burger_id, variation['name'], variation['price'], variation['stock'], 1))
    
    conn.commit()
    conn.close()
    print("✅ Produtos de exemplo adicionados!")

def show_sample_data():
    """Mostra os dados de exemplo criados"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    
    print("\n📊 Dados de exemplo criados:")
    print("=" * 50)
    
    # Produtos com variações
    cursor.execute("""
        SELECT p.id, p.name, p.description, p.price, p.has_variations,
               COUNT(pv.id) as variation_count
        FROM products p
        LEFT JOIN product_variations pv ON p.id = pv.product_id
        WHERE p.has_variations = 1
        GROUP BY p.id
    """)
    
    products = cursor.fetchall()
    
    for product in products:
        print(f"\n🍕 {product[1]}")
        print(f"   Descrição: {product[2]}")
        print(f"   Preço base: {product[3]:.2f} MT")
        print(f"   Variações: {product[5]}")
        
        # Mostrar variações
        cursor.execute("""
            SELECT variation_name, price, stock
            FROM product_variations
            WHERE product_id = ? AND is_active = 1
            ORDER BY variation_name
        """, (product[0],))
        
        variations = cursor.fetchall()
        for variation in variations:
            print(f"     • {variation[0]}: {variation[1]:.2f} MT (Estoque: {variation[2]})")
    
    conn.close()

def main():
    print("🚀 Iniciando migração do sistema de variações...")
    print("=" * 60)
    
    # Verificar se o banco existe
    if not os.path.exists('database/restaurant.db'):
        print("❌ Banco de dados não encontrado!")
        print("💡 Execute primeiro: python main.py")
        return
    
    try:
        # Migrar banco
        migrate_database()
        
        # Adicionar produtos de exemplo
        add_sample_products_with_variations()
        
        # Mostrar dados criados
        show_sample_data()
        
        print("\n" + "=" * 60)
        print("🎉 Migração concluída com sucesso!")
        print("\n📱 Para testar:")
        print("1. Execute: python web_server.py")
        print("2. Acesse: http://localhost:5000/cliente")
        print("3. Clique em 'Pizza Artesanal' ou 'Hambúrguer Gourmet'")
        print("4. Veja as variações disponíveis!")
        
    except Exception as e:
        print(f"❌ Erro durante a migração: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 