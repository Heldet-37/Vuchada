#!/usr/bin/env python3
"""
Script de teste para o Cardápio Digital
Verifica se todas as funcionalidades estão funcionando
"""

import requests
import json
import sqlite3
import sys
import os

def test_database_connection():
    """Testa conexão com o banco de dados"""
    try:
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        # Testa se as tabelas existem
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        required_tables = ['users', 'categories', 'products', 'tables', 'orders', 'order_items']
        missing_tables = [table for table in required_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Tabelas faltando: {missing_tables}")
            return False
        
        print("✅ Conexão com banco de dados OK")
        print(f"📊 Tabelas encontradas: {len(tables)}")
        
        # Testa se há dados
        try:
            cursor.execute("SELECT COUNT(*) FROM products WHERE active = 1")
            product_count = cursor.fetchone()[0]
            print(f"📦 Produtos ativos: {product_count}")
        except:
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"📦 Produtos: {product_count}")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM categories WHERE active = 1")
            category_count = cursor.fetchone()[0]
            print(f"📂 Categorias ativas: {category_count}")
        except:
            cursor.execute("SELECT COUNT(*) FROM categories")
            category_count = cursor.fetchone()[0]
            print(f"📂 Categorias: {category_count}")
        
        try:
            cursor.execute("SELECT COUNT(*) FROM tables WHERE active = 1")
            table_count = cursor.fetchone()[0]
            print(f"🪑 Mesas ativas: {table_count}")
        except:
            cursor.execute("SELECT COUNT(*) FROM tables")
            table_count = cursor.fetchone()[0]
            print(f"🪑 Mesas: {table_count}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erro na conexão com banco: {e}")
        return False

def test_web_server():
    """Testa se o servidor web está rodando"""
    try:
        # Tenta conectar ao servidor
        response = requests.get('http://localhost:5000', timeout=5)
        if response.status_code == 200:
            print("✅ Servidor web está rodando")
            return True
        else:
            print(f"❌ Servidor retornou status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Servidor web não está rodando")
        print("💡 Execute: python web_server.py")
        return False
    except Exception as e:
        print(f"❌ Erro ao testar servidor: {e}")
        return False

def test_api_endpoints():
    """Testa os endpoints da API"""
    base_url = 'http://localhost:5000'
    
    endpoints = [
        '/api/categorias',
        '/api/produtos',
        '/api/mesas'
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ {endpoint}: {len(data)} itens")
            else:
                print(f"❌ {endpoint}: Status {response.status_code}")
        except Exception as e:
            print(f"❌ {endpoint}: Erro - {e}")

def check_files():
    """Verifica se todos os arquivos necessários existem"""
    required_files = [
        'web_server.py',
        'templates/index.html',
        'templates/cliente.html',
        'templates/funcionario.html',
        'templates/funcionario_pedidos.html',
        'static/default_product.png',
        'requirements_web.txt',
        'README_CARDAPIO_DIGITAL.md'
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
        else:
            print(f"✅ {file_path}")
    
    if missing_files:
        print(f"❌ Arquivos faltando: {missing_files}")
        return False
    
    return True

def main():
    """Função principal de teste"""
    print("🧪 Testando Cardápio Digital...")
    print("=" * 50)
    
    # Testa arquivos
    print("\n📁 Verificando arquivos:")
    files_ok = check_files()
    
    # Testa banco de dados
    print("\n🗄️ Verificando banco de dados:")
    db_ok = test_database_connection()
    
    # Testa servidor web
    print("\n🌐 Verificando servidor web:")
    server_ok = test_web_server()
    
    # Testa API se servidor estiver rodando
    if server_ok:
        print("\n🔌 Testando endpoints da API:")
        test_api_endpoints()
    
    # Resumo
    print("\n" + "=" * 50)
    print("📊 RESUMO DOS TESTES:")
    
    if files_ok and db_ok and server_ok:
        print("🎉 TUDO FUNCIONANDO PERFEITAMENTE!")
        print("\n🚀 Para usar:")
        print("1. Acesse: http://localhost:5000")
        print("2. Para tablets/móveis: http://[SEU_IP]:5000")
        print("3. Use as mesmas credenciais do PDV para funcionários")
    else:
        print("⚠️ ALGUNS PROBLEMAS ENCONTRADOS:")
        if not files_ok:
            print("- Arquivos faltando")
        if not db_ok:
            print("- Problema no banco de dados")
        if not server_ok:
            print("- Servidor não está rodando")
        
        print("\n🔧 Para resolver:")
        print("1. Execute: python web_server.py")
        print("2. Verifique se o banco de dados existe")
        print("3. Confirme se todos os arquivos estão presentes")

if __name__ == "__main__":
    main() 