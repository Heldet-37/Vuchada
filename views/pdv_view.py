import flet as ft
import sqlite3
from datetime import datetime


def format_metical(value):
    """Formata um valor para o formato de Metical"""
    if value is None:
        value = 0
    return f"{float(value):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"


def PDVView(page: ft.Page, on_back=None, user=None, on_navigate=None):
    current_order = {'id': None, 'table_id': None, 'items': [], 'total': 0.0}
    selected_table = {'id': None, 'number': None}
    user_id = user[0] if user else None

    # Ao sair do PDV, descartar pedido de balcão não finalizado
    def descartar_pedido_balcao():
        if current_order['id']:
            conn = sqlite3.connect('database/restaurant.db')
            try:
                cursor = conn.cursor()
                # Verificar status do pedido
                cursor.execute('SELECT status, table_id FROM orders WHERE id = ?', (current_order['id'],))
                row = cursor.fetchone()
                if not row:
                    return
                status, table_id = row
                # Só descartar se for balcão OU se for mesa e status ainda 'pendente'
                if (not table_id) or (table_id and status == 'pendente'):
                    # Devolver estoque dos produtos
                    cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (current_order['id'],))
                    for prod_id, qty in cursor.fetchall():
                        cursor.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (qty, prod_id))
                    # Liberar a mesa se for mesa
                    if table_id:
                        cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (table_id,))
                    # Remover itens e pedido
                    cursor.execute('DELETE FROM order_items WHERE order_id = ?', (current_order['id'],))
                    cursor.execute('DELETE FROM orders WHERE id = ?', (current_order['id'],))
                    current_order['id'] = None
                    current_order['table_id'] = None
                    current_order['items'] = []
                    current_order['total'] = 0.0
                conn.commit()
            finally:
                conn.close()
    # Chamar descartar_pedido_balcao ao sair do PDV
    def on_back_pdv(e=None):
        descartar_pedido_balcao()
        if on_back:
            on_back(e)

    # Categoria Dropdown principal (deve ser definido antes do layout)
    category_dropdown = ft.Dropdown(
        label="Categoria",
        width=200,
        options=[],
        on_change=lambda e: load_products_by_category(e.control.value)
    )

    # Definir products_grid antes de qualquer uso
    products_grid = ft.GridView(
        runs_count=3,  # 3 cards por linha
        max_extent=200,  # Cards um pouco maiores
        child_aspect_ratio=0.9,
        spacing=15,
        run_spacing=15
    )

    # Scroll para o grid de produtos com barra sempre visível e estilizada
    products_grid_scroll = ft.Container(
        content=ft.Column(
        [products_grid],
        expand=True,
        scroll=ft.ScrollMode.ALWAYS,  # Deixa a barra sempre visível
        ),
        # Aumentar o padding para afastar a barra de rolagem dos cards
        padding=ft.padding.only(right=30),
        expand=True
    )

    # Definir order_items_list antes de qualquer uso
    order_items_list = ft.ListView(
        height=320,
        spacing=8,
        padding=10
    )

    # Definir tables_grid antes de qualquer uso
    tables_grid = ft.GridView(
        expand=0,
        runs_count=4,
        max_extent=160,
        child_aspect_ratio=1.0,
        spacing=10,
        run_spacing=10
    )
    tables_grid_scroll = ft.Container(
        content=ft.Column(
            [tables_grid],
            scroll=ft.ScrollMode.ALWAYS
        ),
        height=400  # ajuste conforme necessário
    )

    # Definir header antes do layout principal
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.Icon(
                    name=ft.icons.POINT_OF_SALE,
                    size=36,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "PDV - Ponto de Venda",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),
                ft.Text(
                    f"Mesa: {selected_table['number'] or 'Não selecionada'}",
                    size=16,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "Gerenciar Mesas",
                    icon=ft.icons.TABLE_RESTAURANT,
                    on_click=lambda e: on_navigate("/mesas") if on_navigate else page.go("/mesas"),
                    bgcolor=ft.colors.BLUE_700,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "Ver Pedidos",
                    icon=ft.icons.RESTAURANT_MENU,
                    on_click=lambda e: on_navigate("/pedidos") if on_navigate else page.go("/pedidos"),
                    bgcolor=ft.colors.AMBER_700,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "Voltar",
                    icon=ft.icons.ARROW_BACK,
                    on_click=on_back_pdv,
                    bgcolor=ft.colors.WHITE,
                    color=ft.colors.GREEN_900
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        padding=ft.padding.only(top=30, left=40, right=40, bottom=30),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06))
    )

    # Área de produtos (usar o container com scroll)
    products_area = ft.Container(
        content=ft.Column([
            ft.Text("Produtos", size=20, weight=ft.FontWeight.BOLD),
            ft.Row([
                category_dropdown
            ]),
            ft.Container(height=8),
            products_grid_scroll  # Usar o container com scroll
        ], expand=True),
        padding=20,
        border=ft.border.all(1, ft.colors.GREY_400),
        border_radius=10,
        expand=True
    )

    # Mensagem visual fora da grid
    mesas_status_text = ft.Text("", color=ft.colors.RED, size=16)

    # Mensagem visual para status do pedido
    pedido_status_text = ft.Text("", color=ft.colors.BLUE, size=16)

    # Texto do total (variável global para facilitar atualização)
    total_text = ft.Text(format_metical(0), size=18, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN)

    def update_total_display():
        """Atualiza a exibição do total"""
        total_text.value = format_metical(current_order.get('total', 0))
        page.update()

    # Filtro de status de mesas
    mesa_status_filter = ft.Dropdown(
        label="Mostrar Mesas",
        width=180,
        value="livre",
        options=[
            ft.dropdown.Option("livre", "Livres"),
            ft.dropdown.Option("ocupada", "Ocupadas"),
            ft.dropdown.Option("todas", "Todas")
        ],
        on_change=lambda e: load_tables()
    )

    def load_tables():
        try:
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            filtro = mesa_status_filter.value or "livre"
            if filtro == "todas":
                cursor.execute("SELECT id, number, status FROM tables ORDER BY number")
            else:
                cursor.execute("SELECT id, number, status FROM tables WHERE status = ? ORDER BY number", (filtro,))
            tables = cursor.fetchall()
            
            # Buscar contagem de pedidos ativos para cada mesa
            active_orders_count = {}
            cursor.execute('''
                SELECT table_id, COUNT(*) as count 
                FROM orders 
                WHERE table_id IS NOT NULL AND status IN ('pendente', 'preparando', 'pronto')
                GROUP BY table_id
            ''')
            for table_id, count in cursor.fetchall():
                active_orders_count[table_id] = count
            
            conn.close()
            tables_grid.controls.clear()
            if not tables:
                mesas_status_text.value = 'Nenhuma mesa encontrada para o filtro selecionado.'
            else:
                mesas_status_text.value = ''
            for t in tables:
                tid, number, status = t
                is_selected = selected_table.get('id') == tid
                active_orders = active_orders_count.get(tid, 0)
                
                status_colors = {
                    'livre': ft.colors.GREEN,
                    'ocupada': ft.colors.RED,
                    'reservada': ft.colors.ORANGE,
                    'limpeza': ft.colors.GREY
                }
                
                # Conteúdo do card da mesa
                mesa_content = [
                        ft.Text(f"Mesa {number}", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.Container(
                            content=ft.Text(status.capitalize(), color=ft.colors.WHITE, size=12),
                            bgcolor=status_colors.get(status, ft.colors.GREY),
                            padding=5,
                            border_radius=5
                        )
                ]
                
                # Adicionar indicador de pedidos ativos se houver
                if active_orders > 0:
                    mesa_content.append(
                        ft.Container(
                            content=ft.Text(f"{active_orders} pedido(s)", color=ft.colors.WHITE, size=11, weight=ft.FontWeight.BOLD),
                            bgcolor=ft.colors.AMBER_600,
                            padding=4,
                            border_radius=8
                        )
                    )
                
                table_card = ft.Container(
                    content=ft.Column(
                        mesa_content,
                        alignment=ft.MainAxisAlignment.CENTER, 
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8
                    ),
                    bgcolor=ft.colors.BLUE_800 if not is_selected else ft.colors.BLUE_900,
                    border=ft.border.all(3, ft.colors.GREEN if is_selected else ft.colors.BLUE_600),
                    border_radius=10,
                    padding=16,
                    on_click=lambda e, tid=tid, number=number: select_table_card(tid, number)
                )
                tables_grid.controls.append(table_card)
            page.update()
        except Exception as ex:
            mesas_status_text.value = f'Erro ao carregar mesas: {ex}'
            tables_grid.controls.clear()
        page.update()

    def load_categories():
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        
        # Adicionar opção "Todas"
        options = [ft.dropdown.Option(key="all", text="Todas as Categorias")]
        options.extend([
            ft.dropdown.Option(key=str(c[0]), text=c[1])
            for c in categories
        ])
        category_dropdown.options = options
        page.update()

    def select_table_card(tid, number):
        print(f"[DEBUG] select_table_card: tid={tid}, number={number}")
        selected_table['id'] = tid
        selected_table['number'] = number
        # Atualizar header se possível
        if hasattr(header, 'content') and hasattr(header.content, 'controls') and len(header.content.controls) > 3:
            header.content.controls[3].value = f"Mesa: {number}"
        # Buscar pedidos abertos para a mesa
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, created_at, total_amount, status FROM orders
            WHERE table_id = ? AND status IN ('pendente', 'preparando', 'pronto')
            ORDER BY created_at DESC
        ''', (tid,))
        pedidos = cursor.fetchall()
        conn.close()
        def carregar_pedido_existente(order_id):
            current_order['id'] = order_id
            current_order['table_id'] = tid
            # Buscar total e itens
            load_order_items(order_id)
            update_pedido_status()
            page.update()
        def preparar_novo_pedido(e=None):
            current_order['id'] = None
            current_order['table_id'] = tid
            current_order['items'] = []
            current_order['total'] = 0.0
            order_items_list.controls.clear()
            update_pedido_status()
            if e is not None:
                page.dialog.open = False
            page.update()
        if not pedidos:
            # Se não há pedidos abertos, só prepara o estado para novo pedido
            preparar_novo_pedido()
            return
        # Se há pedidos abertos, mostrar modal
        pedidos_controls = []
        for p in pedidos:
            pid, created_at, total, status = p
            # Formatar data/hora
            try:
                dt = datetime.fromisoformat(created_at)
                time_str = dt.strftime("%H:%M")
            except:
                time_str = "N/A"
            
            pedidos_controls.append(
                ft.Container(
                    content=ft.Column([
                ft.Row([
                            ft.Text(f"Pedido #{pid}", size=16, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800),
                            ft.Container(
                                content=ft.Text(status.capitalize(), color=ft.colors.WHITE, size=12),
                                bgcolor=ft.colors.GREEN if status == 'pronto' else ft.colors.ORANGE if status == 'preparando' else ft.colors.BLUE,
                                padding=5,
                                border_radius=5
                            )
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                        ft.Text(f"Total: {format_metical(total)}", size=14, color=ft.colors.GREEN_700),
                        ft.Text(f"Criado às: {time_str}", size=12, color=ft.colors.GREY_600),
                        ft.ElevatedButton(
                            "Selecionar Pedido", 
                            icon=ft.icons.ARROW_FORWARD,
                            on_click=lambda e, pid=pid: (setattr(page.dialog, 'open', False), carregar_pedido_existente(pid)),
                            bgcolor=ft.colors.BLUE_600,
                            color=ft.colors.WHITE
                        )
                    ], spacing=8),
                    padding=12,
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=8,
                    bgcolor=ft.colors.WHITE
                )
            )
        
        dialog = ft.AlertDialog(
            title=ft.Text(f"Mesa {number} - Gerenciar Pedidos", size=20, weight=ft.FontWeight.BOLD),
            content=ft.Column([
                ft.Text(f"Esta mesa tem {len(pedidos)} pedido(s) ativo(s).", size=14, color=ft.colors.GREY_700),
                ft.Container(height=10),
                ft.Text("Pedidos existentes:", size=16, weight=ft.FontWeight.BOLD),
                ft.Container(height=5),
                *pedidos_controls,
                ft.Container(height=15),
                ft.Container(
                    content=ft.ElevatedButton(
                        "➕ Novo Pedido para esta Mesa", 
                        icon=ft.icons.ADD,
                        on_click=preparar_novo_pedido, 
                        bgcolor=ft.colors.GREEN, 
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(padding=15)
                    ),
                    alignment=ft.alignment.center
                ),
                ft.Text("💡 Dica: Cada cliente pode ter seu próprio pedido!", size=12, color=ft.colors.BLUE_600, italic=True)
            ], spacing=12, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update()))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def check_active_order(table_id):
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, total_amount FROM orders 
            WHERE table_id = ? AND status IN ('pendente', 'preparando')
        ''', (table_id,))
        order = cursor.fetchone()
        conn.close()
        
        if order:
            current_order['id'] = order[0]
            current_order['table_id'] = table_id
            current_order['total'] = order[1]
            load_order_items(order[0])

    def load_order_items(order_id):
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT oi.product_id, p.name, oi.quantity, oi.unit_price, oi.notes
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        ''', (order_id,))
        items = cursor.fetchall()
        
        # Buscar o total do pedido
        cursor.execute('SELECT COALESCE(total_amount, 0) FROM orders WHERE id = ?', (order_id,))
        total = cursor.fetchone()[0] or 0
        current_order['total'] = float(total)
        
        conn.close()
        
        current_order['items'] = []
        order_items_list.controls.clear()
        
        for item in items:
            product_id, name, quantity, unit_price, notes = item
            current_order['items'].append({
                'product_id': product_id,
                'name': name,
                'quantity': quantity,
                'unit_price': unit_price,
                'notes': notes
            })
            
            def make_update_qty_fn(pid, delta):
                def fn(e):
                    update_item_quantity(pid, delta)
                return fn
                
            def make_remove_fn(pid):
                def fn(e):
                    remove_item_from_order(pid)
                return fn

            # Container para cada item do pedido com melhor organização
            item_container = ft.Container(
                content=ft.Column([
                    # Nome do produto em linha própria
                    ft.Text(f"{name}", size=14, weight=ft.FontWeight.BOLD),
                    # Controles em uma linha separada
                    ft.Row([
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                on_click=make_update_qty_fn(product_id, -1),
                                tooltip="Diminuir",
                                icon_color=ft.colors.RED_400,
                                icon_size=20
                            ),
                            ft.Text(
                                str(quantity),
                                size=14,
                                width=30,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.IconButton(
                                icon=ft.icons.ADD_CIRCLE_OUTLINE,
                                on_click=make_update_qty_fn(product_id, 1),
                                tooltip="Aumentar",
                                icon_color=ft.colors.GREEN_400,
                                icon_size=20
                            ),
                        ], spacing=0),
                        ft.Container(expand=True),  # Espaçador flexível
                        ft.Text(
                            format_metical(unit_price * quantity),
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLUE_900
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            on_click=make_remove_fn(product_id),
                            tooltip="Remover",
                            icon_color=ft.colors.RED,
                            icon_size=20
                        )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=ft.padding.all(8),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                bgcolor=ft.colors.WHITE
            )
            order_items_list.controls.append(item_container)
        
        # Atualizar o total usando a função auxiliar
        update_total_display()
        
        page.update()

    def update_item_quantity(product_id, delta):
        if not current_order['id']:
            return
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT quantity FROM order_items WHERE order_id = ? AND product_id = ?
        ''', (current_order['id'], product_id))
        row = cursor.fetchone()
        if not row:
            conn.close()
            return
        new_qty = row[0] + delta
        # Buscar estoque do produto
        cursor.execute('SELECT stock FROM products WHERE id = ?', (product_id,))
        stock_row = cursor.fetchone()
        stock = stock_row[0] if stock_row else 0
        if delta > 0:
            if new_qty > stock:
                conn.close()
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Estoque insuficiente!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))
                return
            elif new_qty == stock:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Última unidade!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.ORANGE_400
                ))
            elif stock - new_qty < 2:
                page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text("Estoque baixo!", color=ft.colors.AMBER_400),
                        bgcolor=ft.colors.AMBER_400
                    )
                )
        # Ajustar estoque de balcão ao incrementar/decrementar
        if not selected_table['id']:
            if delta > 0:
                cursor.execute('UPDATE products SET stock = stock - 1 WHERE id = ?', (product_id,))
            elif delta < 0:
                cursor.execute('UPDATE products SET stock = stock + 1 WHERE id = ?', (product_id,))
        if new_qty < 1:
            # Remove item se quantidade < 1
            cursor.execute('DELETE FROM order_items WHERE order_id = ? AND product_id = ?', (current_order['id'], product_id))
        else:
            cursor.execute('UPDATE order_items SET quantity = ? WHERE order_id = ? AND product_id = ?', (new_qty, current_order['id'], product_id))
        # Atualizar total do pedido
        cursor.execute('''
            UPDATE orders 
            SET total_amount = COALESCE((
                SELECT SUM(quantity * unit_price) 
                FROM order_items 
                WHERE order_id = ?
            ), 0)
            WHERE id = ?
        ''', (current_order['id'], current_order['id']))
        conn.commit()
        conn.close()
        load_order_items(current_order['id'])

    def remove_item_from_order(product_id):
        if not current_order['id']:
            return
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM order_items WHERE order_id = ? AND product_id = ?', (current_order['id'], product_id))
        # Atualizar total do pedido
        cursor.execute('''
            UPDATE orders 
            SET total_amount = COALESCE((
                SELECT SUM(quantity * unit_price) 
                FROM order_items 
                WHERE order_id = ?
            ), 0)
            WHERE id = ?
        ''', (current_order['id'], current_order['id']))
        conn.commit()
        conn.close()
        load_order_items(current_order['id'])

    def show_product_details_pdv(product):
        prod_id, name, description, price, image_url, stock = product
        dialog = ft.AlertDialog(
            title=ft.Text(f"Detalhes do Produto: {name}"),
            content=ft.Column([
                ft.Image(src=image_url if image_url else None, width=120, height=120, fit=ft.ImageFit.CONTAIN) if image_url else ft.Icon(ft.icons.IMAGE, size=80, color=ft.colors.GREY_400),
                ft.Text(f"Descrição: {description or '-'}"),
                ft.Text(f"Preço: {price:.2f}MT"),
                ft.Text(f"Estoque: {stock}")
            ], spacing=12),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: (setattr(dialog, 'open', False), page.update()))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    # Ajustar products_grid para exibir imagem, nome, preço, botão adicionar
    def load_products_by_category(category_id=None):
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        if not category_id or category_id == "all":
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock 
                FROM products 
                WHERE is_active = 1
                ORDER BY name
            ''')
        else:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock 
                FROM products 
                WHERE category_id = ? AND is_active = 1
                ORDER BY name
            ''', (category_id,))
        products = cursor.fetchall()
        conn.close()
        products_grid.controls.clear()
        for product in products:
            prod_id, name, description, price, image_url, stock = product
            img = ft.Image(src=image_url if image_url else None, width=80, height=80, fit=ft.ImageFit.CONTAIN) if image_url else ft.Icon(ft.icons.IMAGE, size=70, color=ft.colors.GREY_400)
            product_card = ft.Container(
                width=180,
                height=200,
                content=ft.Stack([
                    ft.Container(
                        content=ft.Column([
                            img,
                            ft.Text(name, size=15, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE, text_align=ft.TextAlign.CENTER, no_wrap=True, overflow=ft.TextOverflow.ELLIPSIS),
                            ft.Text(format_metical(price), size=14, weight=ft.FontWeight.BOLD, color=ft.colors.AMBER_200, text_align=ft.TextAlign.CENTER),
                            ft.Text(f"Estoque: {stock}", size=12, color=ft.colors.WHITE70, text_align=ft.TextAlign.CENTER),
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, spacing=5),
                        alignment=ft.alignment.center,
                        expand=True
                    )
                ]),
                bgcolor=ft.colors.BLUE_800,
                padding=6,
                border_radius=12,
                alignment=ft.alignment.center,
                border=ft.border.all(2, ft.colors.AMBER_200),
                on_click=lambda e, p=product: add_to_order(p),
                tooltip="Adicionar ao pedido"
            )
            products_grid.controls.append(product_card)
        page.update()

    def add_to_order(product):
        try:
            show_success = True
            prod_id, name, description, price, image_url, stock = product
            
            # --- MESA: manter em memória até processar ---
            if selected_table['id']:
                # Verificar se já existe o item no pedido em memória
                found = False
                for item in current_order.get('items', []):
                    if item['product_id'] == prod_id:
                        # Verificar estoque
                        if item['quantity'] + 1 > stock:
                            page.show_snack_bar(ft.SnackBar(
                                content=ft.Text(f"Estoque insuficiente para {name}!", color=ft.colors.WHITE),
                                bgcolor=ft.colors.RED_400
                            ))
                            return
                        item['quantity'] += 1
                        found = True
                        break
                
                if not found:
                    # Verificar estoque para novo item
                    if 1 > stock:
                        page.show_snack_bar(ft.SnackBar(
                            content=ft.Text(f"Estoque insuficiente para {name}!", color=ft.colors.WHITE),
                            bgcolor=ft.colors.RED_400
                        ))
                        return
                    # Adicionar novo item em memória
                    current_order['items'].append({
                        'product_id': prod_id,
                        'name': name,
                        'quantity': 1,
                        'unit_price': price
                    })
                
                # Atualizar total em memória
                current_order['total'] = sum(i['quantity'] * i['unit_price'] for i in current_order['items'])
                
                # Atualizar interface
                load_order_items_mem()
                update_total_display()
                update_pedido_status()
                load_tables()
                
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"{name} adicionado ao pedido", color=ft.colors.WHITE),
                    bgcolor=ft.colors.GREEN_400
                ))
                return
            
            # --- BALCÃO: fluxo normal (criar no banco imediatamente) ---
            # Se não existe pedido, criar um novo
            if not current_order['id']:
                pedido_status_text.value = "Pedido de Balcão (sem mesa associada)"
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO orders (table_id, status, total_amount, created_at)
                    VALUES (?, 'pendente', 0.0, ?)
                ''', (None, datetime.now().isoformat()))
                current_order['id'] = cursor.lastrowid
                conn.commit()
                conn.close()
            
            # Verificar quantidade já no pedido atual
            qty_in_order = 0
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT quantity FROM order_items 
                WHERE order_id = ? AND product_id = ?
            ''', (current_order['id'], prod_id))
            existing_item = cursor.fetchone()
            if existing_item:
                qty_in_order = existing_item[0]
            
            # Checar estoque
            if qty_in_order + 1 > stock:
                conn.close()
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"Estoque insuficiente para {name}!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))
                return
            elif qty_in_order + 1 == stock:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"Última unidade de {name}!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.ORANGE_400
                ))
            elif stock - (qty_in_order + 1) < 2:
                page.show_snack_bar(
                    ft.SnackBar(
                        content=ft.Text(f"Estoque baixo de {name}!", color=ft.colors.WHITE),
                        bgcolor=ft.colors.AMBER_400
                    )
                )
                show_success = False
            else:
                show_success = True
            
            # Adicionar novo item ou atualizar quantidade
            if existing_item:
                new_qty = qty_in_order + 1
                cursor.execute('''
                    UPDATE order_items 
                    SET quantity = ? 
                    WHERE order_id = ? AND product_id = ?
                ''', (new_qty, current_order['id'], prod_id))
            else:
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, 1, ?)
                ''', (current_order['id'], prod_id, price))
            
            # Baixar estoque imediatamente se for balcão
            cursor.execute('UPDATE products SET stock = stock - 1 WHERE id = ?', (prod_id,))
            
            # Atualizar total do pedido
            cursor.execute('''
                UPDATE orders SET total_amount = (
                    SELECT SUM(quantity * unit_price) 
                    FROM order_items 
                    WHERE order_id = ?
                ) WHERE id = ?
            ''', (current_order['id'], current_order['id']))
            conn.commit()
            conn.close()
            
            # Recarregar itens do pedido
            load_order_items(current_order['id'])
            if show_success:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"{name} adicionado ao pedido", color=ft.colors.WHITE),
                    bgcolor=ft.colors.GREEN_400
                ))
            update_pedido_status()
            load_tables()
            
        except Exception as e:
            print(f"[ERROR] Erro ao adicionar produto: {e}")
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao adicionar produto: {str(e)}"),
                bgcolor=ft.colors.RED_400
            ))
    # Função para exibir itens do carrinho em memória (mesa)
    def load_order_items_mem():
        order_items_list.controls.clear()
        for item in current_order.get('items', []):
            def make_update_qty_fn(pid, delta):
                def fn(e):
                    for it in current_order['items']:
                        if it['product_id'] == pid:
                            if it['quantity'] + delta < 1:
                                current_order['items'].remove(it)
                            else:
                                it['quantity'] += delta
                            break
                    current_order['total'] = sum(i['quantity'] * i['unit_price'] for i in current_order['items'])
                    load_order_items_mem()
                    update_total_display()
                return fn
            def make_remove_fn(pid):
                def fn(e):
                    for it in current_order['items']:
                        if it['product_id'] == pid:
                            current_order['items'].remove(it)
                            break
                    current_order['total'] = sum(i['quantity'] * i['unit_price'] for i in current_order['items'])
                    load_order_items_mem()
                    update_total_display()
                return fn
            item_container = ft.Container(
                content=ft.Column([
                    ft.Text(f"{item['name']}", size=14, weight=ft.FontWeight.BOLD),
                    ft.Row([
                        ft.Row([
                            ft.IconButton(
                                icon=ft.icons.REMOVE_CIRCLE_OUTLINE,
                                on_click=make_update_qty_fn(item['product_id'], -1),
                                tooltip="Diminuir",
                                icon_color=ft.colors.RED_400,
                                icon_size=20
                            ),
                            ft.Text(
                                str(item['quantity']),
                                size=14,
                                width=30,
                                text_align=ft.TextAlign.CENTER,
                                weight=ft.FontWeight.BOLD
                            ),
                            ft.IconButton(
                                icon=ft.icons.ADD_CIRCLE_OUTLINE,
                                on_click=make_update_qty_fn(item['product_id'], 1),
                                tooltip="Aumentar",
                                icon_color=ft.colors.GREEN_400,
                                icon_size=20
                            ),
                        ], spacing=0),
                        ft.Container(expand=True),
                        ft.Text(
                            format_metical(item['unit_price'] * item['quantity']),
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLUE_900
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE_OUTLINE,
                            on_click=make_remove_fn(item['product_id']),
                            tooltip="Remover",
                            icon_color=ft.colors.RED,
                            icon_size=20
                        )
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ]),
                padding=ft.padding.all(8),
                border=ft.border.all(1, ft.colors.GREY_300),
                border_radius=8,
                bgcolor=ft.colors.WHITE
            )
            order_items_list.controls.append(item_container)
        update_total_display()
        page.update()

    def finalize_order():
        """Finaliza o pedido atual, atualiza o estoque e registra a venda"""
        if not current_order['id']:
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Nenhum pedido para finalizar", color=ft.colors.WHITE),
                bgcolor=ft.colors.ORANGE_400
            ))
            return
        # Se for balcão (sem mesa), abrir modal para método de pagamento
        if not selected_table['id']:
            pagamento_state = {"value": "dinheiro"}
            valor_pago_state = {"value": ""}
            troco_state = {"value": 0.0}
            erro_valor_pago = ft.Text("", color=ft.colors.RED, size=13)
            def on_pagamento_change(e):
                pagamento_state["value"] = e.control.value
                valor_pago_field.visible = (pagamento_state["value"] == "dinheiro")
                troco_text.visible = (pagamento_state["value"] == "dinheiro")
                erro_valor_pago.value = ""
                page.update()
            def on_valor_pago_change(e):
                try:
                    valor_pago = float(e.control.value.replace(",", "."))
                except Exception:
                    valor_pago = 0.0
                valor_pago_state["value"] = valor_pago
                total = current_order["total"]
                troco = valor_pago - total
                troco_state["value"] = troco
                if valor_pago < total:
                    erro_valor_pago.value = "Valor insuficiente!"
                else:
                    erro_valor_pago.value = ""
                troco_text.value = f"Troco: {troco:.2f} MT" if pagamento_state["value"] == "dinheiro" and valor_pago else ""
                page.update()
            def confirmar_pagamento(ev):
                total = current_order["total"]
                if pagamento_state["value"] == "dinheiro":
                    valor_pago = valor_pago_state["value"]
                    if valor_pago < total:
                        erro_valor_pago.value = "Valor insuficiente!"
                        page.update()
                        return
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                # Registrar venda
                cursor.execute('''
                    INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
                    VALUES (?, ?, ?, ?, ?)
                ''', (current_order["id"], user_id, pagamento_state["value"], current_order["total"], datetime.now().isoformat()))
                # Remover pedido do banco (não deixar como entregue nos pedidos), mas manter os itens para cálculo do lucro
                cursor.execute('DELETE FROM orders WHERE id = ?', (current_order["id"],))
                conn.commit()
                conn.close()
                # Limpar pedido atual
                current_order['id'] = None
                current_order['table_id'] = None
                current_order['items'] = []
                current_order['total'] = 0.0
                order_items_list.controls.clear()
                update_total_display()
                load_tables()
                load_products_by_category()
                page.dialog.open = False
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Venda finalizada com sucesso!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.GREEN_400
                ))
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
            dialog = ft.AlertDialog(
                title=ft.Text("Finalizar Venda - Balcão"),
                content=ft.Column([
                    ft.Text("Escolha o método de pagamento:"),
                    pagamento_dropdown,
                    ft.Container(height=12),
                    ft.Column([
                        valor_pago_field,
                        troco_text,
                        erro_valor_pago
                    ], visible=(pagamento_state["value"] == "dinheiro"))
                ], spacing=16),
                actions=[
                    ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                    ft.ElevatedButton("Confirmar", icon=ft.icons.PAYMENTS, on_click=confirmar_pagamento, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE)
                ]
            )
            # Inicialmente só mostra campo se for dinheiro
            dialog.content.controls[2].visible = (pagamento_state["value"] == "dinheiro")
            page.dialog = dialog
            dialog.open = True
            page.update()
            return
        # (Fluxo normal para pedidos de mesa)
        conn = None
        try:
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            # Buscar a mesa associada ao pedido
            cursor.execute('SELECT table_id FROM orders WHERE id = ?', (current_order['id'],))
            table_id = cursor.fetchone()[0]
            # Baixar estoque dos produtos do pedido
            cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (current_order['id'],))
            for prod_id, qty in cursor.fetchall():
                cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (qty, prod_id))
            # Registrar venda
            cursor.execute('''
                INSERT INTO sales (order_id, user_id, payment_method, total_amount, created_at)
                VALUES (?, ?, ?, ?, ?)
            ''', (current_order["id"], user_id, 'dinheiro', current_order["total"], datetime.now().isoformat()))
            # Atualizar status do pedido
            cursor.execute('UPDATE orders SET status = ? WHERE id = ?', ("entregue", current_order["id"]))
            # Liberar a mesa se existir
            if table_id:
                cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (table_id,))
            conn.commit()
            # Limpar pedido atual
            current_order['id'] = None
            current_order['table_id'] = None
            current_order['items'] = []
            current_order['total'] = 0.0
            order_items_list.controls.clear()
            update_total_display()
            load_tables()
            load_products_by_category()
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Venda finalizada com sucesso!", color=ft.colors.WHITE),
                bgcolor=ft.colors.GREEN_400
            ))
        except Exception as e:
            if conn:
                conn.rollback()
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao finalizar pedido: {str(e)}"),
                bgcolor=ft.colors.RED_400
            ))
        finally:
            if conn:
                conn.close()
        page.update()

    def cancel_order():
        if not current_order['id']:
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Nenhum pedido para cancelar", color=ft.colors.WHITE),
                bgcolor=ft.colors.ORANGE_400
            ))
            return
        
        conn = None
        try:
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            # Devolver estoque dos produtos se for balcão
            if not selected_table['id']:
                cursor.execute('SELECT product_id, quantity FROM order_items WHERE order_id = ?', (current_order['id'],))
                for prod_id, qty in cursor.fetchall():
                    cursor.execute('UPDATE products SET stock = stock + ? WHERE id = ?', (qty, prod_id))
            # Buscar a mesa associada ao pedido
            cursor.execute('SELECT table_id FROM orders WHERE id = ?', (current_order['id'],))
            table_id = cursor.fetchone()[0]
            # Cancelar pedido
            cursor.execute('UPDATE orders SET status = "cancelado" WHERE id = ?', (current_order['id'],))
            # Liberar a mesa se existir
            if table_id:
                cursor.execute('UPDATE tables SET status = "livre" WHERE id = ?', (table_id,))
            conn.commit()
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Pedido cancelado", color=ft.colors.WHITE),
                bgcolor=ft.colors.AMBER_700
            ))
            # Limpar pedido atual
            current_order['id'] = None
            current_order['table_id'] = None
            current_order['items'] = []
            current_order['total'] = 0.0
            order_items_list.controls.clear()
            update_total_display()
        except Exception as e:
            if conn:
                conn.rollback()
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao cancelar pedido: {str(e)}"),
                bgcolor=ft.colors.RED_400
            ))
        finally:
            if conn:
                conn.close()
            # Recarregar a lista de mesas para atualizar o status
            load_tables()
        page.update()

    def show_new_table_dialog():
        number_field = ft.TextField(label="Número da Mesa")
        capacity_field = ft.TextField(label="Capacidade")
        def save_table(e):
            try:
                number = int(number_field.value)
                capacity = int(capacity_field.value)
                conn = sqlite3.connect('database/restaurant.db')
                try:
                    cursor = conn.cursor()
                    cursor.execute('SELECT 1 FROM tables WHERE number = ?', (number,))
                    if cursor.fetchone():
                        page.show_snack_bar(ft.SnackBar(
                            content=ft.Text(f"Já existe uma mesa com o número {number}", color=ft.colors.WHITE),
                            bgcolor=ft.colors.RED_400
                        ))
                        return
                    cursor.execute('''
                        INSERT INTO tables (number, capacity, status)
                        VALUES (?, ?, 'livre')
                    ''', (number, capacity))
                    conn.commit()
                finally:
                    conn.close()
                dialog.open = False
                page.update()
                load_tables()
            except ValueError:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Por favor, insira valores válidos", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))

        dialog = ft.AlertDialog(
            title=ft.Text("Nova Mesa"),
            content=ft.Column([
                number_field,
                capacity_field
            ], spacing=20),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Salvar", on_click=save_table)
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    # --- FLUXO DE VENDAS: BALCÃO vs MESA ---
    # Se nenhuma mesa for selecionada, é venda de balcão: produtos são vendidos e estoque baixado imediatamente.
    # Se uma mesa for selecionada, é pedido de mesa: só envia para cozinha, pagamento e baixa de estoque só depois.

    # Botão principal do pedido: objeto para texto dinâmico
    pedido_btn = ft.ElevatedButton(
        "Finalizar Venda (Balcão)",
        icon=ft.icons.CHECK,
        style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREEN),
        on_click=lambda _: finalize_order() if not selected_table['id'] else processar_pedido()
    )

    def update_pedido_status():
        print(f"[DEBUG] update_pedido_status: selected_table['id'] = {selected_table['id']}")
        if selected_table['id']:
            pedido_status_text.value = f"Pedido para a Mesa {selected_table['number']}"
            pedido_btn.text = "Processar Pedido (Mesa)"
        else:
            pedido_status_text.value = "Pedido de Balcão (sem mesa associada)"
            pedido_btn.text = "Finalizar Venda (Balcão)"
        print(f"[DEBUG] update_pedido_status: pedido_btn.text = {pedido_btn.text}")
        page.update()

    def processar_pedido():
        """Processa o pedido de mesa: cria o pedido no banco, ocupa a mesa, baixa o estoque e muda status para pendente"""
        print(f"[LOG] Iniciando processamento do pedido para a mesa: {selected_table['number']} (id={selected_table['id']})")
        print(f"[LOG] Estado atual do pedido: {current_order}")
        
        if not current_order.get('items') or not selected_table['id']:
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text("Nenhum pedido para processar", color=ft.colors.WHITE),
                bgcolor=ft.colors.ORANGE_400
            ))
            print("[LOG] Nenhum item no pedido ou mesa não selecionada. Abortando processamento.")
            return
        
        # Verificar se a mesa está livre (só ocupar se estiver livre)
        conn = sqlite3.connect('database/restaurant.db')
        try:
            cursor = conn.cursor()
            cursor.execute('SELECT status FROM tables WHERE id = ?', (selected_table['id'],))
            table_status = cursor.fetchone()
            
            if not table_status:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Mesa não encontrada!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))
                return
            
            # Se a mesa estiver livre, ocupá-la. Se já estiver ocupada, apenas criar o pedido
            should_occupy_table = (table_status[0] == 'livre')
            
            # Criar pedido
            cursor.execute('''
                INSERT INTO orders (table_id, status, total_amount, created_at)
                VALUES (?, 'pendente', ?, ?)
            ''', (selected_table['id'], current_order['total'], datetime.now().isoformat()))
            order_id = cursor.lastrowid
            print(f"[LOG] Pedido criado no banco: order_id={order_id}")
            
            # Criar itens
            for item in current_order['items']:
                print(f"[LOG] Adicionando item ao pedido: {item}")
                cursor.execute('''
                    INSERT INTO order_items (order_id, product_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                ''', (order_id, item['product_id'], item['quantity'], item['unit_price']))
            
            # Ocupar a mesa apenas se estiver livre
            if should_occupy_table:
                cursor.execute('UPDATE tables SET status = "ocupada" WHERE id = ?', (selected_table['id'],))
                print(f"[LOG] Mesa {selected_table['number']} ocupada")
            else:
                print(f"[LOG] Mesa {selected_table['number']} já estava ocupada, mantendo status")
            
            # Baixar estoque dos produtos
            for item in current_order['items']:
                print(f"[LOG] Baixando estoque do produto {item['product_id']} em {item['quantity']} unidade(s)")
                cursor.execute('UPDATE products SET stock = stock - ? WHERE id = ?', (item['quantity'], item['product_id']))
            
            conn.commit()
            print(f"[LOG] Pedido processado com sucesso para a mesa {selected_table['number']} (id={selected_table['id']})")
            
        except Exception as e:
            conn.rollback()
            print(f"[ERROR] Erro ao processar pedido: {e}")
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Erro ao processar pedido: {str(e)}", color=ft.colors.WHITE),
                bgcolor=ft.colors.RED_400
            ))
            return
        finally:
            conn.close()
        
        page.show_snack_bar(ft.SnackBar(
            content=ft.Text("Pedido enviado para a cozinha! O pagamento será feito depois, na tela de Pedidos.", color=ft.colors.WHITE),
            bgcolor=ft.colors.GREEN_400
        ))
        
        # Limpa o pedido atual
        current_order['id'] = None
        current_order['table_id'] = None
        current_order['items'] = []
        current_order['total'] = 0.0
        order_items_list.controls.clear()
        update_total_display()
        load_tables()
        load_products_by_category()
        page.update()

    # Área do pedido atual (movida para depois das definições das funções)
    order_area = ft.Container(
        content=ft.Column([
            ft.Text("Pedido Atual", size=20, weight=ft.FontWeight.BOLD),
            order_items_list,
            ft.Container(height=10),
            ft.Row([
                ft.Text("Total:", size=18, weight=ft.FontWeight.BOLD),
                total_text  # Usar a variável global
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            ft.Container(height=10),
            ft.Row([
                pedido_btn,
                ft.ElevatedButton(
                    "Cancelar Pedido",
                    icon=ft.icons.CANCEL,
                    style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.RED),
                    on_click=lambda _: cancel_order()
                )
            ], alignment=ft.MainAxisAlignment.CENTER)
        ]),
        padding=20,
        border=ft.border.all(1, ft.colors.GREY_400),
        border_radius=10,
        width=480
    )

    # Lista de itens do pedido
    # order_items_list = ft.ListView(
    #     height=300,
    #     spacing=5
    # )

    # Carregar dados iniciais
    load_tables()
    load_categories()
    load_products_by_category()  # Mostrar todos os produtos ao abrir
    update_pedido_status()

    # Remover logs visuais e debug
    # Ajustar layout: header fixo no topo, colunas alinhadas
    return ft.Column([
            header,
            ft.Container(height=12),
            ft.Row([
                # Coluna esquerda: Resumo do pedido
                ft.Container(
                    content=ft.Column([
                        pedido_status_text,
                        order_area
                    ], expand=True),
                    width=480,
                    padding=ft.padding.only(right=8)
                ),
                # Coluna central: Grid de mesas
                ft.Container(
                    content=ft.Column([
                        ft.Text("Mesas", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                        mesa_status_filter,
                        tables_grid_scroll,
                        ft.ElevatedButton("Nova Mesa", icon=ft.icons.ADD, on_click=lambda _: show_new_table_dialog(), style=ft.ButtonStyle(color=ft.colors.WHITE, bgcolor=ft.colors.GREEN, padding=8))
                    ], expand=True),
                    width=260,
                    padding=ft.padding.symmetric(horizontal=8)
                ),
                # Coluna direita: Grid de produtos
                ft.Container(
                    content=ft.Column([
                        ft.Text("Produtos", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                        ft.Row([
                            category_dropdown
                        ]),
                        ft.Container(height=8),
                        products_grid_scroll  # Usar o container com scroll
                    ], expand=True),
                    expand=True,
                    padding=ft.padding.only(left=8)
                )
            ], expand=True)
        ], expand=True) 