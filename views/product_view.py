import flet as ft
from database.models import get_products, create_product, update_product, set_product_active, delete_product, add_stock_entry, get_product_by_id, register_missing_stock_entries, fix_invalid_image_urls
import os
import shutil
import uuid
import logging

def product_header(on_back=None):
    return ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.SHOPPING_CART, size=36, color=ft.colors.WHITE),
            ft.Text("Produtos", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Container(expand=True),
            ft.ElevatedButton("Voltar", icon=ft.icons.ARROW_BACK, on_click=on_back, bgcolor=ft.colors.WHITE, color=ft.colors.BLUE_900)
        ], alignment=ft.MainAxisAlignment.CENTER),
        padding=ft.padding.only(top=30, left=40, right=40, bottom=30),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        border_radius=10,
        shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06))
    )

# Card de produto mock
class ProductCard(ft.UserControl):
    def __init__(self, id, name, price, code, image_url=None, is_active=True, on_edit=None, on_toggle_active=None, on_delete=None, on_details=None):
        super().__init__()
        self.id = id
        self.name = name
        self.price = price
        self.code = code
        self.image_url = image_url or "https://cdn-icons-png.flaticon.com/512/3081/3081559.png"
        self.is_active = is_active
        self.on_edit = on_edit
        self.on_toggle_active = on_toggle_active
        self.on_delete = on_delete
        self.on_details = on_details

    def build(self):
        def format_metical(value):
            return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".") + " MT"
        # Corrigir caminho da imagem local
        img_src = self.image_url
        # Se não for string ou arquivo não existe, usa ícone padrão
        if not isinstance(img_src, str) or not os.path.exists(img_src):
            img_src = "https://cdn-icons-png.flaticon.com/512/3081/3081559.png"
        print(f"[DEBUG] ProductCard: self.image_url = {self.image_url}")
        print(f"[DEBUG] ProductCard: img_src usado = {img_src}")
        if isinstance(img_src, str) and os.path.exists(img_src):
            print(f"[DEBUG] ProductCard: arquivo existe? {os.path.exists(img_src)}")
        return ft.Container(
            width=220,
            height=320,
            bgcolor=ft.colors.WHITE,
            border_radius=16,
            border=ft.border.all(1, ft.colors.GREY_200),
            shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06)),
            padding=0,
            margin=ft.margin.all(4),
            content=ft.Column([
                ft.Stack([
                    ft.Container(
                        content=ft.Image(
                            src=img_src,
                            fit=ft.ImageFit.COVER,
                            width=220,
                            height=80,
                        ),
                        border_radius=ft.border_radius.only(top_left=16, top_right=16),
                        clip_behavior=ft.ClipBehavior.HARD_EDGE,
                    ),
                    ft.Container(
                        content=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(text="Ver detalhes", on_click=lambda e: self.on_details and self.on_details(self.id)),
                                ft.PopupMenuItem(text="Editar", on_click=lambda e: self.on_edit and self.on_edit(self)),
                                ft.PopupMenuItem(text="Excluir", on_click=lambda e: self.on_delete and self.on_delete(self)),
                            ],
                            icon=ft.icons.MORE_VERT,
                        ),
                        alignment=ft.alignment.top_right,
                        padding=ft.padding.only(top=4, right=4),
                    ),
                ], width=220, height=90),
                ft.Container(
                    content=ft.Column([
                        ft.Text(self.name, size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLACK, text_align=ft.TextAlign.CENTER, max_lines=3, overflow=ft.TextOverflow.ELLIPSIS),
                        ft.Text(format_metical(self.price), size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(self.code, size=13, color=ft.colors.BLUE_900, text_align=ft.TextAlign.CENTER, weight=ft.FontWeight.BOLD),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                    padding=ft.padding.symmetric(vertical=14, horizontal=8),
                ),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0)
        )

# Dados mockados para simular muitos produtos
PAGE_SIZE = 12

def view(page: ft.Page, on_back=None):
    state = {"current_page": 1}

    # Carregar categorias do banco
    from database.models import get_connection
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name')
    categories = cursor.fetchall()
    conn.close()
    category_options = [ft.dropdown.Option(str(cid), cname) for cid, cname in categories]
    category_field = ft.Dropdown(label="Categoria", width=200, options=category_options, value=None, on_change=lambda e: update_grid())

    def go_back(e):
        if on_back:
            on_back(e)
        else:
            page.go("/home")

    search_field = ft.TextField(
        hint_text="Buscar produto...",
        prefix_icon=ft.icons.SEARCH,
        width=320,
        border_radius=12,
        bgcolor=ft.colors.WHITE,
        filled=True,
        content_padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_change=lambda e: update_grid(),
    )
    filter_button = ft.IconButton(
        icon=ft.icons.FILTER_LIST,
        tooltip="Filtrar",
        style=ft.ButtonStyle(
            shape={"": ft.RoundedRectangleBorder(radius=12)},
            bgcolor={"": ft.colors.WHITE},
            overlay_color={"hovered": ft.colors.with_opacity(ft.colors.BLUE_100, 0.2)},
        ),
    )

    grid = ft.GridView(
        expand=1,
        runs_count=4,
        max_extent=240,  # acompanha largura do card
        child_aspect_ratio=1.1,
        spacing=16,
        run_spacing=16,
        controls=[]
    )

    # Remover filtro de inativos
    # show_inactive = ft.Checkbox(label="Mostrar inativos", value=False)

    def update_grid():
        filtro = search_field.value.lower() if search_field.value else ""
        categoria = category_field.value
        produtos_db = get_products(False)  # Só ativos
        produtos = []
        for p in produtos_db:
            img_url = p[8]
            print(f"[DEBUG] update_grid: produto {p[0]} image_url do banco = {img_url}")
            if isinstance(img_url, str) and img_url.startswith("static/images/"):
                img_url = img_url.replace("\\", "/")
            produtos.append({
                "id": p[0],
                "name": p[1],
                "price": p[3],
                "code": f"COD: {p[0]:04d}",
                "image_url": img_url,
                "is_active": True,  # Sempre ativo
                "category_id": p[4] if len(p) > 4 else None
            })
        produtos_filtrados = [p for p in produtos if filtro in p["name"].lower() and (not categoria or str(p.get("category_id")) == categoria)]
        total = len(produtos_filtrados)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        state["current_page"] = min(state["current_page"], total_pages)
        start = (state["current_page"] - 1) * PAGE_SIZE
        end = start + PAGE_SIZE
        page_items = produtos_filtrados[start:end]
        grid.controls = [
            ProductCard(
                id=p["id"],
                name=p["name"],
                price=p["price"],
                code=p["code"],
                image_url=p["image_url"],
                is_active=True,  # Sempre ativo
                on_edit=edit_product,
                on_toggle_active=None,  # Remove ativar/desativar
                on_delete=delete_product_action,
                on_details=show_product_details
            ) for p in page_items
        ]
        prev_btn.disabled = state["current_page"] == 1
        next_btn.disabled = state["current_page"] == total_pages
        page_info.value = f"Página {state['current_page']} de {total_pages}"
        page.update()

    def go_prev(e):
        if state["current_page"] > 1:
            state["current_page"] -= 1
            update_grid()

    def go_next(e):
        filtro = search_field.value.lower() if search_field.value else ""
        produtos_db = get_products()
        produtos = []
        for p in produtos_db:
            produtos.append({
                "id": p[0],
                "name": p[1],
                "price": p[3],
                "code": f"COD: {p[0]:04d}",
                "image_url": p[8],
                "is_active": p[9] == 1
            })
        produtos_filtrados = [p for p in produtos if filtro in p["name"].lower()]
        total = len(produtos_filtrados)
        total_pages = max(1, (total + PAGE_SIZE - 1) // PAGE_SIZE)
        if state["current_page"] < total_pages:
            state["current_page"] += 1
            update_grid()

    # Funções para ações do menu
    def edit_product(card):
        from database.models import get_product_by_id
        product = get_product_by_id(card.id)
        if not product:
            return
        # Mapear os campos do produto
        if len(product) == 11:
            (pid, name, description, price, category_id, stock, min_stock, cost_price, image_url, is_active, created_at) = product
        elif len(product) == 10:
            (pid, name, description, price, category_id, stock, min_stock, image_url, is_active, created_at) = product
            cost_price = 0.0
        else:
            pid = name = description = price = category_id = stock = min_stock = cost_price = image_url = is_active = created_at = None
        name_field = ft.TextField(label="Nome do Produto", value=name or '', width=350)
        description_field = ft.TextField(label="Descrição", value=description or '', width=350, multiline=True, min_lines=2, max_lines=3)
        price_field = ft.TextField(label="Preço (MT)", value=str(price or ''), width=200, keyboard_type=ft.KeyboardType.NUMBER)
        stock_field = ft.TextField(label="Estoque", value=str(stock or ''), width=120, keyboard_type=ft.KeyboardType.NUMBER)
        min_stock_field = ft.TextField(label="Estoque Mínimo", value=str(min_stock or ''), width=120, keyboard_type=ft.KeyboardType.NUMBER)
        cost_price_field = ft.TextField(label="Valor de Custo (MT)", value=str(cost_price or ''), width=200, keyboard_type=ft.KeyboardType.NUMBER)
        # Dropdown de categoria
        from database.models import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        category_options = [ft.dropdown.Option(str(cid), cname) for cid, cname in categories]
        category_field = ft.Dropdown(label="Categoria", width=200, options=category_options, value=str(category_id or ''))
        image_field = ft.TextField(label="URL da Imagem (opcional)", value=image_url or '', width=300)
        error_text = ft.Text("", color=ft.colors.RED, size=14)
        file_picker = ft.FilePicker()
        image_path_field = ft.TextField(label="Imagem selecionada", width=300, read_only=True)
        selected_image = {"path": None}

        def on_file_result(e):
            if e.files and len(e.files) > 0:
                image_path_field.value = e.files[0].name
                selected_image["path"] = e.files[0].path
                page.update()

        file_picker.on_result = on_file_result

        def save_edit(ev):
            try:
                name = name_field.value.strip()
                description = description_field.value.strip()
                price = float(price_field.value.replace(",", "."))
                stock = int(stock_field.value)
                min_stock = int(min_stock_field.value)
                cost_price = float(cost_price_field.value.replace(",", "."))
                # Buscar dados antigos
                old_product = get_product_by_id(card.id)
                old_name = old_product[1] if old_product else ""
                old_description = old_product[2] if old_product else ""
                old_price = old_product[3] if old_product else 0
                old_category = old_product[4] if old_product else None
                old_stock = old_product[5] if old_product else 0
                old_min_stock = old_product[6] if old_product else 0
                old_cost_price = old_product[7] if old_product and len(old_product) > 7 else 0
                old_image_url = old_product[8] if old_product and len(old_product) > 8 else None
                if selected_image["path"]:
                    os.makedirs(os.path.join("static", "images"), exist_ok=True)
                    ext = os.path.splitext(selected_image["path"])[1]
                    filename = f"produto_{uuid.uuid4().hex}{ext}"
                    dest_path = os.path.join("static", "images", filename)
                    try:
                        shutil.copy(selected_image["path"], dest_path)
                        image_url = dest_path.replace("\\", "/")
                        print(f"[DEBUG] Imagem salva (edit): {image_url}")
                        print(f"[DEBUG] Arquivo existe? {os.path.exists(dest_path)}")
                    except Exception as ex:
                        error_text.value = f"Erro ao salvar imagem: {ex}"
                        page.update()
                        return
                else:
                    image_url = old_image_url
                print(f"[DEBUG] Caminho da imagem salvo no banco (edit): {image_url}")
                if not name:
                    error_text.value = "Nome obrigatório"
                    page.update()
                    return
                if not category_field.value:
                    error_text.value = "Categoria obrigatória"
                    page.update()
                    return
                update_product(card.id, name, description, price, image_url, int(category_field.value), stock, min_stock, cost_price)
                # Mensagens de edição
                changes = []
                if name != old_name:
                    changes.append("nome")
                if description != old_description:
                    changes.append("descrição")
                if price != old_price:
                    changes.append("preço")
                if int(category_field.value) != old_category:
                    changes.append("categoria")
                if cost_price != old_cost_price:
                    changes.append("custo")
                if image_url != old_image_url:
                    changes.append("imagem")
                msg = ""
                if changes:
                    msg += f"Produto editado: {', '.join(changes)} alterado(s). "
                if stock > old_stock:
                    diff = stock - old_stock
                    add_stock_entry(product_id=card.id, quantity=diff, unit_cost=cost_price, supplier=None, notes=f"Entrada ao editar produto: +{diff}")
                    msg += f"Entrada de estoque registrada: +{diff} unidade(s)."
                elif stock < old_stock:
                    diff = old_stock - stock
                    msg += f"Estoque reduzido: -{diff} unidade(s)."
                if not changes and stock == old_stock:
                    msg = "Nenhuma alteração relevante."
                dialog.open = False
                update_grid()
                if msg:
                    page.snack_bar = ft.SnackBar(ft.Text(msg), bgcolor=ft.colors.GREEN)
                    page.snack_bar.open = True
                page.update()
                print(f"[DEBUG] Caminho da imagem salvo no banco (edit): {image_url}")
            except Exception as ex:
                error_text.value = f"Erro: {ex}"
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text(f"Editar Produto: {name}"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    name_field,
                    description_field,
                    ft.Row([
                        price_field,
                        cost_price_field
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Row([
                        stock_field,
                        min_stock_field
                    ], alignment=ft.MainAxisAlignment.START),
                    category_field,
                    ft.ElevatedButton("Selecionar Imagem", icon=ft.icons.IMAGE, on_click=lambda e: file_picker.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png"])),
                    image_path_field,
                    image_field,
                    error_text,
                    file_picker
                ], spacing=12, width=500)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Salvar", on_click=save_edit)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def toggle_active(card):
        set_product_active(card.id, not card.is_active)
        update_grid()

    def delete_product_action(card):
        def confirm_delete(ev):
            delete_product(card.id)
            dialog.open = False
            update_grid()
        dialog = ft.AlertDialog(
            title=ft.Text("Excluir Produto"),
            content=ft.Text(f"Tem certeza que deseja excluir o produto '{card.name}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Excluir", on_click=confirm_delete)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def show_product_details(product_id):
        from database.models import get_product_by_id
        product = get_product_by_id(product_id)
        if not product:
            return
        # Mapear os campos do produto, lidando com produtos antigos (sem cost_price)
        if len(product) == 11:
            (pid, name, description, price, category_id, stock, min_stock, cost_price, image_url, is_active, created_at) = product
        elif len(product) == 10:
            (pid, name, description, price, category_id, stock, min_stock, image_url, is_active, created_at) = product
            cost_price = 0.0
        else:
            pid = name = description = price = category_id = stock = min_stock = cost_price = image_url = is_active = created_at = None
        dialog = ft.AlertDialog(
            title=ft.Text(f"Detalhes do Produto: {name}"),
            content=ft.Column([
                ft.Text(f"Código: {pid}"),
                ft.Text(f"Nome: {name}"),
                ft.Text(f"Descrição: {description or '-'}"),
                ft.Text(f"Preço de Venda: {price:.2f} MT"),
                ft.Text(f"Valor de Custo: {cost_price:.2f} MT"),
                ft.Text(f"Estoque Atual: {stock}"),
                ft.Text(f"Estoque Mínimo: {min_stock}"),
                ft.Text(f"Criado em: {created_at}"),
            ], spacing=8),
            actions=[
                ft.TextButton("Fechar", on_click=lambda e: (setattr(dialog, 'open', False), page.update()))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    prev_btn = ft.IconButton(icon=ft.icons.ARROW_BACK, on_click=go_prev)
    next_btn = ft.IconButton(icon=ft.icons.ARROW_FORWARD, on_click=go_next)
    page_info = ft.Text("")

    # Botão para adicionar produto
    def show_add_product_dialog(e=None):
        # Buscar categorias sempre que abrir o modal, sem duplicar
        from database.models import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories WHERE is_active = 1 ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        category_options = [ft.dropdown.Option(str(cid), cname) for cid, cname in categories]
        # Criar campo categoria com opções limpas
        category_field = ft.Dropdown(label="Categoria", width=300, options=category_options, value=None)
        name_field = ft.TextField(label="Nome do Produto", width=350)
        description_field = ft.TextField(label="Descrição", width=350, multiline=True, min_lines=2, max_lines=3)
        price_field = ft.TextField(label="Preço (MT)", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="")
        stock_field = ft.TextField(label="Estoque", width=120, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        min_stock_field = ft.TextField(label="Estoque Mínimo", width=120, keyboard_type=ft.KeyboardType.NUMBER, value="0")
        cost_price_field = ft.TextField(label="Valor de Custo (MT)", width=200, keyboard_type=ft.KeyboardType.NUMBER, value="0.00")
        image_path_field = ft.TextField(label="Imagem selecionada", width=350, read_only=True)
        error_text = ft.Text("", color=ft.colors.RED, size=14)
        file_picker = ft.FilePicker()
        selected_image = {"path": None}

        def on_file_result(e):
            if e.files and len(e.files) > 0:
                image_path_field.value = e.files[0].name
                selected_image["path"] = e.files[0].path
                page.update()

        file_picker.on_result = on_file_result

        def save_product(ev):
            try:
                name = name_field.value.strip()
                description = description_field.value.strip()
                if not price_field.value.strip():
                    error_text.value = "Preço obrigatório"
                    page.update()
                    return
                if not category_field.value:
                    error_text.value = "Categoria obrigatória"
                    page.update()
                    return
                price = float(price_field.value.replace(",", "."))
                stock = int(stock_field.value)
                min_stock = int(min_stock_field.value)
                cost_price = float(cost_price_field.value.replace(",", "."))
                is_active = 1  # Sempre ativo
                image_url = None
                if selected_image["path"]:
                    os.makedirs(os.path.join("static", "images"), exist_ok=True)
                    ext = os.path.splitext(selected_image["path"])[1]
                    filename = f"produto_{uuid.uuid4().hex}{ext}"
                    dest_path = os.path.join("static", "images", filename)
                    try:
                        shutil.copy(selected_image["path"], dest_path)
                        image_url = dest_path.replace("\\", "/")
                        print(f"[DEBUG] Imagem salva: {image_url}")
                        print(f"[DEBUG] Arquivo existe? {os.path.exists(dest_path)}")
                    except Exception as ex:
                        error_text.value = f"Erro ao salvar imagem: {ex}"
                        page.update()
                        return
                print(f"[DEBUG] Caminho da imagem salvo no banco: {image_url}")
                from database.models import create_product
                create_product(
                    name=name,
                    description=description,
                    price=price,
                    stock=stock,
                    min_stock=min_stock,
                    image_url=image_url,
                    cost_price=cost_price,
                    is_active=is_active,
                    category_id=int(category_field.value)
                )
                if stock > 0:
                    add_stock_entry(product_id=get_products()[-1][0], quantity=stock, unit_cost=cost_price, supplier=None, notes="Entrada inicial ao cadastrar produto", update_product_stock=False)
                dialog.open = False
                update_grid()
                page.snack_bar = ft.SnackBar(ft.Text("Produto cadastrado com sucesso!"), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                error_text.value = f"Erro: {ex}"
                page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Adicionar Produto"),
            content=ft.Container(
                width=500,
                content=ft.Column([
                    name_field,
                    description_field,
                    ft.Row([
                        price_field,
                        cost_price_field
                    ], alignment=ft.MainAxisAlignment.START),
                    ft.Row([
                        stock_field,
                        min_stock_field
                    ], alignment=ft.MainAxisAlignment.START),
                    category_field,
                    ft.ElevatedButton("Selecionar Imagem", icon=ft.icons.IMAGE, on_click=lambda e: file_picker.pick_files(allow_multiple=False, allowed_extensions=["jpg", "jpeg", "png"])),
                    image_path_field,
                    error_text,
                    file_picker
                ], spacing=12)
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Salvar", on_click=save_product)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    add_button = ft.ElevatedButton(
        "Adicionar Produto",
        icon=ft.icons.ADD,
        on_click=show_add_product_dialog,
        bgcolor=ft.colors.BLUE_700,
        color=ft.colors.WHITE,
        tooltip="Cadastrar novo produto"
    )

    # Corrigir entradas retroativas e image_url inválido automaticamente ao abrir a página de produtos
    register_missing_stock_entries()
    fix_invalid_image_urls()
    update_grid()

    return ft.Column([
        product_header(on_back=go_back),
        ft.Container(
            content=ft.Row([
                add_button,
                # fix_entries_button # Removido botão de correção retroativa
            ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            padding=ft.padding.symmetric(horizontal=24, vertical=16),
            bgcolor=None,
        ),
        ft.Container(
            content=grid,
            expand=True,
            padding=ft.padding.symmetric(horizontal=24, vertical=8),
        ),
        ft.Row([
            prev_btn,
            page_info,
            next_btn,
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
    ], expand=True, spacing=0)

ProductView = view
