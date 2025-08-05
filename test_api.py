import sqlite3

def test_orders_api():
    try:
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        # Testar a consulta da API
        cursor.execute('''
            SELECT o.id, o.status, o.created_at,
                   t.number as table_number
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            ORDER BY o.created_at DESC
        ''')
        
        pedidos = cursor.fetchall()
        print(f"Pedidos encontrados: {len(pedidos)}")
        
        for pedido in pedidos:
            print(f"Pedido ID: {pedido[0]}, Status: {pedido[1]}, Mesa: {pedido[3]}")
            
            # Calcular total dos itens do pedido
            cursor.execute('''
                SELECT SUM(quantity * unit_price) as total
                FROM order_items 
                WHERE order_id = ?
            ''', (pedido[0],))
            
            total_result = cursor.fetchone()
            total = total_result[0] if total_result[0] else 0
            print(f"  Total: {total}")
            
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_orders_api() 