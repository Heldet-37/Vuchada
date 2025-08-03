import flet as ft
import sqlite3
from datetime import datetime


def CategoryView(page: ft.Page, on_back=None):
    # Cabeçalho (mantém igual)
    header = ft.Container(
        content=ft.Row(
            controls=[
                ft.IconButton(
                    icon=ft.icons.ARROW_BACK,
                    icon_color=ft.colors.WHITE,
                    tooltip="Voltar",
                    on_click=lambda _: on_back() if on_back else None
                ),
                ft.Icon(
                    name=ft.icons.CATEGORY,
                    size=50,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Categorias",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Nova Categoria",
                    icon=ft.icons.ADD,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN
                    ),
                    on_click=lambda _: show_add_category_dialog()
                )
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN
        ),
        gradient=ft.LinearGradient(
            begin=ft.alignment.top_left,
            end=ft.alignment.bottom_right,
            colors=[ft.colors.BLUE_900, ft.colors.BLUE_700]
        ),
        padding=50,
        border_radius=10
    )

    # Grid de categorias
    categories_grid = ft.GridView(
        expand=1,
        runs_count=3,
        max_extent=340,
        child_aspect_ratio=1.2,
        spacing=20,
        run_spacing=20,
        controls=[]
    )

    def load_categories():
        categories_grid.controls.clear()
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, name, description, is_active, created_at 
            FROM categories 
            ORDER BY name
        ''')
        categories = cursor.fetchall()
        conn.close()
        for category in categories:
            cat_id, name, description, is_active, created_at = category
            card = ft.Container(
                bgcolor=ft.colors.BLUE_800,
                border_radius=14,
                border=ft.border.all(2, ft.colors.BLUE_600),
                padding=20,
                content=ft.Column([
                    ft.Text(name, size=20, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
                    ft.Text(description or "Sem descrição", size=14, color=ft.colors.WHITE70, max_lines=2, overflow=ft.TextOverflow.ELLIPSIS),
                    ft.Container(height=8),
                    ft.Row([
                        ft.Container(
                            content=ft.Text(
                                "Ativa" if is_active else "Inativa",
                                size=12,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=ft.colors.GREEN if is_active else ft.colors.RED,
                            padding=5,
                            border_radius=5
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.icons.EDIT,
                            icon_color=ft.colors.AMBER_200,
                            tooltip="Editar",
                            on_click=lambda e, c=category: edit_category(c)
                        ),
                        ft.IconButton(
                            icon=ft.icons.DELETE,
                            icon_color=ft.colors.RED_400,
                            tooltip="Excluir",
                            on_click=lambda e, c=category: delete_category(c)
                        ),
                        ft.IconButton(
                            icon=ft.icons.TOGGLE_ON if is_active else ft.icons.TOGGLE_OFF,
                            icon_color=ft.colors.GREEN if is_active else ft.colors.GREY_400,
                            tooltip="Ativar/Desativar",
                            on_click=lambda e, c=category: toggle_category(c)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
                ], spacing=10)
            )
            categories_grid.controls.append(card)
        page.update()

    def show_add_category_dialog():
        name_field = ft.TextField(
            label="Nome da Categoria",
            hint_text="Ex: Carnes, Grãos, Pratos Principais",
            width=300
        )
        description_field = ft.TextField(
            label="Descrição",
            hint_text="Ex: Ingredientes de origem animal",
            width=300,
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        tipo_field = ft.Dropdown(
            label="Tipo",
            value="ambos",
            options=[
                ft.dropdown.Option("ambos", "Ambos"),
                ft.dropdown.Option("produto_final", "Produto Final"),
                ft.dropdown.Option("insumo", "Insumo")
            ],
            width=200
        )
        def save_category(e):
            if not name_field.value.strip():
                page.show_snack_bar(ft.SnackBar(content=ft.Text("Nome da categoria é obrigatório")))
                return
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO categories (name, description, tipo, is_active, created_at)
                VALUES (?, ?, ?, 1, ?)
            ''', (name_field.value.strip(), description_field.value.strip(), tipo_field.value, datetime.now().isoformat()))
            conn.commit()
            conn.close()
            dialog.open = False
            page.update()
            load_categories()
        dialog = ft.AlertDialog(
            title=ft.Text("Nova Categoria"),
            content=ft.Column(
                controls=[
                    name_field,
                    description_field,
                    tipo_field
                ],
                spacing=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Salvar", on_click=save_category)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def edit_category(category):
        cat_id, name, description, is_active, created_at = category
        # Buscar tipo da categoria
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('SELECT tipo FROM categories WHERE id = ?', (cat_id,))
        tipo_row = cursor.fetchone()
        tipo_value = tipo_row[0] if tipo_row else "ambos"
        conn.close()
        name_field = ft.TextField(
            label="Nome da Categoria",
            value=name,
            width=300
        )
        description_field = ft.TextField(
            label="Descrição",
            value=description or "",
            width=300,
            multiline=True,
            min_lines=2,
            max_lines=3
        )
        tipo_field = ft.Dropdown(
            label="Tipo",
            value=tipo_value,
            options=[
                ft.dropdown.Option("ambos", "Ambos"),
                ft.dropdown.Option("produto_final", "Produto Final"),
                ft.dropdown.Option("insumo", "Insumo")
            ],
            width=200
        )
        def save_changes(e):
            if not name_field.value.strip():
                page.show_snack_bar(ft.SnackBar(content=ft.Text("Nome da categoria é obrigatório")))
                return
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE categories 
                SET name = ?, description = ?, tipo = ?
                WHERE id = ?
            ''', (name_field.value.strip(), description_field.value.strip(), tipo_field.value, cat_id))
            conn.commit()
            conn.close()
            dialog.open = False
            page.update()
            load_categories()
        dialog = ft.AlertDialog(
            title=ft.Text("Editar Categoria"),
            content=ft.Column(
                controls=[
                    name_field,
                    description_field,
                    tipo_field
                ],
                spacing=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Salvar", on_click=save_changes)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def delete_category(category):
        cat_id, name, description, is_active, created_at = category
        def confirm_delete(e):
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM categories WHERE id = ?', (cat_id,))
            conn.commit()
            conn.close()
            dialog.open = False
            page.update()
            load_categories()
        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja realmente excluir a categoria '{name}'?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
                ft.TextButton("Excluir", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def toggle_category(category):
        cat_id, name, description, is_active, created_at = category
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE categories 
            SET is_active = ?
            WHERE id = ?
        ''', (0 if is_active else 1, cat_id))
        conn.commit()
        conn.close()
        load_categories()

    # Carregar categorias ao inicializar
    load_categories()

    return ft.Container(
        content=ft.Column([
            header,
            ft.Container(height=24),
            categories_grid
        ], expand=True, scroll=ft.ScrollMode.AUTO),
        padding=ft.padding.only(left=20, right=20, bottom=20)
    ) 