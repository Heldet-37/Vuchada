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

    def build(self):
        self.load_categories()
        self.load_products()
        
        return ft.Container(
            content=ft.Column([
                # Header Padrão
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            icon_color=ft.colors.WHITE,
                            on_click=self.on_back
                        ),
                        ft.Text("Gerenciar Produtos", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                        ft.IconButton(
                            icon=ft.icons.ADD,
                            icon_color=ft.colors.WHITE,
                            on_click=self.show_add_product_dialog
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor=ft.colors.BLUE_700
                ),
                
                # Products Grid
                ft.Container(
                    content=ft.Column([
                        ft.Text("Lista de Produtos", size=16, weight=ft.FontWeight.BOLD),
                        self.products_grid
                    ]),
                    padding=10,
                    expand=True
                )
            ]),
            expand=True
        )

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
                SELECT p.id, p.name, p.price, p.description, p.image_url, p.stock, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            """)
            self.products = cursor.fetchall()
            conn.close()
            self.update_products_grid()
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")

    def update_products_grid(self):
        self.products_grid.controls = []
        
        for product in self.products:
            # Criar card do produto com imagem
            product_card = ft.Card(
                elevation=8,
                content=ft.Container(
                    content=ft.Column([
                        # Imagem do produto
                        ft.Container(
                            content=ft.Image(
                                src=product[4] if product[4] else "https://via.placeholder.com/200x150/FF8C00/FFFFFF?text=Sem+Imagem",
                                width=200,
                                height=150,
                                fit=ft.ImageFit.COVER,
                                border_radius=10
                            ),
                            margin=ft.margin.only(bottom=10)
                        ),
                        
                        # Informações do produto
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    product[1], 
                                    size=18, 
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLUE_700
                                ),
                                ft.Text(
                                    f"💰 {product[2]:.2f} MT",
                                    size=16,
                                    weight=ft.FontWeight.W_500,
                                    color=ft.colors.GREEN_700
                                ),
                                ft.Text(
                                    f"📦 Estoque: {product[5]}",
                                    size=14,
                                    color=ft.colors.GREY_700
                                ),
                                ft.Text(
                                    f"🏷️ {product[6] or 'Sem categoria'}",
                                    size=14,
                                    color=ft.colors.GREY_600
                                ),
                                ft.Text(
                                    product[3] or "Sem descrição",
                                    size=12,
                                    color=ft.colors.GREY_600,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                )
                            ], spacing=5),
                            padding=10
                        ),
                        
                        # Botões de ação
                        ft.Container(
                            content=ft.Row([
                                ft.ElevatedButton(
                                    "✏️ Editar",
                                    icon=ft.icons.EDIT,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.colors.BLUE_500,
                                        color=ft.colors.WHITE
                                    ),
                                    on_click=lambda e, p=product: self.edit_product(p)
                                ),
                                ft.ElevatedButton(
                                    "🗑️ Excluir",
                                    icon=ft.icons.DELETE,
                                    style=ft.ButtonStyle(
                                        bgcolor=ft.colors.RED_500,
                                        color=ft.colors.WHITE
                                    ),
                                    on_click=lambda e, p=product: self.delete_product(p)
                                )
                            ], alignment=ft.MainAxisAlignment.SPACE_EVENLY),
                            padding=ft.padding.only(bottom=10)
                        )
                    ]),
                    width=250,
                    padding=10,
                    border_radius=15
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
        
        description_field = ft.TextField(
            label="Descrição",
            value=self.current_product[3] if self.current_product else "",
            width=400,
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        stock_field = ft.TextField(
            label="Estoque",
            value=str(self.current_product[5]) if self.current_product else "0",
            width=400,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        category_dropdown = ft.Dropdown(
            label="Categoria",
            width=400,
            options=[ft.dropdown.Option(key=str(cat[0]), text=cat[1]) for cat in self.categories]
        )
        
        # Campo de imagem
        image_preview = ft.Container(
            content=ft.Image(
                src=self.selected_image_path if self.selected_image_path else "https://via.placeholder.com/200x150/FF8C00/FFFFFF?text=Selecione+uma+imagem",
                width=200,
                height=150,
                fit=ft.ImageFit.COVER,
                border_radius=10
            ),
            margin=ft.margin.only(bottom=10)
        )
        
        def pick_image(e):
            if not self.file_picker:
                self.file_picker = ft.FilePicker(on_result=self.on_image_picked)
                self.page.overlay.append(self.file_picker)
                self.page.update()
            
            self.file_picker.pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "gif"],
                allow_multiple=False
            )
        
        def on_image_picked(e: ft.FilePickerResultEvent):
            if e.files:
                file_path = e.files[0].path
                self.selected_image_path = file_path
                image_preview.content.src = file_path
                image_preview.update()
        
        image_button = ft.ElevatedButton(
            "Selecionar Imagem",
            icon=ft.icons.IMAGE,
            on_click=pick_image
        )
        
        if self.current_product:
            # Set current category
            for option in category_dropdown.options:
                if option.text == self.current_product[6]:
                    category_dropdown.value = option.key
                    break

        def save_product(e):
            try:
                name = name_field.value
                price = float(price_field.value or 0)
                description = description_field.value
                stock = int(stock_field.value or 0)
                category_id = int(category_dropdown.value) if category_dropdown.value else None
                
                if not name:
                    self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Nome é obrigatório!")))
                    return
                
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                
                # Salvar imagem se foi selecionada
                image_url = self.selected_image_path if self.selected_image_path else (self.current_product[4] if self.current_product else None)
                
                if self.is_editing:
                    cursor.execute("""
                        UPDATE products 
                        SET name=?, price=?, description=?, stock=?, category_id=?, image_url=?, updated_at=?
                        WHERE id=?
                    """, (name, price, description, stock, category_id, image_url, datetime.now(), self.current_product[0]))
                else:
                    cursor.execute("""
                        INSERT INTO products (name, price, description, stock, category_id, image_url, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (name, price, description, stock, category_id, image_url, datetime.now(), datetime.now()))
                
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.update()
                
                self.load_products()
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Produto salvo com sucesso!")))
                
            except Exception as e:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro ao salvar: {e}")))

        def cancel(e):
            self.page.dialog.open = False
            self.page.update()

        # Create dialog
        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Editar Produto" if self.is_editing else "Adicionar Produto"),
            content=ft.Column([
                name_field,
                price_field,
                description_field,
                stock_field,
                category_dropdown,
                ft.Divider(),
                ft.Text("Imagem do Produto", size=16, weight=ft.FontWeight.BOLD),
                image_preview,
                image_button
            ], spacing=15, scroll=ft.ScrollMode.AUTO),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.ElevatedButton("Salvar", on_click=save_product)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog.open = True
        self.page.update()

    def delete_product(self, product):
        def confirm_delete(e):
            try:
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                cursor.execute("DELETE FROM products WHERE id=?", (product[0],))
                conn.commit()
                conn.close()
                
                self.page.dialog.open = False
                self.page.update()
                
                self.load_products()
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text("Produto excluído com sucesso!")))
                
            except Exception as e:
                self.page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Erro ao excluir: {e}")))

        def cancel(e):
            self.page.dialog.open = False
            self.page.update()

        self.page.dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Tem certeza que deseja excluir o produto '{product[1]}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.ElevatedButton("Excluir", on_click=confirm_delete)
            ],
            actions_alignment=ft.MainAxisAlignment.END
        )
        
        self.page.dialog.open = True
        self.page.update()

    @property
    def products_grid(self):
        if not hasattr(self, '_products_grid'):
            self._products_grid = ft.GridView(
                expand=1,
                runs_count=5,
                max_extent=280,
                spacing=20,
                run_spacing=20,
                child_aspect_ratio=0.8
            )
        return self._products_grid 