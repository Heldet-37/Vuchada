import flet as ft
import sqlite3
from datetime import datetime

def get_today_sales(user_id=None):
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    today = datetime.now().date().isoformat()
    if user_id:
        cursor.execute('''SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE date(created_at) = ? AND user_id = ?''', (today, user_id))
    else:
        cursor.execute('''SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE date(created_at) = ?''', (today,))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_month_sales(user_id=None):
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    first_day = datetime.now().replace(day=1).date().isoformat()
    if user_id:
        cursor.execute('''SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE date(created_at) >= ? AND user_id = ?''', (first_day, user_id))
    else:
        cursor.execute('''SELECT COALESCE(SUM(total_amount), 0) FROM sales WHERE date(created_at) >= ?''', (first_day,))
    total = cursor.fetchone()[0] or 0
    conn.close()
    return total

def get_ticket_medio(user_id=None):
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    first_day = datetime.now().replace(day=1).date().isoformat()
    if user_id:
        cursor.execute('''SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM sales WHERE date(created_at) >= ? AND user_id = ?''', (first_day, user_id))
    else:
        cursor.execute('''SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM sales WHERE date(created_at) >= ?''', (first_day,))
    num, total = cursor.fetchone()
    conn.close()
    return (total / num) if num else 0

def get_low_stock_count():
    conn = sqlite3.connect('database/restaurant.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT COUNT(*) FROM products WHERE stock <= min_stock AND is_active = 1''')
    count = cursor.fetchone()[0] or 0
    conn.close()
    return count

def format_metical(value):
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"

def EmployeeDashboardView(page: ft.Page, user, on_navigate, on_logout=None):
    print('[DEBUG] Entrou em EmployeeDashboardView')
    # Dados reais
    user_id = user[0] if user else None
    print(f"[DEBUG] user_id do funcionário: {user_id}")
    today_sales = get_today_sales(user_id)
    print(f"[DEBUG] Vendas Hoje: {today_sales}")
    month_sales = get_month_sales(user_id)
    print(f"[DEBUG] Vendas do Mês: {month_sales}")
    low_stock = get_low_stock_count()
    print(f"[DEBUG] Estoque Baixo: {low_stock}")

    # Header igual admin, agora com botão de logout e fechar programa
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
                    on_click=lambda e: on_logout() if on_logout else page.go("/")
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
    # Botões (apenas os permitidos)
    buttons = [
        ft.Container(
            content=ft.ElevatedButton(
        "PDV",
        icon=ft.icons.POINT_OF_SALE,
        style=ft.ButtonStyle(
            color=ft.colors.WHITE,
                    bgcolor=ft.colors.GREEN
                ),
                on_click=lambda _: on_navigate("/pdv") if on_navigate else page.go("/pdv")
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
    ]
    # Cards igual admin, mas só os permitidos
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
            col={"sm": 6, "md": 3},
            ink=True,
            on_hover=lambda e: e.control.bgcolor == ft.colors.GREEN_800 if e.data == "true" else None
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
            col={"sm": 6, "md": 3},
            ink=True,
            on_hover=lambda e: e.control.bgcolor == ft.colors.BLUE_800 if e.data == "true" else None
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
                        str(low_stock),
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
            col={"sm": 6, "md": 3},
            ink=True,
            on_hover=lambda e: e.control.bgcolor == ft.colors.RED_800 if e.data == "true" else None
        )
    ]
    print('[DEBUG] Vai retornar layout do EmployeeDashboardView')
    return ft.Column([
        header,
        ft.Container(height=60),
        ft.ResponsiveRow(controls=buttons),
        ft.Container(height=20),
        ft.ResponsiveRow(controls=cards, spacing=20),
    ], expand=True, scroll=ft.ScrollMode.AUTO) 