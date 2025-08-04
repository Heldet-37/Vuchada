import flet as ft
import sqlite3
from datetime import datetime

class ProductView(ft.UserControl):
    def __init__(self, page: ft.Page, on_back=None):
        super().__init__()
        self.page = page
        self.on_back = on_back
        self.products = []
        self.categories = []
        self.current_product = None
        self.is_editing = False

    def build(self):
        self.load_categories()
        self.load_products()
        
        return ft.Container(
            content=ft.Column([
                # Header
                ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.icons.ARROW_BACK,
                            on_click=self.on_back
                        ),
                        ft.Text("Gerenciar Produtos", size=20, weight=ft.FontWeight.BOLD),
                        ft.IconButton(
                            icon=ft.icons.ADD,
                            on_click=self.show_add_product_dialog
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=10,
                    bgcolor=ft.colors.BLUE_50
                ),
                
                # Products List
                ft.Container(
                    content=ft.Column([
                        ft.Text("Produtos", size=16, weight=ft.FontWeight.BOLD),
                        self.products_list
                    ]),
                    padding=10
                )
            ]),
            expand=True
        )

    def load_categories(self):
        try:
            conn = sqlite3.connect('restaurant.db')
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories ORDER BY name")
            self.categories = cursor.fetchall()
            conn.close()
        except Exception as e:
            print(f"Erro ao carregar categorias: {e}")

    def load_products(self):
        try:
            conn = sqlite3.connect('restaurant.db')
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.name, p.price, p.description, p.image_url, p.stock, c.name as category_name
                FROM products p
                LEFT JOIN categories c ON p.category_id = c.id
                ORDER BY p.name
            """)
            self.products = cursor.fetchall()
            conn.close()
            self.update_products_list()
        except Exception as e:
            print(f"Erro ao carregar produtos: {e}")

    def update_products_list(self):
        self.products_list.controls = []
        
        for product in self.products:
            product_card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.ListTile(
                            leading=ft.Icon(ft.icons.RESTAURANT),
                            title=ft.Text(product[1], weight=ft.FontWeight.BOLD),
                            subtitle=ft.Text(f"R$ {product[2]:.2f} - {product[6] or 'Sem categoria'}"),
                        ),
                        ft.Row([
                            ft.TextButton("Editar", on_click=lambda e, p=product: self.edit_product(p)),
                            ft.TextButton("Excluir", on_click=lambda e, p=product: self.delete_product(p)),
                        ], alignment=ft.MainAxisAlignment.END)
                    ]),
                    padding=10
                )
            )
            self.products_list.controls.append(product_card)
        
        self.products_list.update()

    def show_add_product_dialog(self, e):
        self.current_product = None
        self.is_editing = False
        self.show_product_dialog()

    def edit_product(self, product):
        self.current_product = product
        self.is_editing = True
        self.show_product_dialog()

    def show_product_dialog(self):
        # Create form fields
        name_field = ft.TextField(
            label="Nome do Produto",
            value=self.current_product[1] if self.current_product else "",
            width=300
        )
        
        price_field = ft.TextField(
            label="Preço",
            value=str(self.current_product[2]) if self.current_product else "",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        description_field = ft.TextField(
            label="Descrição",
            value=self.current_product[3] if self.current_product else "",
            width=300,
            multiline=True,
            min_lines=3,
            max_lines=5
        )
        
        stock_field = ft.TextField(
            label="Estoque",
            value=str(self.current_product[5]) if self.current_product else "0",
            width=300,
            keyboard_type=ft.KeyboardType.NUMBER
        )
        
        category_dropdown = ft.Dropdown(
            label="Categoria",
            width=300,
            options=[ft.dropdown.Option(key=str(cat[0]), text=cat[1]) for cat in self.categories]
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
                
                conn = sqlite3.connect('restaurant.db')
                cursor = conn.cursor()
                
                if self.is_editing:
                    cursor.execute("""
                        UPDATE products 
                        SET name=?, price=?, description=?, stock=?, category_id=?, updated_at=?
                        WHERE id=?
                    """, (name, price, description, stock, category_id, datetime.now(), self.current_product[0]))
                else:
                    cursor.execute("""
                        INSERT INTO products (name, price, description, stock, category_id, created_at, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (name, price, description, stock, category_id, datetime.now(), datetime.now()))
                
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
                category_dropdown
            ], spacing=10),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.TextButton("Salvar", on_click=save_product)
            ]
        )
        
        self.page.dialog.open = True
        self.page.update()

    def delete_product(self, product):
        def confirm_delete(e):
            try:
                conn = sqlite3.connect('restaurant.db')
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
            content=ft.Text(f"Deseja realmente excluir o produto '{product[1]}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=cancel),
                ft.TextButton("Excluir", on_click=confirm_delete)
            ]
        )
        
        self.page.dialog.open = True
        self.page.update()

    @property
    def products_list(self):
        if not hasattr(self, '_products_list'):
            self._products_list = ft.Column(spacing=10)
        return self._products_list 