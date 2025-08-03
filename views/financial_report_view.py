import flet as ft
import sqlite3
import datetime
import os

DB_PATH = os.path.join("database", "restaurant.db")

def get_financial_data(start_date, end_date, user_id=None):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    params = [start_date, end_date]
    user_filter = ""
    if user_id:
        user_filter = "AND sales.user_id = ?"
        params.append(user_id)
    cursor.execute(f'''
        SELECT sales.id, sales.created_at, users.username, SUM(order_items.quantity * order_items.unit_price) as total
        FROM sales
        JOIN order_items ON sales.id = order_items.order_id
        JOIN users ON sales.user_id = users.id
        WHERE sales.created_at BETWEEN ? AND ? {user_filter}
        GROUP BY sales.id
        ORDER BY sales.created_at DESC
    ''', params)
    sales = cursor.fetchall()
    total_sales = sum(row[3] for row in sales)
    conn.close()
    return sales, total_sales

def FinancialReportView(page: ft.Page, user, on_back=None):
    today = datetime.date.today()
    start_field = ft.TextField(label="Data Inicial", value=str(today.replace(day=1)), width=150)
    end_field = ft.TextField(label="Data Final", value=str(today), width=150)
    total_text = ft.Text("Total de Vendas: 0 MZN", size=18, weight=ft.FontWeight.BOLD)
    sales_list = ft.Column([], spacing=10)

    def update_report(e=None):
        start = start_field.value
        end = end_field.value
        sales, total = get_financial_data(start, end)
        sales_list.controls.clear()
        for row in sales:
            sales_list.controls.append(
                ft.Container(
                    bgcolor=ft.colors.WHITE,
                    border_radius=16,
                    border=ft.border.all(1, ft.colors.GREY_200),
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06)),
                    margin=ft.margin.all(4),
                    padding=0,
                    content=ft.Column([
                        ft.Text(f"{row[1][:16]}", size=14, color=ft.colors.BLUE_900, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{row[2]}", size=14, color=ft.colors.BLUE_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{row[3]:.2f} MZN", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                )
            )
        total_text.value = f"Total de Vendas: {total:.2f} MZN"
        page.update()

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                tooltip="Voltar",
                on_click=on_back
            ),
            ft.Icon(
                name=ft.icons.REPORT,
                size=50,
                color=ft.colors.WHITE
            ),
            ft.Text(
                "Relatório Financeiro",
                size=30,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE
            ),
            ft.Container(expand=True),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        padding=ft.padding.only(top=30, left=40, right=40, bottom=30),
        border_radius=10
    )

    filter_row = ft.Row([
        start_field,
        end_field,
        ft.ElevatedButton("Filtrar", on_click=update_report)
    ], spacing=16)

    content = ft.Column([
        header,
        ft.Container(height=20),
        filter_row,
        total_text,
        sales_list
    ], spacing=24, expand=True)

    # Atualiza ao abrir
    update_report()
    return content 