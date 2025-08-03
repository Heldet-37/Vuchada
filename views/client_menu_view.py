import flet as ft
import sqlite3
from datetime import datetime


def format_metical(value):
    return f"{value:,.2f} MT"


def ClientMenuView(page: ft.Page, on_back=None):
    # Variáveis de estado
    selected_category = None
    search_query = ""
    
    # Containers principais
    header_container = ft.Container()
    categories_container = ft.Container()
    products_container = ft.Container()
    search_container = ft.Container()
    
    def load_categories():
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id, name FROM categories WHERE active = 1 ORDER BY name')
        categories = cursor.fetchall()
        conn.close()
        
        category_buttons = []
        for cat_id, cat_name in categories:
            btn = ft.ElevatedButton(
                text=cat_name,
                style=ft.ButtonStyle(
                    color=ft.colors.WHITE,
                    bgcolor=ft.colors.BLUE_600 if selected_category == cat_id else ft.colors.GREY_400,
                ),
                on_click=lambda e, cid=cat_id: select_category(cid)
            )
            category_buttons.append(btn)
        
        # Botão "Todos"
        all_btn = ft.ElevatedButton(
            text="Todos",
            style=ft.ButtonStyle(
                color=ft.colors.WHITE,
                bgcolor=ft.colors.BLUE_600 if selected_category is None else ft.colors.GREY_400,
            ),
            on_click=lambda e: select_category(None)
        )
        category_buttons.insert(0, all_btn)
        
        categories_container.content = ft.Row(
            controls=category_buttons,
            scroll=ft.ScrollMode.HORIZONTAL,
            spacing=10
        )
        page.update()
    
    def select_category(category_id):
        nonlocal selected_category
        selected_category = category_id
        load_categories()
        load_products()
    
    def load_products():
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        if selected_category:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock 
                FROM products 
                WHERE category_id = ? AND active = 1 AND stock > 0
                ORDER BY name
            ''', (selected_category,))
        else:
            cursor.execute('''
                SELECT id, name, description, price, image_url, stock 
                FROM products 
                WHERE active = 1 AND stock > 0
                ORDER BY name
            ''')
        
        products = cursor.fetchall()
        conn.close()
        
        # Filtrar por busca se necessário
        if search_query:
            products = [p for p in products if search_query.lower() in p[1].lower()]
        
        product_cards = []
        for prod_id, name, description, price, image_url, stock in products:
            card = ft.Card(
                content=ft.Container(
                    content=ft.Column([
                        ft.Container(
                            content=ft.Image(
                                src=image_url if image_url else "static/default_product.png",
                                width=200,
                                height=150,
                                fit=ft.ImageFit.COVER,
                            ),
                            border_radius=10,
                            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
                        ),
                        ft.Container(
                            content=ft.Column([
                                ft.Text(
                                    name,
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=ft.colors.BLACK
                                ),
                                ft.Text(
                                    description or "Sem descrição",
                                    size=14,
                                    color=ft.colors.GREY_600,
                                    max_lines=2,
                                    overflow=ft.TextOverflow.ELLIPSIS
                                ),
                                ft.Row([
                                    ft.Text(
                                        format_metical(price),
                                        size=16,
                                        weight=ft.FontWeight.BOLD,
                                        color=ft.colors.GREEN_600
                                    ),
                                    ft.Container(
                                        content=ft.Text(
                                            f"Estoque: {stock}",
                                            size=12,
                                            color=ft.colors.GREY_500
                                        ),
                                        bgcolor=ft.colors.GREY_100,
                                        padding=5,
                                        border_radius=5
                                    )
                                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                            ]),
                            padding=15
                        )
                    ]),
                    width=250,
                    bgcolor=ft.colors.WHITE,
                    border_radius=15,
                    shadow=ft.BoxShadow(
                        spread_radius=1,
                        blur_radius=15,
                        color=ft.colors.BLACK12,
                    )
                )
            )
            product_cards.append(card)
        
        products_container.content = ft.GridView(
            controls=product_cards,
            max_extent=280,
            spacing=20,
            run_spacing=20,
            child_aspect_ratio=0.8,
        )
        page.update()
    
    def on_search_change(e):
        nonlocal search_query
        search_query = e.control.value
        load_products()
    
    def go_back(e):
        if on_back:
            on_back(e)
    
    # Configurar interface
    header_container.content = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                on_click=go_back
            ),
            ft.Text(
                "Cardápio Digital",
                size=32,
                weight=ft.FontWeight.BOLD,
                color=ft.colors.WHITE
            )
        ], alignment=ft.MainAxisAlignment.START),
        bgcolor=ft.colors.BLUE_600,
        padding=20,
        border_radius=ft.border_radius.only(bottom_left=20, bottom_right=20)
    )
    
    search_container.content = ft.Container(
        content=ft.TextField(
            hint_text="Buscar produtos...",
            prefix_icon=ft.icons.SEARCH,
            on_change=on_search_change,
            border_radius=25,
            filled=True,
            bgcolor=ft.colors.WHITE,
            text_size=16
        ),
        padding=20
    )
    
    categories_container.content = ft.Container(
        padding=ft.padding.only(left=20, right=20, bottom=10)
    )
    
    products_container.content = ft.Container(
        padding=20
    )
    
    # Layout principal
    page.add(
        header_container,
        search_container,
        categories_container,
        products_container
    )
    
    # Carregar dados iniciais
    load_categories()
    load_products()
    
    return page 