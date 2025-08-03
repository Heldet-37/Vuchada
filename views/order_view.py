import flet as ft
import sqlite3
from datetime import datetime

# Função utilitária para formatar valores em Metical
def format_metical(value):
    if value is None:
        value = 0
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"


def OrderView(page: ft.Page, on_back=None, user=None):
    import datetime
    print(f"[LOG] [OrderView] Página de pedidos acessada por usuário: {user}")
    print(f"[LOG] [OrderView] Data/hora de acesso: {datetime.datetime.now().isoformat()}")
    
    # Sistema de auto-refresh simplificado
    # Por enquanto, vamos desabilitar o auto-refresh automático
    # e adicionar um botão de refresh manual
    def manual_refresh(e):
        """Refresh manual dos pedidos"""
        check_for_new_orders()
        page.show_snack_bar(ft.SnackBar(
            content=ft.Text("🔄 Lista de pedidos atualizada!"),
            bgcolor=ft.colors.BLUE_400,
            duration=2000
        ))
    
    # Adicionar botão de refresh manual no header
    refresh_button = ft.IconButton(
        icon=ft.icons.REFRESH,
        icon_color=ft.colors.WHITE,
        tooltip="Atualizar pedidos",
        on_click=manual_refresh
    )
    
    # Indicador de status
    status_indicator = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.SYNC, size=16, color=ft.colors.WHITE),
            ft.Text("Auto-refresh ativo", size=12, color=ft.colors.WHITE)
        ], spacing=4),
        visible=True
    )
    
    # Cabeçalho
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    icon_color=ft.colors.WHITE,
                    tooltip="Voltar",
                    on_click=lambda e: on_back(e) if on_back else page.go("/pdv")
                ),
                ft.Icon(
                    name=ft.icons.RESTAURANT_MENU,
                    size=50,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Pedidos",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),
                status_indicator,
                refresh_button
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        padding=ft.padding.only(top=30, left=40, right=40, bottom=30),
        border_radius=10
    )
    # Paginação funcional
    cards_por_pagina = 10
    colunas = 3
    pagina_atual = {"value": 0}

    # Buscar pedidos reais do banco
    def fetch_pedidos_reais():
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.id, t.number as mesa, o.customer_name, o.status, o.total_amount
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            ORDER BY o.created_at DESC
        ''')
        pedidos = []
        for row in cursor.fetchall():
            pid, mesa, cliente, status, valor = row
            # Buscar itens do pedido
            cursor.execute('''
                SELECT p.name, oi.quantity FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id = ?
            ''', (pid,))
            itens = cursor.fetchall()
            itens_str = ', '.join([f"{q}x {n}" for n, q in itens]) if itens else "-"
            pedidos.append({
                "id": pid,
                "mesa": mesa if mesa is not None else "-",
                "cliente": cliente or "-",
                "itens": itens_str,
                "valor": valor or 0.0,
                "status": status or "-"
            })
        conn.close()
        return pedidos

    # Substituir o mock por dados reais
    def get_pedidos():
        return fetch_pedidos_reais()

    # Campo de busca
    busca_valor = {"value": ""}

    # Filtro de status simplificado
    status_filtro_valor = {"value": "todos"}
    status_filtro_options = [
        ("todos", "Todos os Status"),
        ("pendente", "Pendente"),
        ("preparando", "Preparando"),
        ("pronto", "Pronto"),
        ("entregue", "Entregue"),
        ("cancelado", "Cancelado")
    ]

    paginacao_row = [None]  # placeholder mutável

    paginacao_row[0] = ft.Row([
        ft.ElevatedButton("Anterior", icon=ft.icons.ARROW_BACK, disabled=False, on_click=lambda e: anterior_pagina()),
        ft.Text("Página 1 de 1", size=13, color=ft.colors.BLUE_900),
        ft.ElevatedButton("Próxima", icon=ft.icons.ARROW_FORWARD, disabled=False, on_click=lambda e: proxima_pagina())
    ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)

    # Área dinâmica para grid + paginação
    pedidos_area = ft.Column([], expand=True)



    def excluir_pedidos_filtrados(e):
        # Obter pedidos filtrados atuais
        pedidos_lista = get_pedidos()
        
        # Aplicar os mesmos filtros da função atualizar_grid
        status_filtro = status_filtro_valor["value"]
        if status_filtro != "todos":
            pedidos_lista = [p for p in pedidos_lista if p["status"] == status_filtro]
        
        filtro = busca_valor["value"].strip().lower()
        if filtro:
            pedidos_filtrados = [p for p in pedidos_lista if filtro in str(p["id"]).lower() or filtro in str(p["mesa"]).lower() or filtro in (p["cliente"] or "").lower()]
        else:
            pedidos_filtrados = pedidos_lista
        
        if not pedidos_filtrados:
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Nenhum pedido encontrado para excluir!"),
                bgcolor=ft.colors.ORANGE
            ))
            return
        
        # Confirmar exclusão
        def confirmar_exclusao(ev):
            conn = None
            try:
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                
                # Excluir pedidos filtrados
                for pedido in pedidos_filtrados:
                    pedido_id = pedido["id"]
                    
                    # Primeiro, restaurar estoque dos produtos
                    cursor.execute('''
                        SELECT product_id, quantity FROM order_items 
                        WHERE order_id = ?
                    ''', (pedido_id,))
                    
                    for prod_id, qty in cursor.fetchall():
                        cursor.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (qty, prod_id))
                    
                    # Liberar mesa se houver
                    cursor.execute('SELECT table_id FROM orders WHERE id = ?', (pedido_id,))
                    row = cursor.fetchone()
                    if row and row[0]:
                        cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (row[0],))
                    
                    # Excluir itens do pedido
                    cursor.execute('DELETE FROM order_items WHERE order_id = ?', (pedido_id,))
                    
                    # Excluir o pedido
                    cursor.execute('DELETE FROM orders WHERE id = ?', (pedido_id,))
                
                conn.commit()
                
                dialog.open = False
                page.update()
                
                # Atualizar a lista
                atualizar_grid()
                
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"{len(pedidos_filtrados)} pedido(s) excluído(s) com sucesso!"),
                    bgcolor=ft.colors.GREEN
                ))
                
            except Exception as ex:
                if conn:
                    conn.rollback()
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"Erro ao excluir pedidos: {ex}"),
                    bgcolor=ft.colors.RED
                ))
            finally:
                if conn:
                    conn.close()
        
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja realmente excluir {len(pedidos_filtrados)} pedido(s)?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Excluir", on_click=confirmar_exclusao, style=ft.ButtonStyle(color=ft.colors.RED))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def on_status_filtro_change(e):
        status_filtro_valor["value"] = e.control.value
        pagina_atual["value"] = 0
        atualizar_grid()

    def atualizar_grid():
        pedidos_lista = get_pedidos()
        
        # Filtrar por status
        status_filtro = status_filtro_valor["value"]
        if status_filtro != "todos":
            pedidos_lista = [p for p in pedidos_lista if p["status"] == status_filtro]
        
        # Filtrar pedidos pelo campo de busca
        filtro = busca_valor["value"].strip().lower()
        if filtro:
            pedidos_filtrados = [p for p in pedidos_lista if filtro in str(p["id"]).lower() or filtro in str(p["mesa"]).lower() or filtro in (p["cliente"] or "").lower()]
        else:
            pedidos_filtrados = pedidos_lista
        
        total_paginas_local = (len(pedidos_filtrados) + cards_por_pagina - 1) // cards_por_pagina
        pagina_atual["value"] = min(pagina_atual["value"], max(0, total_paginas_local - 1))
        inicio = pagina_atual["value"] * cards_por_pagina
        fim = inicio + cards_por_pagina
        pedidos_pagina = pedidos_filtrados[inicio:fim]
        grid = render_pedidos_grid(pedidos_pagina)
        
        pedidos_area.controls = [
            ft.Container(
                content=ft.Column(
                    [grid],
                    scroll=ft.ScrollMode.AUTO,
                    expand=True
                ),
                expand=True,
                height=500
            )
        ]
        # Atualizar paginação
        paginacao_row[0].controls[1].value = f"Página {pagina_atual['value']+1} de {max(1, total_paginas_local)}"
        paginacao_row[0].controls[0].disabled = pagina_atual['value'] == 0
        paginacao_row[0].controls[2].disabled = pagina_atual['value'] >= total_paginas_local-1
        page.update()

    def render_pedidos_grid(pedidos_pagina=None):
        if pedidos_pagina is None:
            pedidos_pagina = get_pedidos()
        status_colors = {
            'pendente': ft.colors.ORANGE,
            'preparando': ft.colors.BLUE,
            'pronto': ft.colors.GREEN,
            'entregue': ft.colors.GREEN_700,
            'cancelado': ft.colors.RED_700
        }
        status_icons = {
            'pendente': ft.icons.HOURGLASS_EMPTY,
            'preparando': ft.icons.KITCHEN,
            'pronto': ft.icons.CHECK_CIRCLE,
            'entregue': ft.icons.CHECK,
            'cancelado': ft.icons.CANCEL
        }
        grid = ft.Row([
            ft.Container(
                content=ft.GridView(
                    runs_count=colunas,
                    max_extent=260,
                    child_aspect_ratio=1.1,
                    spacing=24,
                    run_spacing=24,
                    controls=[
                        ft.Container(
                            content=ft.Column([
                                ft.Icon(name=status_icons.get(p["status"], ft.icons.LIST_ALT), color=status_colors.get(p["status"], ft.colors.GREY), size=32),
                                ft.Text(f"Pedido #{p['id']}", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"Mesa: {p['mesa']}", size=12, color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"Cliente: {p['cliente']}", size=12, color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER),
                                ft.Text(f"Itens: {p['itens']}", size=11, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER),
                                ft.Text(format_metical(p['valor']), size=13, weight=ft.FontWeight.BOLD, color=ft.colors.AMBER_200, text_align=ft.TextAlign.CENTER),
                                ft.Container(
                                    content=ft.Text(p["status"].capitalize(), size=12, color=ft.colors.WHITE, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                                    bgcolor=status_colors.get(p["status"], ft.colors.GREY),
                                    border_radius=7,
                                    padding=ft.padding.symmetric(vertical=4, horizontal=8),
                                    alignment=ft.alignment.center,
                                    margin=ft.margin.only(top=6)
                                ),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=6),
                            bgcolor=ft.colors.BLUE_800,
                            border=ft.border.all(2, status_colors.get(p["status"], ft.colors.GREY)),
                            border_radius=10,
                            padding=10,
                            width=220,
                            alignment=ft.alignment.center,
                            ink=True,
                            on_click=lambda e, pedido=p: show_order_modal(pedido)
                        ) for p in pedidos_pagina
                    ]
                ),
                alignment=ft.alignment.center,
                expand=True
            )
        ], alignment=ft.MainAxisAlignment.CENTER)
        return grid

    def show_order_modal(pedido):
        # Modal de gerenciamento do pedido
        status_options = [
            ("pendente", "Pendente"),
            ("preparando", "Preparando"),
            ("pronto", "Pronto"),
            ("entregue", "Entregue"),
            ("cancelado", "Cancelado")
        ]
        status_state = {"value": pedido["status"]}
        pagamento_state = {"value": "dinheiro"}
        valor_pago_state = {"value": ""}
        troco_state = {"value": 0.0}
        erro_valor_pago = ft.Text("", color=ft.colors.RED, size=13)
        dialog_ref = {"dialog": None}
        is_finalizado = pedido["status"] in ["entregue", "cancelado"]
        def on_status_change(e):
            status_state["value"] = e.control.value
            update_actions()
        status_dropdown = ft.Dropdown(
            label="Status",
            value=pedido["status"],
            options=[ft.dropdown.Option(opt[0], opt[1]) for opt in status_options],
            width=200,
            on_change=on_status_change
        )
        def on_pagamento_change(e):
            pagamento_state["value"] = e.control.value
            if valor_pago_field:
                valor_pago_field.visible = (pagamento_state["value"] == "dinheiro")
            if troco_text:
                troco_text.visible = (pagamento_state["value"] == "dinheiro")
            erro_valor_pago.value = ""
            page.update()
        def on_valor_pago_change(e):
            try:
                valor_pago = float(e.control.value.replace(",", "."))
            except Exception:
                valor_pago = 0.0
            valor_pago_state["value"] = valor_pago
            total = pedido["valor"]
            troco = valor_pago - total
            troco_state["value"] = troco
            if valor_pago < total:
                erro_valor_pago.value = "Valor insuficiente!"
            else:
                erro_valor_pago.value = ""
            troco_text.value = f"Troco: {troco:.2f} MT" if pagamento_state["value"] == "dinheiro" and valor_pago else ""
            page.update()
        pagamento_dropdown = ft.Dropdown(
            label="Método de Pagamento",
            value=pagamento_state["value"],
            options=[
                ft.dropdown.Option("dinheiro", "Dinheiro"),
                ft.dropdown.Option("mpesa", "M-Pesa"),
                ft.dropdown.Option("emola", "e-Mola"),
                ft.dropdown.Option("cartao", "Cartão"),
                ft.dropdown.Option("ponto24", "Ponto24")
            ],
            width=200,
            on_change=on_pagamento_change
        )
        valor_pago_field = ft.TextField(
            label="Valor Pago",
            width=150,
            keyboard_type=ft.KeyboardType.NUMBER,
            on_change=on_valor_pago_change,
            visible=(pagamento_state["value"] == "dinheiro")
        )
        troco_text = ft.Text("", color=ft.colors.BLUE, size=15, visible=(pagamento_state["value"] == "dinheiro"))
        def salvar_status(ev):
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', (status_state["value"], pedido["id"]))
            conn.commit()
            conn.close()
            dialog_ref["dialog"].open = False
            atualizar_grid()
        def pagar(ev):
            total = pedido["valor"]
            if pagamento_state["value"] == "dinheiro":
                valor_pago = valor_pago_state["value"]
                if valor_pago < total:
                    erro_valor_pago.value = "Valor insuficiente!"
                    page.update()
                    return
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            # Baixar estoque dos produtos do pedido
            cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (pedido['id'],))
            for prod_id, qty in cursor.fetchall():
                cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, prod_id))
            # Registrar venda
            user_id = user[0] if user else None
            cursor.execute('''
                INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (pedido["id"], user_id, pagamento_state["value"], pedido["valor"], datetime.now().isoformat()))
            # Atualizar status do pedido
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ("entregue", pedido["id"]))
            # Liberar mesa se houver
            cursor.execute('SELECT table_id FROM orders WHERE id = ?', (pedido["id"],))
            row = cursor.fetchone()
            if row and row[0]:
                cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (row[0],))
            conn.commit()
            conn.close()
            # Atualiza o status local para garantir bloqueio ao reabrir
            pedido["status"] = "entregue"
            dialog_ref["dialog"].open = False
            atualizar_grid()
        def cancelar_pedido(ev):
            conn = None
            try:
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                # Devolver estoque dos produtos
                cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (pedido['id'],))
                for prod_id, qty in cursor.fetchall():
                    cursor.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (qty, prod_id))
                # Atualizar status do pedido
                cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ("cancelado", pedido['id']))
                # Liberar mesa se houver
                cursor.execute('SELECT table_id FROM orders WHERE id = ?', (pedido['id'],))
                row = cursor.fetchone()
                if row and row[0]:
                    cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (row[0],))
                conn.commit()
                pedido['status'] = 'cancelado'
                dialog_ref["dialog"].open = False
                atualizar_grid()
            except Exception as ex:
                if conn:
                    conn.rollback()
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"Erro ao cancelar pedido: {ex}"),
                    bgcolor=ft.colors.RED
                ))
            finally:
                if conn:
                    conn.close()
        # Função para atualizar os botões de ação
        def update_actions():
            if is_finalizado:
                dialog_ref["dialog"].actions = [
                    ft.TextButton("Fechar", on_click=lambda e: (setattr(dialog_ref["dialog"], 'open', False), page.update())),
                ]
            elif status_state["value"] == "pronto":
                dialog_ref["dialog"].actions = [
                    ft.TextButton("Cancelar Pedido", on_click=cancelar_pedido, style=ft.ButtonStyle(color=ft.colors.RED)),
                    pagamento_dropdown,
                    ft.Container(height=12),
                    valor_pago_field if pagamento_state["value"] == "dinheiro" else None,
                    troco_text if pagamento_state["value"] == "dinheiro" else None,
                    erro_valor_pago if pagamento_state["value"] == "dinheiro" else None,
                    ft.Container(height=10),
                    ft.ElevatedButton("Pagar", icon=ft.icons.PAYMENTS, on_click=pagar, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE)
                ]
            else:
                dialog_ref["dialog"].actions = [
                    ft.TextButton("Cancelar Pedido", on_click=cancelar_pedido, style=ft.ButtonStyle(color=ft.colors.RED)),
                    ft.ElevatedButton("Salvar", icon=ft.icons.SAVE, on_click=salvar_status, bgcolor=ft.colors.BLUE, color=ft.colors.WHITE)
                ]
            # Remover None dos actions
            dialog_ref["dialog"].actions = [a for a in dialog_ref["dialog"].actions if a]
            page.update()
        dialog = ft.AlertDialog(
            title=ft.Text(f"Gerenciar Pedido #{pedido['id']}"),
            content=ft.Column([
                ft.Text(f"Mesa: {pedido['mesa']}"),
                ft.Text(f"Cliente: {pedido['cliente']}"),
                ft.Text(f"Itens: {pedido['itens']}"),
                ft.Text(f"Valor: {format_metical(pedido['valor'])}"),
            ] + ([] if not is_finalizado else [ft.Text(f"Status: {pedido['status'].capitalize()}", color=ft.colors.GREEN if pedido['status']=='entregue' else ft.colors.RED)] )
            + ([] if is_finalizado else [status_dropdown]),
            spacing=10),
            actions=[]
        )
        dialog_ref["dialog"] = dialog
        update_actions()
        page.dialog = dialog
        dialog.open = True
        page.update()

    def on_busca_change(e):
        busca_valor["value"] = e.control.value
        pagina_atual["value"] = 0
        atualizar_grid()

    def proxima_pagina():
        pagina_atual['value'] += 1
        atualizar_grid()

    def anterior_pagina():
        pagina_atual['value'] -= 1
        atualizar_grid()

    # Sistema de auto-refresh para novos pedidos
    last_order_count = {"value": 0}
    
    def check_for_new_orders():
        """Verifica se há novos pedidos e atualiza automaticamente"""
        try:
            # Animar o indicador de refresh
            status_indicator.content.controls[0].name = ft.icons.SYNC
            page.update()
            
            current_orders = get_pedidos()
            current_count = len(current_orders)
            
            if current_count > last_order_count["value"]:
                # Há novos pedidos, atualizar a grid
                last_order_count["value"] = current_count
                atualizar_grid()
                # Mostrar notificação
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"🆕 Novo pedido recebido! Total: {current_count} pedidos"),
                    bgcolor=ft.colors.GREEN_400,
                    duration=3000
                ))
            elif current_count != last_order_count["value"]:
                # Atualizar contador (pode ter havido exclusões)
                last_order_count["value"] = current_count
                atualizar_grid()
            
            # Resetar o indicador
            status_indicator.content.controls[0].name = ft.icons.SYNC
            page.update()
        except Exception as e:
            print(f"Erro ao verificar novos pedidos: {e}")
    
    # Inicializar contador
    last_order_count["value"] = len(get_pedidos())
    
    # Sistema de auto-refresh usando page.window.set_timer
    def schedule_next_check():
        """Agenda a próxima verificação de novos pedidos"""
        try:
            # Usar page.window.set_timer que é o método correto do Flet
            page.window.set_timer(5000, lambda _: check_for_new_orders_and_schedule())
        except Exception as e:
            print(f"Erro ao agendar verificação: {e}")
    
    def check_for_new_orders_and_schedule():
        """Verifica novos pedidos e agenda a próxima verificação"""
        check_for_new_orders()
        schedule_next_check()
    
    # Iniciar o sistema de auto-refresh
    schedule_next_check()

    # Inicializa grid e paginação
    atualizar_grid()

    # Campos de filtro
    busca_field = ft.TextField(
                    label="Buscar",
                    width=240,
                    height=36,
                    text_size=13,
                    content_padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    hint_text="Buscar por cliente, mesa ou número do pedido",
                    on_change=on_busca_change
    )
    status_filtro_dropdown = ft.Dropdown(
        label="Status dos Pedidos",
        value=status_filtro_valor["value"],
        options=[ft.dropdown.Option(opt[0], opt[1]) for opt in status_filtro_options],
        width=240,
        on_change=on_status_filtro_change
    )
    excluir_button = ft.ElevatedButton("Excluir Pedidos", icon=ft.icons.DELETE, on_click=excluir_pedidos_filtrados, style=ft.ButtonStyle(bgcolor=ft.colors.RED, color=ft.colors.WHITE))

    return ft.Column([
        header,
        ft.Container(height=8),
        # Área de filtros compacta
        ft.Container(
            content=ft.Row([
                busca_field,
                status_filtro_dropdown,
                ft.Container(width=8),
                excluir_button
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.END, spacing=12),
            bgcolor=ft.colors.BLUE_50,
            border_radius=6,
            border=ft.border.all(1, ft.colors.BLUE_100),
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            margin=ft.margin.only(left=12, right=12, bottom=8)
        ),
        # Cards e paginação
            ft.Container(
            content=ft.Column([
        pedidos_area,
                ft.Container(height=8),
        paginacao_row[0]
            ], expand=True),
            expand=True,
            padding=ft.padding.symmetric(horizontal=8)
        )
    ], expand=True) 