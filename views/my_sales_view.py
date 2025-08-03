import flet as ft
import sqlite3
from datetime import datetime, timedelta

def format_metical(value):
    if value is None:
        value = 0
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"

def MySalesView(page: ft.Page, user, on_back=None):
    user_id = user[0] if user else None
    is_admin = user and user[4] == 'admin'
    hoje = datetime.now().date()
    data_inicio = ft.TextField(label="Data Início", width=120, value=hoje.strftime("%Y-%m-%d"))
    data_fim = ft.TextField(label="Data Fim", width=120, value=hoje.strftime("%Y-%m-%d"))
    vendas_list = ft.ListView(expand=1, spacing=8, padding=10)
    total_vendas_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)
    num_vendas_text = ft.Text("", size=15, color=ft.colors.BLUE_900)
    ticket_medio_text = ft.Text("", size=15, color=ft.colors.BLUE_900)
    mensagem_vazia = ft.Text("", size=16, color=ft.colors.GREY)

    def carregar_vendas():
        vendas_list.controls.clear()
        mensagem_vazia.value = ""
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        query = '''
            SELECT s.id, s.created_at, s.total_amount, s.payment_method, u.name, u.username
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE date(s.created_at) BETWEEN ? AND ? AND s.user_id = ?
        '''
        params = [data_inicio.value, data_fim.value, user_id]
        query += " ORDER BY s.created_at DESC"
        cursor.execute(query, params)
        vendas = cursor.fetchall()
        total = 0
        num_vendas = len(vendas)
        for vid, created_at, total_amount, payment_method, user_name, user_username in vendas:
            total += total_amount or 0
            vendas_list.controls.append(
                ft.Container(
                    content=ft.Row([
                        ft.Text(f"#{vid}", size=14, weight=ft.FontWeight.BOLD, width=50),
                        ft.Text(f"{created_at[:16]}", size=13, color=ft.colors.BLUE_900, width=120),
                        ft.Text(format_metical(total_amount), size=14, color=ft.colors.GREEN_700, width=110),
                        ft.Text(payment_method.capitalize() if payment_method else "-", size=13, color=ft.colors.BLUE_700, width=90),
                        ft.Text(user_name or '-', size=13, color=ft.colors.GREY_700, width=160, max_lines=1, overflow=ft.TextOverflow.CLIP),
                    ], alignment=ft.MainAxisAlignment.START, spacing=8),
                    bgcolor=ft.colors.BLUE_50,
                    border_radius=8,
                    padding=8
                )
            )
        total_vendas_text.value = f"Total vendido: {format_metical(total)}"
        num_vendas_text.value = f"Nº de vendas: {num_vendas}"
        ticket_medio = total / num_vendas if num_vendas else 0
        ticket_medio_text.value = f"Ticket médio: {format_metical(ticket_medio)}"
        if not vendas:
            mensagem_vazia.value = "Nenhuma venda encontrada para os filtros selecionados."
        page.update()

    def on_filtrar_vendas(e):
        carregar_vendas()

    # Carregar vendas ao abrir
    carregar_vendas()

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                tooltip="Voltar",
                on_click=lambda e: on_back(e) if on_back else None
            ),
            ft.Icon(
                name=ft.icons.SHOPPING_CART,
                size=50,
                color=ft.colors.WHITE
            ),
            ft.Text(
                "Minhas Vendas",
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

    return ft.Column([
        header,
        ft.Container(height=16),
        ft.Row([
            data_inicio,
            data_fim,
            ft.ElevatedButton("Filtrar", icon=ft.icons.SEARCH, on_click=on_filtrar_vendas)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        ft.Container(height=12),
        ft.Container(
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_100),
            padding=ft.padding.symmetric(vertical=10, horizontal=18),
            content=ft.Row([
                total_vendas_text,
                num_vendas_text,
                ticket_medio_text,
                ft.ElevatedButton("Atualizar", icon=ft.icons.REFRESH, on_click=lambda e: carregar_vendas())
            ], alignment=ft.MainAxisAlignment.START, spacing=40)
        ),
        ft.Container(height=12),
        ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.colors.BLUE_100),
            padding=ft.padding.all(24),
            content=ft.Container(
                content=vendas_list,
                height=320,
                expand=False
            )
        ),
        ft.Container(mensagem_vazia, alignment=ft.alignment.center)
    ], expand=True, scroll=ft.ScrollMode.AUTO) 