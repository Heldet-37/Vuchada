import flet as ft
import sqlite3
from datetime import datetime
import os
from pathlib import Path

class ProductView(ft.UserControl):
    def __init__(self, page: ft.Page, on_back=None):
        super().__init__()
        self.page = page
        self.on_back = on_back
        self.products = []
        self.categories = []
        self.current_product = None
        self.is_editing = False
        self.selected_image_path = None
        self.file_picker = None
        self.search_query = ""
        self.selected_category = None

    def build(self):
        self.load_categories()
        self.load_products()
        
        # Header seguindo o padrão das outras páginas
        header = ft.Container(
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        icon_color=ft.colors.WHITE,
                        tooltip="Voltar",
                        on_click=self.on_back
                    ),
                    ft.Icon(
                        name=ft.icons.INVENTORY,
                        size=50,
                        color=ft.colors.WHITE
                    ),
                    ft.Text(
                        "Gerenciar Produtos",
                        size=30,
                        weight=ft.FontWeight.BOLD,
                        color=ft.colors.WHITE
                    ),
                    ft.Container(expand=True),
                    ft.ElevatedButton(
                        "➕ Novo Produto",
                        icon=ft.icons.ADD,
                        on_click=self.show_add_product_dialog,
                        bgcolor=ft.colors.GREEN_700,
                        color=ft.colors.WHITE,
                        style=ft.ButtonStyle(
                            padding=ft.padding.symmetric(horizontal=20, vertical=10)
                        )
                    )
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

        # Controles de filtro e busca
        controls_row = ft.Container(
            content=ft.Row([
                # Campo de busca
                ft.Container(
                    content=ft.TextField(
                        label="🔍 Buscar produtos...",
                        prefix_icon=ft.icons.SEARCH,
                        on_change=self.on_search_change,
                        width=300,
                        border_color=ft.colors.BLUE_200,
                        focused_border_color=ft.colors.BLUE_500
                    ),
                    padding=ft.padding.only(right=20)
                ),
                
                # Filtro de categoria
                ft.Container(
                    content=ft.Dropdown(
                        label="🏷️ Categoria",
                        width=200,
                        border_color=ft.colors.BLUE_200,
                        focused_border_color=ft.colors.BLUE_500,
                        on_change=self.on_category_change,
                        options=[
                            ft.dropdown.Option(key="todos", text="Todas as categorias")
                        ] + [
                            ft.dropdown.Option(key=str(cat[0]), text=cat[1])
                            for cat in self.categories
                        ]
                    ),
                    padding=ft.padding.only(right=20)
                ),
                
                # Botão de refresh
                ft.ElevatedButton(
                    "🔄 Atualizar",
                    icon=ft.icons.REFRESH,
                    on_click=self.refresh_products,
                    bgcolor=ft.colors.ORANGE_600,
                    color=ft.colors.WHITE
                ),
                
                ft.Container(expand=True),
                
                # Estatísticas
                ft.Container(
                    content=ft.Row([
                        ft.Icon(ft.icons.INVENTORY_2, color=ft.colors.BLUE_600),
                        ft.Text(
                            f"Total: {len(self.products)} produtos",
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.BLUE_600
                        )
                    ], spacing=8),
                    padding=ft.padding.only(left=20)
                )
            ], alignment=ft.MainAxisAlignment.START),
            padding=ft.padding.only(top=20, left=40, right=40, bottom=20),
            bgcolor=ft.colors.WHITE,
            border_radius=10,
            margin=ft.margin.only(left=40, right=40, top=20)
        )

        # Grid de produtos com scroll
        products_container = ft.Container(
            content=ft.Column([
                ft.Text(
                    "📦 Lista de Produtos",
                    size=24,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.BLUE_900
                ),
                ft.Container(height=20),
                self.products_grid
            ]),
            padding=ft.padding.only(left=40, right=40, bottom=40),
            expand=True
        )

        return ft.Column([
            header,
            controls_row,
            products_container
        ], expand=True, scroll=ft.ScrollMode.AUTO)

    def on_search_change(self, e):
        self.search_query = e.control.value.lower()
        self.filter_products()

    def on_category_change(self, e):
        self.selected_category = e.control.value if e.control.value != "todos" else None
        self.filter_products()

    def filter_products(self):
        filtered_products = []
        
        for product in self.products:
            # Filtro por busca
            if self.search_query and self.search_query not in product[1].lower():
                continue
                
            # Filtro por categoria
            if self.selected_category:
                product_category_id = str(product[7]) if len(product) > 7 and product[7] else None
                if product_category_id != self.selected_category:
                    continue
            
            filtered_products.append(product)
        
        self.update_products_grid(filtered_products)

    def refresh_products(self, e=None):
        self.load_products()
        self.page.show_snack_bar(ft.SnackBar(
            content=ft.Text("🔄 Produtos atualizados!"),
            bgcolor=ft.colors.GREEN_400,
            duration=2000
        ))

    def load_categories(self):
        try:
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            self.categories = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def load_products(self):
        try:
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.price, p.description, p.image_url, p.stock, 
                       c.name as category_name, p.category_id, p.is_active
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            """)
            self.products = cursor.fetchall()
            conn.close()
            self.update_products_grid()
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")

    def update_products_grid(self, products_to_show=None):
        if products_to_show is None:
            products_to_show = self.products
            
        self.products_grid.controls = []
        
        for product in products_to_show:
            # Status do produto
            is_active = product[8] if len(product) > 8 else True
            status_color = ft.colors.GREEN_600 if is_active else ft.colors.RED_600
            status_text = "✅ Ativo" if is_active else "❌ Inativo"
            
            # Criar card do produto melhorado
            product_card = ft.Card(
                elevation=12,
                content=ft.Container(
                    content=ft.Column([
                        # Header do card com status
                        ft.Container(
                            content=ft.Row([
                                ft.Container(expand=True),
                                ft.Container(
                                    content=ft.Text(
                                        status_text,
                                        size=12,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.WHITE
                                    ),
                                    bgcolor=status_color,
                                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                    border_radius=10
                                )
                            ]),
                            padding=ft.padding.only(bottom=10)
                        ),
                        
                        # Imagem do produto
                        ft.Container(
                            content=ft.Image(
                                src=product[4] if product[4] else "https://via.placeholder.com/250x180/FF8C00/FFFFFF?text=Sem+Imagem",
                                width=250,
                                height=180,
                                fit=ft.ImageFit.COVER,
                                border_radius=15
                            ),
                            margin=ft.margin.only(bottom=15)
                        ),
                        
                        # Informações do produto
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    product[1], 
                                    size=20, 
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_900,
                                    text_align=ft.TextAlign.CENTER
                                ),
                                ft.Container(height=8),
                                ft.Container(
                                    content=ft.Text(
                                        f"💰 {product[2]:.2f} MT",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREEN_700,
                                        text_align=ft.TextAlign.CENTER
                                    ),
                                    bgcolor=ft.colors.GREEN_50,
                                    padding=ft.padding.symmetric(horizontal=12, vertical=6),
                                    border_radius=8
                                ),
                                ft.Container(height=8),
                                ft.Row([
                                    ft.Icon(ft.icons.INVENTORY, color=ft.colors.BLUE_600, size=16),
                                    ft.Text(
                                        f"Estoque: {product[5]}",
                                        size=14,
                                        weight=ft.FontWeight.W_500,
                                        color=ft.colors.BLUE_600
                                    )
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Container(height=4),
                                ft.Row([
                                    ft.Icon(ft.icons.CATEGORY, color=ft.colors.ORANGE_600, size=16),
                                    ft.Text(
                                        f"{product[6] or 'Sem categoria'}",
                                        size=14,
                                        color=ft.colors.ORANGE_600
                                    )
                                ], alignment=ft.MainAxisAlignment.CENTER),
                                ft.Container(height=8),
                                ft.Container(
                                    content=ft.Text(
                                        product[3] or "Sem descrição",
                                        size=12,
                                        color=ft.colors.GREY_600,
                                        max_lines=3,
                                        overflow=ft.TextOverflow.ELLIPSIS,
                                        text_align=ft.TextAlign.CENTER
                                    ),
                                    bgcolor=ft.colors.GREY_50,
                                    padding=ft.padding.all(8),
                                    border_radius=8
                                )
                            ], spacing=5),
                            padding=ft.padding.only(bottom=15)
                        ),
                        
                        # Botões de ação
                        ft.Container(
                            content=ft.Row([
                                ft.ElevatedButton(
                                    "✏️ Editar",
                                    icon=ft.icons.EDIT,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.colors.BLUE_600,
                                        color=ft.colors.WHITE,
                                        padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                    ),
                                    on_click=lambda e, p=product: self.edit_product(p)
                                ),
                                ft.ElevatedButton(
                                    "🗑️ Excluir",
                                    icon=ft.icons.DELETE,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.colors.RED_600,
                                        color=ft.colors.WHITE,
                                        padding=ft.padding.symmetric(horizontal=16, vertical=8)
                                    ),
                                    on_click=lambda e, p=product: self.delete_product(p)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                            padding=ft.padding.only(bottom=15)
                        )
                    ]),
                    width=280,
                    padding=20,
                    border_radius=20
                )
            )
            self.products_grid.controls.append(product_card)
        
        self.products_grid.update()

    def show_add_product_dialog(self, e):
        self.current_product = None
        self.is_editing = False
        self.selected_image_path = None
        self.show_product_dialog()

    def edit_product(self, product):
        self.current_product = product
        self.is_editing = True
        self.selected_image_path = product[4] if product[4] else None
        self.show_product_dialog()

    def show_product_dialog(self):
        # Create form fields
        name_field = ft.TextField(
            label="Nome do Produto",
            value=self.current_product[1] if self.current_product else "",
            width=400
        )
        
        price_field = ft.TextField(
            label="Preço (MT)",
            value=str(self.current_product[2]) if self.current_product else "",
            width=400,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        stock_field = ft.TextField(
            label="Estoque",
            value=str(self.current_product[5]) if self.current_product else "0",
            width=400,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        description_field = ft.TextField(
            label="Descrição",
            value=self.current_product[3] if self.current_product else "",
            width=400,
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        # Dropdown de categorias
        category_dropdown = ft.Dropdown(
            label="Categoria",
            width=400,
            options=[
                ft.dropdown.Option(key="", text="Sem categoria")
            ] + [
                ft.dropdown.Option(key=str(cat[0]), text=cat[1])
                for cat in self.categories
            ]
        )
        
        if self.current_product and self.current_product[7]:
            category_dropdown.value = str(self.current_product[7])
        
        # Preview da imagem
        image_preview = ft.Container(
            content=ft.Image(
                src=self.selected_image_path if self.selected_image_path else "https://via.placeholder.com/200x150/FF8C00/FFFFFF?text=Sem+Imagem",
                width=200,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=10
            ),
            margin=ft.margin.only(bottom=10)
        )
        
        # File picker para imagem
        if not self.file_picker:
            self.file_picker = ft.FilePicker(
                on_result=self.on_image_picked
            )
            self.page.overlay.append(self.file_picker)
            self.page.update()
        
        def pick_image(e):
            self.file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "gif"],
                allow_multiple=False
            )
        
        def on_image_picked(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                # Copiar arquivo para pasta static
                static_dir = Path("static/products")
                static_dir.mkdir(exist_ok=True)
                
                import shutil
                file_name = f"product_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{e.files[0].name}"
                dest_path = static_dir / file_name
                shutil.copy2(file_path, dest_path)
                
                self.selected_image_path = f"/static/products/{file_name}"
                image_preview.content.src = self.selected_image_path
                image_preview.update()
        
        def save_product(e):
            try:
                name = name_field.value.strip()
                price = float(price_field.value) if price_field.value else 0.0
                stock = int(stock_field.value) if stock_field.value else 0
                description = description_field.value.strip()
                category_id = int(category_dropdown.value) if category_dropdown.value else None
                
                if not name:
                    self.page.show_snack_bar(ft.SnackBar(
                        content=ft.Text("❌ Nome do produto é obrigatório!"),
                        bgcolor=ft.colors.RED_400
                    ))
                    return
                
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                
                if self.is_editing:
                    cursor.execute("""
                        UPDATE products 
                        SET name=?, price=?, stock=?, description=?, image_url=?, category_id=?
                        WHERE id=?
                    """, (name, price, stock, description, self.selected_image_path, category_id, self.current_product[0]))
                else:
                    cursor.execute("""
                        INSERT INTO products (name, price, stock, description, image_url, category_id, is_active)
                        VALUES (?, ?, ?, ?, ?, ?, 1)
                    """, (name, price, stock, description, self.selected_image_path, category_id))
                
                conn.commit()
                conn.close()
                
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"✅ Produto {'atualizado' if self.is_editing else 'criado'} com sucesso!"),
                    bgcolor=ft.colors.GREEN_400
                ))
                
                self.load_products()
                self.page.dialog.open = False
                self.page.update()
                
            except Exception as e:
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"❌ Erro: {str(e)}"),
                    bgcolor=ft.colors.RED_400
                ))
        
        def cancel(e):
            self.page.dialog.open = False
            self.page.update()
        
        # Dialog content
        dialog_content = ft.Column([
            ft.Text(
                f"{'✏️ Editar' if self.is_editing else '➕ Novo'} Produto",
                size=24,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.BLUE_900
            ),
            ft.Container(height=20),
            name_field,
            ft.Container(height=10),
            price_field,
            ft.Container(height=10),
            stock_field,
            ft.Container(height=10),
            description_field,
            ft.Container(height=10),
            category_dropdown,
            ft.Container(height=20),
            ft.Text("Imagem do Produto", weight=ft.FontWeight.BOLD),
            ft.Container(height=10),
            image_preview,
            ft.ElevatedButton(
                "📁 Escolher Imagem",
                icon=ft.icons.UPLOAD_FILE,
                on_click=pick_image,
                bgcolor=ft.colors.BLUE_600,
                color=ft.colors.WHITE
            ),
            ft.Container(height=20),
            ft.Row([
                ft.ElevatedButton(
                    "❌ Cancelar",
                    on_click=cancel,
                    bgcolor=ft.colors.RED_600,
                    color=ft.colors.WHITE
                ),
                ft.ElevatedButton(
                    "💾 Salvar",
                    on_click=save_product,
                    bgcolor=ft.colors.GREEN_600,
                    color=ft.colors.WHITE
                )
            ], alignment=ft.MainAxisAlignment.END)
        ], scroll=ft.ScrollMode.AUTO, width=500)
        
        self.page.dialog = ft.AlertDialog(
            content=dialog_content,
            open=True
        )
        self.page.update()

    def delete_product(self, product):
        def confirm_delete(e):
            try:
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id=?", (product[0],))
                conn.commit()
                conn.close()
                
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("✅ Produto excluído com sucesso!"),
                    bgcolor=ft.colors.GREEN_400
                ))
                
                self.load_products()
                self.page.dialog.open = False
                self.page.update()
                
            except Exception as e:
                self.page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"❌ Erro ao excluir: {str(e)}"),
                    bgcolor=ft.colors.RED_400
                ))
        
        def cancel(e):
            self.page.dialog.open = False
            self.page.update()
        
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("🗑️ Confirmar Exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o produto '{product[1]}'?"),
            actions=[
                ft.TextButton("❌ Cancelar", on_click=cancel),
                ft.TextButton("✅ Confirmar", on_click=confirm_delete)
            ]
        )
        self.page.dialog.open = True
        self.page.update()

    @property
    def products_grid(self):
        if not hasattr(self, '_products_grid'):
            self._products_grid = ft.GridView(
                expand=True,
                runs_count=5,
                max_extent=300,
                child_aspect_ratio=0.8,
                spacing=20,
                run_spacing=20,
            )
        return self._products_grid 