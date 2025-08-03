#!/usr/bin/env python3
"""
Script para testar a dedução de estoque e identificar duplicações
"""

import sqlite3
from datetime import datetime

def check_stock_before_after():
    """Verifica o estoque antes e depois de operações"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    
    print("=== VERIFICAÇÃO DE ESTOQUE ===")
    
    # Verificar estoque atual
    cursor.execute('SELECT id, name, stock FROM products ORDER BY name')
    products = cursor.fetchall()
    
    print("\n📦 ESTOQUE ATUAL:")
    for prod_id, name, stock in products:
        print(f"  {name}: {stock} unidades")
    
    # Verificar pedidos pendentes
    cursor.execute('''
        SELECT o.id, o.status, oi.product_id, p.name, oi.quantity
        FROM orders o
        JOIN order_items oi ON o.id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE o.status IN ('pendente', 'preparando', 'pronto')
        ORDER BY o.id
    ''')
    
    orders = cursor.fetchall()
    if orders:
        print("\n📋 PEDIDOS ATIVOS:")
        current_order = None
        for order_id, status, prod_id, prod_name, qty in orders:
            if order_id != current_order:
                print(f"  Pedido #{order_id} ({status}):")
                current_order = order_id
            print(f"    - {prod_name}: {qty} unidades")
    else:
        print("\n📋 Nenhum pedido ativo encontrado")
    
    # Verificar vendas recentes
    cursor.execute('''
        SELECT s.order_id, s.payment_method, s.total_amount, s.created_at
        FROM sales s
        ORDER BY s.created_at DESC
        LIMIT 5
    ''')
    
    sales = cursor.fetchall()
    if sales:
        print("\n💰 VENDAS RECENTES:")
        for order_id, payment_method, total, created_at in sales:
            print(f"  Pedido #{order_id}: {total:.2f}MT ({payment_method}) - {created_at}")
    
    conn.close()

if __name__ == "__main__":
    check_stock_before_after() 