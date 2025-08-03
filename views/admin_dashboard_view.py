import flet as ft
from datetime import datetime, timedelta
import sqlite3
from views.financial_report_view import FinancialReportView

def format_metical(value):
    """Formata um valor para o formato de Metical"""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"

def get_today_sales():
    """Retorna o total de vendas do dia"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    today = datetime.now().date().isoformat()
    cursor.execute('''
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales
        WHERE date(created_at) = ?
    ''', (today,))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_month_sales():
    """Retorna o total de vendas do mês"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    first_day = datetime.now().replace(day=1).date().isoformat()
    cursor.execute('''
        SELECT COALESCE(SUM(total_amount), 0)
        FROM sales
        WHERE date(created_at) >= ?
    ''', (first_day,))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_total_profit():
    """Calcula o lucro total (vendas - custo dos produtos) incluindo vendas de balcão"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    first_day = datetime.now().replace(day=1).date().isoformat()
    cursor.execute('''
        SELECT oi.product_id, oi.quantity, oi.unit_price, p.cost_price
        FROM sales s
        JOIN order_items oi ON s.order_id = oi.order_id
        JOIN products p ON oi.product_id = p.id
        WHERE date(s.created_at) >= ?
    ''', (first_day,))
    total_profit = 0
    for product_id, quantity, sale_price, cost_price in cursor.fetchall():
        profit = (sale_price - (cost_price or 0)) * quantity
        total_profit += profit
    conn.close()
    return total_profit

def get_stock_value():
    """Calcula o valor total em estoque com base no custo"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT COALESCE(SUM(stock * cost_price), 0)
        FROM products
        WHERE is_active = 1
    ''')
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def AdminDashboardView(page: ft.Page, user, on_navigate, on_logout=None):
    print('[DEBUG] Entrou em AdminDashboardView')
    # Cabeçalho com gradiente e botão sair
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    name=ft.icons.DASHBOARD,
                    size=50,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Dashboard",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(width=20),
                ft.Text(
                    f"Bem-vindo(a), {user[3]}!",
                    size=16,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.LOGOUT,
                    icon_color=ft.colors.WHITE,
                    tooltip="Sair",
                    on_click=lambda _: on_logout() if on_logout else None
                ),
                ft.IconButton(
                    icon=ft.icons.POWER_SETTINGS_NEW,
                    icon_color=ft.colors.RED_400,
                    tooltip="Fechar Programa",
                    on_click=lambda e: page.window_close()
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        padding=ft.padding.symmetric(vertical=40, horizontal=60),
        border_radius=10
    )

    # Botões de ação
    buttons = [
        ft.Container(
            content=ft.ElevatedButton(
                "PDV",
                icon=ft.icons.POINT_OF_SALE,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.GREEN
                ),
                on_click=lambda _: on_navigate("/pdv") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Minhas Vendas",
                icon=ft.icons.SHOPPING_CART,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.BLUE
                ),
                on_click=lambda _: on_navigate("/minhas-vendas") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Configurações",
                icon=ft.icons.SETTINGS,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.ORANGE
                ),
                on_click=lambda _: on_navigate("/configuracoes") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Produtos",
                icon=ft.icons.INVENTORY,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.INDIGO
                ),
                on_click=lambda _: on_navigate("/produtos") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Categorias",
                icon=ft.icons.CATEGORY,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.DEEP_PURPLE
                ),
                on_click=lambda _: on_navigate("/categorias") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Funcionários",
                icon=ft.icons.PEOPLE,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.PURPLE
                ),
                on_click=lambda _: on_navigate("/usuarios") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Todas as Vendas",
                icon=ft.icons.RECEIPT_LONG,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.TEAL
                ),
                on_click=lambda _: on_navigate("/todas-vendas") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Relatórios",
                icon=ft.icons.REPORT,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.ORANGE_500
                ),
                on_click=lambda _: on_navigate("/relatorios") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Produtos Mais Vendidos",
                icon=ft.icons.TRENDING_UP,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.RED_600
                ),
                on_click=lambda _: on_navigate("/produtos-mais-vendidos") if on_navigate else None
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Relatório Financeiro",
                icon=ft.icons.REPORT,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.BLUE
                ),
                on_click=lambda _: on_navigate("/relatorio-financeiro") if on_navigate else None,
                disabled=True,
                opacity=0.5
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.ElevatedButton(
                "Despesas",
                icon=ft.icons.MONEY_OFF,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.RED_700
                ),
                on_click=lambda _: on_navigate("/despesas") if on_navigate else None,
                disabled=True,
                opacity=0.5
            ),
            col={"sm": 6, "md": 3}
        ),
    ]

    print('[DEBUG] Vai retornar layout do AdminDashboardView')
    return ft.Column([
                header,
        ft.Container(height=60),
        ft.ResponsiveRow(controls=buttons),
                ft.Container(height=20),
                get_stats_cards(),
    ], expand=True, scroll=ft.ScrollMode.AUTO)

def get_stats_cards():
    # Obter valores reais do banco de dados
    today_sales = get_today_sales()
    month_sales = get_month_sales()
    total_profit = get_total_profit()
    stock_value = get_stock_value()
    
    # Cards com as estatísticas (agora com valores reais)
    cards = [
        ft.Container(
            content=ft.Column([
                ft.Text(
                    "Vendas Hoje",
                    size=16, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    format_metical(today_sales),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.GREEN_700, ft.colors.GREEN_900]
            ),
            padding=25,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.Column([
                ft.Text(
                    "Vendas do Mês",
                    size=16, 
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    format_metical(month_sales),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.BLUE_700, ft.colors.BLUE_900]
            ),
            padding=25,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Lucro do Mês", size=16, color=ft.colors.WHITE),
                ft.Text(
                    format_metical(total_profit),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.PURPLE_700, ft.colors.PURPLE_900]
            ),
            padding=25,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Valor em Estoque", size=16, color=ft.colors.WHITE),
                ft.Text(
                    format_metical(stock_value),
                    size=20,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.ORANGE_700, ft.colors.ORANGE_900]
            ),
            padding=25,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            col={"sm": 6, "md": 3}
        ),
        ft.Container(
            content=ft.Column([
                ft.Text("Estoque Baixo", size=16, color=ft.colors.WHITE),
                ft.Row([
                    ft.Icon(
                        name=ft.icons.WARNING_AMBER_ROUNDED,
                        color=ft.colors.WHITE,
                        size=24
                    ),
                    ft.Text(
                        "0",
                        size=20,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    )
                ], alignment=ft.MainAxisAlignment.CENTER)
            ], alignment=ft.MainAxisAlignment.CENTER),
            gradient=ft.LinearGradient(
                begin=ft.alignment.top_left,
                end=ft.alignment.bottom_right,
                colors=[ft.colors.RED_700, ft.colors.RED_900]
            ),
            padding=25,
            border_radius=10,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.with_opacity(0.3, ft.colors.BLACK)
            ),
            col={"sm": 6, "md": 3}
        )
    ]

    return ft.ResponsiveRow(
        controls=cards,
        spacing=20
    ) 