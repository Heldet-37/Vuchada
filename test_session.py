import sqlite3

def test_session_issue():
    try:
        conn = sqlite3.connect('database/restaurant.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Simular a consulta da API
        cursor.execute('''
            SELECT o.id, o.status, o.total_amount, o.created_at,
                   t.number as table_number, t.capacity,
                   'Mesa ' || t.number as table_name
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            ORDER BY o.created_at DESC
        ''')
        
        rows = cursor.fetchall()
        print(f"📊 Encontrados {len(rows)} pedidos")
        
        for row in rows:
            print(f"Pedido ID: {row['id']}")
            print(f"  Status: {row['status']}")
            print(f"  Total: {row['total_amount']}")
            print(f"  Mesa: {row['table_name']}")
            print(f"  Data: {row['created_at']}")
            print("---")
        
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_session_issue() 