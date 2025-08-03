import flet as ft
from datetime import datetime, timedelta
import sqlite3

def format_metical(value):
    """Formata um valor para o formato de Metical"""
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"

def get_best_sellers(period="month"):
    """Retorna os produtos mais vendidos baseado no período"""
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    
    if period == "today":
        start_date = datetime.now().date().isoformat()
        end_date = start_date
    elif period == "week":
        start_date = (datetime.now() - timedelta(days=7)).date().isoformat()
        end_date = datetime.now().date().isoformat()
    elif period == "month":
        start_date = datetime.now().replace(day=1).date().isoformat()
        end_date = datetime.now().date().isoformat()
    else:  # all time
        start_date = "1900-01-01"
        end_date = datetime.now().date().isoformat()
    
    cursor.execute('''
        SELECT 
            p.id,
            p.name,
            p.price,
            p.cost_price,
            p.stock,
            c.name as category_name,
            COALESCE(SUM(oi.quantity), 0) as total_quantity,
            COALESCE(SUM(oi.quantity * oi.unit_price), 0) as total_revenue,
            COALESCE(SUM(oi.quantity * (oi.unit_price - COALESCE(p.cost_price, 0))), 0) as total_profit
        FROM products p
        LEFT JOIN categories c ON p.category_id = c.id
        LEFT JOIN order_items oi ON p.id = oi.product_id
        LEFT JOIN orders o ON oi.order_id = o.id
        WHERE p.is_active = 1
        AND (o.created_at IS NULL OR (date(o.created_at) BETWEEN ? AND ?))
        GROUP BY p.id, p.name, p.price, p.cost_price, p.stock, c.name
        ORDER BY total_quantity DESC, total_revenue DESC
        LIMIT 20
    ''', (start_date, end_date))
    
    products = cursor.fetchall()
    conn.close()
    
    return products

def BestSellersView(page: ft.Page, user, on_navigate, on_logout=None):
    print('[DEBUG] Entrou em BestSellersView')
    
    # Estado da página
    current_period = ft.Ref[ft.Dropdown]()
    products_data = ft.Ref[ft.DataTable]()
    
    def load_data():
        """Carrega os dados baseado no período selecionado"""
        period = current_period.current.value
        products = get_best_sellers(period)
        
        # Atualizar tabela de produtos
        if products_data.current:
            products_data.current.rows = []
            for i, product in enumerate(products):
                products_data.current.rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(f"{i+1}")),
                            ft.DataCell(ft.Text(product[1])),  # nome
                            ft.DataCell(ft.Text(product[5] or "Sem categoria")),  # categoria
                            ft.DataCell(ft.Text(f"{product[6]:,}")),  # quantidade
                            ft.DataCell(ft.Text(format_metical(product[7]))),  # receita
                            ft.DataCell(ft.Text(format_metical(product[8]))),  # lucro
                            ft.DataCell(ft.Text(f"{product[4]}")),  # estoque
                        ]
                    )
                )
        
        page.update()
    
    def on_period_change(e):
        """Callback quando o período é alterado"""
        load_data()
    
    # Cabeçalho seguindo o padrão das outras páginas
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    name=ft.icons.TRENDING_UP,
                    size=50,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Produtos Mais Vendidos",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    icon_color=ft.colors.WHITE,
                    tooltip="Voltar",
                    on_click=lambda _: on_navigate("/admin") if on_navigate else None
                ),
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        padding=ft.padding.only(top=30, left=40, right=40, bottom=30),
        border_radius=10
    )
    
    # Seletor de período
    period_selector = ft.Container(
        content=ft.Row([
            ft.Text("Período:", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Dropdown(
                ref=current_period,
                width=200,
                value="month",
                options=[
                    ft.dropdown.Option("today", "Hoje"),
                    ft.dropdown.Option("week", "Última Semana"),
                    ft.dropdown.Option("month", "Este Mês"),
                    ft.dropdown.Option("all", "Todo Período"),
                ],
                on_change=on_period_change
            ),
        ], alignment=ft.MainAxisAlignment.START),
        padding=20,
        bgcolor=ft.colors.BLUE_50,
        border_radius=10,
        border=ft.border.all(1, ft.colors.BLUE_100),
        margin=ft.margin.only(bottom=20)
    )
    
    # Tabela de produtos
    products_table = ft.Container(
        content=ft.Column([
            ft.Text(
                "Ranking dos Produtos Mais Vendidos",
                size=20,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_900
            ),
            ft.DataTable(
                ref=products_data,
                border=ft.border.all(2, ft.colors.BLUE_100),
                border_radius=10,
                vertical_lines=ft.border.BorderSide(1, ft.colors.BLUE_200),
                horizontal_lines=ft.border.BorderSide(1, ft.colors.BLUE_200),
                column_spacing=20,
                columns=[
                    ft.DataColumn(ft.Text("Rank", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                    ft.DataColumn(ft.Text("Produto", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                    ft.DataColumn(ft.Text("Categoria", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                    ft.DataColumn(ft.Text("Qtd. Vendida", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                    ft.DataColumn(ft.Text("Receita", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                    ft.DataColumn(ft.Text("Lucro", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                    ft.DataColumn(ft.Text("Estoque", weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)),
                ],
                rows=[]
            )
        ]),
        padding=20,
        bgcolor=ft.colors.WHITE,
        border_radius=10,
        border=ft.border.all(1, ft.colors.BLUE_100),
        margin=ft.margin.only(top=20)
    )
    
    # Carregar dados iniciais
    load_data()
    
    print('[DEBUG] Vai retornar layout do BestSellersView')
    return ft.Column([
        header,
        period_selector,
        products_table,
    ], expand=True, scroll=ft.ScrollMode.AUTO) 