import flet as ft
import sqlite3
from datetime import datetime, timedelta
from database.models import get_stock_entries, get_product_by_id

# Utilitário para formatar valores em Metical

def format_metical(value):
    if value is None:
        value = 0
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"


def ReportView(page: ft.Page, on_back=None):
    # Cabeçalho
    header = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                tooltip="Voltar",
                on_click=lambda e: on_back(e) if on_back else None
            ),
            ft.Icon(
                name=ft.icons.REPORT,
                size=50,
                color=ft.colors.WHITE
            ),
            ft.Text(
                "Relatórios",
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

    # Filtros rápidos
    hoje = datetime.now().date()
    inicio_mes = hoje.replace(day=1)
    inicio_semana = hoje - timedelta(days=hoje.weekday())
    filtros_rapidos = [
        ("Hoje", hoje, hoje),
        ("Esta Semana", inicio_semana, hoje),
        ("Este Mês", inicio_mes, hoje),
        ("Personalizado", None, None)
    ]
    filtro_rapido_valor = {"value": "Hoje"}

    # Estado dos filtros
    data_inicio = ft.TextField(label="Data Início", width=120, value=hoje.strftime("%Y-%m-%d"))
    data_fim = ft.TextField(label="Data Fim", width=120, value=hoje.strftime("%Y-%m-%d"))
    metodo_pagamento = ft.Dropdown(
        label="Pagamento",
        width=120,
        options=[ft.dropdown.Option("", "Todos"),
                 ft.dropdown.Option("dinheiro", "Dinheiro"),
                 ft.dropdown.Option("mpesa", "M-Pesa"),
                 ft.dropdown.Option("emola", "e-Mola"),
                 ft.dropdown.Option("cartao", "Cartão"),
                 ft.dropdown.Option("ponto24", "Ponto24")],
        value=""
    )
    operador = ft.Dropdown(label="Operador", width=150, options=[ft.dropdown.Option("", "Todos")], value="")
    valor_min = ft.TextField(label="Valor Mínimo", width=100, value="")
    valor_max = ft.TextField(label="Valor Máximo", width=100, value="")
    vendas_list = ft.ListView(expand=1, spacing=8, padding=10)
    total_vendas_text = ft.Text("", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)
    num_vendas_text = ft.Text("", size=15, color=ft.colors.BLUE_900)
    ticket_medio_text = ft.Text("", size=15, color=ft.colors.BLUE_900)
    mensagem_vazia = ft.Text("", size=16, color=ft.colors.GREY)

    # Carregar operadores
    def carregar_operadores():
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, username, name, role FROM users ORDER BY name')
        ops = cursor.fetchall()
        conn.close()
        operador.options = [ft.dropdown.Option("", "Todos")]
        for op in ops:
            if op[3] == 'admin':
                operador.options.append(ft.dropdown.Option(str(op[0]), "admin"))
            else:
                operador.options.append(ft.dropdown.Option(str(op[0]), op[1]))

    carregar_operadores()

    def set_filtro_rapido(nome, dt_ini, dt_fim):
        filtro_rapido_valor["value"] = nome
        if dt_ini and dt_fim:
            data_inicio.value = dt_ini.strftime("%Y-%m-%d")
            data_fim.value = dt_fim.strftime("%Y-%m-%d")
        page.update()
        carregar_vendas()

    def on_filtro_rapido_change(e):
        nome = e.control.value
        for n, dt_ini, dt_fim in filtros_rapidos:
            if n == nome:
                set_filtro_rapido(n, dt_ini, dt_fim)
                break
        if nome == "Personalizado":
            # Não altera datas
            pass

    filtro_rapido_dropdown = ft.Dropdown(
        label="Período",
        width=140,
        value=filtro_rapido_valor["value"],
        options=[ft.dropdown.Option(n, n) for n, _, _ in filtros_rapidos],
        on_change=on_filtro_rapido_change
    )

    def carregar_vendas():
        vendas_list.controls.clear()
        mensagem_vazia.value = ""
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        query = '''
            SELECT s.id, s.created_at, s.total_amount, s.payment_method, u.name, u.username
            FROM sales s
            LEFT JOIN users u ON s.user_id = u.id
            WHERE date(s.created_at) BETWEEN ? AND ?
        '''
        params = [data_inicio.value, data_fim.value]
        if metodo_pagamento.value:
            query += " AND s.payment_method = ?"
            params.append(metodo_pagamento.value)
        if operador.value:
            query += " AND s.user_id = ?"
            params.append(operador.value)
        if valor_min.value:
            query += " AND s.total_amount >= ?"
            params.append(float(valor_min.value.replace(",", ".")))
        if valor_max.value:
            query += " AND s.total_amount <= ?"
            params.append(float(valor_max.value.replace(",", ".")))
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
                        ft.Icon(name=ft.icons.ARROW_UPWARD, color=ft.colors.RED_600, size=20),
                        ft.Text("Saída", size=12, color=ft.colors.RED_600, width=50),
                        ft.Text(f"#{vid}", size=14, weight=ft.FontWeight.BOLD, width=50),
                        ft.Text(f"{created_at[:16]}", size=13, color=ft.colors.BLUE_900, width=120),
                        ft.Text(format_metical(total_amount), size=14, color=ft.colors.GREEN_700, width=110),
                        ft.Text(payment_method.capitalize() if payment_method else "-", size=13, color=ft.colors.BLUE_700, width=90),
                        # SAÍDAS (vendas):
                        ft.Container(
                            content=ft.Text(user_name or '-', size=13, color=ft.colors.GREY_700, max_lines=1, overflow=ft.TextOverflow.CLIP),
                            width=160,
                            padding=ft.padding.only(left=8)
                        ),
                        # ENTRADAS (estoque):
                        # (Remover o campo operador daqui)
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
        filtro_rapido_valor["value"] = "Personalizado"
        filtro_rapido_dropdown.value = "Personalizado"
        page.update()
        carregar_vendas()

    # --- Relatório de Entradas (Compras/Estoque) ---
    data_inicio_entrada = ft.TextField(label="Data Início", width=120, value=hoje.strftime("%Y-%m-%d"))
    data_fim_entrada = ft.TextField(label="Data Fim", width=120, value=hoje.strftime("%Y-%m-%d"))
    entradas_list = ft.ListView(expand=1, spacing=8, padding=10)
    total_entradas_text = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900)
    mensagem_vazia_entrada = ft.Text("", size=16, color=ft.colors.GREY)

    def carregar_entradas():
        entradas_list.controls.clear()
        mensagem_vazia_entrada.value = ""
        entries = get_stock_entries(start_date=data_inicio_entrada.value, end_date=data_fim_entrada.value)
        print(f"[DEBUG] Entradas encontradas: {len(entries)}")
        for entry in entries:
            print(f"[DEBUG] Entrada: {entry}")
        total = 0
        for eid, product_id, quantity, unit_cost, total_cost, supplier, notes, created_at in entries:
            total += total_cost or 0
            prod = get_product_by_id(product_id)
            prod_name = prod[1] if prod and prod[1] else f"ID {product_id}"
            entradas_list.controls.append(
                ft.Container(
                    bgcolor=ft.colors.WHITE,
                    border_radius=16,
                    border=ft.border.all(1, ft.colors.GREY_200),
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06)),
                    margin=ft.margin.all(4),
                    padding=0,
                    content=ft.Column([
                        ft.Text(f"{created_at[:16]}", size=14, color=ft.colors.BLUE_900, text_align=ft.TextAlign.CENTER),
                        ft.Text(prod_name, size=14, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"Qtd: {quantity}", size=13, color=ft.colors.BLUE_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"Unit: {format_metical(unit_cost)}", size=13, color=ft.colors.GREEN_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"Total: {format_metical(total_cost)}", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_900, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"Fornecedor: {supplier if supplier else '-'}", size=13, color=ft.colors.GREY_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"Obs: {notes if notes else '-'}", size=12, color=ft.colors.GREY_600, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                )
            )
        total_entradas_text.value = f"Total em Entradas: {format_metical(total)}"
        if not entries:
            mensagem_vazia_entrada.value = "Nenhuma entrada encontrada para os filtros selecionados."
        page.update()

    def on_filtrar_entradas(e):
        carregar_entradas()

    # --- Resumo Geral ---
    data_inicio_resumo = ft.TextField(label="Data Início", width=120, value=hoje.strftime("%Y-%m-%d"))
    data_fim_resumo = ft.TextField(label="Data Fim", width=120, value=hoje.strftime("%Y-%m-%d"))
    total_vendas_resumo = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700)
    total_entradas_resumo = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_700)
    lucro_resumo = ft.Text("", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.PURPLE_700)
    ticket_medio_resumo = ft.Text("", size=16, color=ft.colors.BLUE_900)
    num_vendas_resumo = ft.Text("", size=16, color=ft.colors.BLUE_900)
    num_entradas_resumo = ft.Text("", size=16, color=ft.colors.BLUE_900)

    def carregar_resumo():
        # Vendas
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_amount),0) FROM sales
            WHERE date(created_at) BETWEEN ? AND ?
        ''', (data_inicio_resumo.value, data_fim_resumo.value))
        num_vendas, total_vendas = cursor.fetchone()
        ticket_medio = total_vendas / num_vendas if num_vendas else 0
        # Entradas
        cursor.execute('''
            SELECT COUNT(*), COALESCE(SUM(total_cost),0) FROM stock_entries
            WHERE date(created_at) BETWEEN ? AND ?
        ''', (data_inicio_resumo.value, data_fim_resumo.value))
        num_entradas, total_entradas = cursor.fetchone()
        # Lucro bruto
        lucro = total_vendas - total_entradas
        conn.close()
        total_vendas_resumo.value = f"Total de Vendas: {format_metical(total_vendas)}"
        total_entradas_resumo.value = f"Total de Entradas: {format_metical(total_entradas)}"
        lucro_resumo.value = f"Lucro Bruto: {format_metical(lucro)}"
        ticket_medio_resumo.value = f"Ticket Médio: {format_metical(ticket_medio)}"
        num_vendas_resumo.value = f"Nº de Vendas: {num_vendas}"
        num_entradas_resumo.value = f"Nº de Entradas: {num_entradas}"
        page.update()

    def on_filtrar_resumo(e):
        carregar_resumo()

    aba_vendas = ft.Column([
        ft.Container(height=16),
        ft.Row([
            ft.Text("Filtros de Vendas", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Container(width=24),
            filtro_rapido_dropdown,
            data_inicio,
            data_fim,
            metodo_pagamento,
            operador,
            valor_min,
            valor_max,
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
                height=220,
                expand=False
            )
        ),
        ft.Container(mensagem_vazia, alignment=ft.alignment.center)
    ], expand=True)

    aba_entradas = ft.Column([
        ft.Container(height=16),
        ft.Row([
            ft.Text("Relatório de Entradas (Compras/Estoque)", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Container(width=24),
            data_inicio_entrada,
            data_fim_entrada,
            ft.ElevatedButton("Filtrar", icon=ft.icons.SEARCH, on_click=on_filtrar_entradas)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        ft.Container(height=12),
        ft.Container(
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_100),
            padding=ft.padding.symmetric(vertical=10, horizontal=18),
            content=ft.Row([
                total_entradas_text,
                ft.ElevatedButton("Atualizar", icon=ft.icons.REFRESH, on_click=lambda e: carregar_entradas())
            ], alignment=ft.MainAxisAlignment.START, spacing=40)
        ),
        ft.Container(height=12),
        ft.Container(
            bgcolor=ft.colors.WHITE,
            border_radius=12,
            border=ft.border.all(1, ft.colors.BLUE_100),
            padding=ft.padding.all(24),
            content=ft.Container(
                content=entradas_list,
                height=220,
                expand=False
            )
        ),
        ft.Container(mensagem_vazia_entrada, alignment=ft.alignment.center)
    ], expand=True)

    aba_resumo = ft.Column([
        ft.Container(height=16),
        ft.Row([
            ft.Text("Resumo Geral", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Container(width=24),
            data_inicio_resumo,
            data_fim_resumo,
            ft.ElevatedButton("Filtrar", icon=ft.icons.SEARCH, on_click=on_filtrar_resumo)
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER, spacing=12),
        ft.Container(height=12),
        ft.Container(
            bgcolor=ft.colors.BLUE_50,
            border_radius=8,
            border=ft.border.all(1, ft.colors.BLUE_100),
            padding=ft.padding.symmetric(vertical=18, horizontal=18),
            height=220,
            content=ft.Row([
                total_vendas_resumo,
                total_entradas_resumo,
                lucro_resumo,
                ticket_medio_resumo,
                num_vendas_resumo,
                num_entradas_resumo,
            ], alignment=ft.MainAxisAlignment.START, spacing=32)
        )
    ], expand=True)

    # Forçar carregar_vendas ou carregar_entradas ao trocar de aba
    def on_tab_change(e):
        if e.control.selected_index == 0:
            carregar_vendas()
        elif e.control.selected_index == 1:
            carregar_entradas()
        elif e.control.selected_index == 2:
            carregar_resumo()

    abas = ft.Tabs(
        selected_index=0,
        animation_duration=200,
        on_change=on_tab_change,
        tabs=[
            ft.Tab(text="Vendas (Saídas)", content=aba_vendas),
            ft.Tab(text="Entradas", content=aba_entradas),
            ft.Tab(text="Resumo", content=aba_resumo),
        ]
    )

    # Carregar vendas, entradas e resumo ao abrir
    carregar_vendas()
    carregar_entradas()
    carregar_resumo()

    # Exemplo para vendas:
    metodo_pagamento.on_change = lambda e: carregar_vendas()
    operador.on_change = lambda e: carregar_vendas()
    filtro_rapido_dropdown.on_change = on_filtro_rapido_change  # já chama carregar_vendas indiretamente
    data_inicio.on_change = lambda e: carregar_vendas()
    data_fim.on_change = lambda e: carregar_vendas()
    valor_min.on_change = lambda e: carregar_vendas()
    valor_max.on_change = lambda e: carregar_vendas()

    # Exemplo para entradas:
    data_inicio_entrada.on_change = lambda e: carregar_entradas()
    data_fim_entrada.on_change = lambda e: carregar_entradas()

    return ft.Container(
        bgcolor=ft.colors.BLUE_50,
        expand=True,
        content=ft.Column([
            header,
            ft.Container(height=20),
            abas
        ], expand=True, scroll=ft.ScrollMode.AUTO)
    ) 