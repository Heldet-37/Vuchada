import sqlite3

def test_database():
    try:
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        # Verificar tabelas
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print("Tabelas encontradas:", [table[0] for table in tables])
        
        # Verificar se a tabela orders existe
        if ('orders',) in tables:
            cursor.execute("SELECT COUNT(*) FROM orders")
            orders_count = cursor.fetchone()[0]
            print(f"Total de pedidos: {orders_count}")
            
            # Verificar estrutura da tabela orders
            cursor.execute("PRAGMA table_info(orders)")
            columns = cursor.fetchall()
            print("Colunas da tabela orders:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
            
            # Verificar alguns pedidos
            if orders_count > 0:
                cursor.execute("SELECT id, status, created_at FROM orders LIMIT 5")
                orders = cursor.fetchall()
                print("Primeiros 5 pedidos:")
                for order in orders:
                    print(f"  - ID: {order[0]}, Status: {order[1]}, Data: {order[2]}")
        else:
            print("Tabela 'orders' não encontrada!")
            
        conn.close()
        
    except Exception as e:
        print(f"Erro: {e}")

if __name__ == "__main__":
    test_database() 