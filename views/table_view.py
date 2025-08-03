import flet as ft
import sqlite3
from datetime import datetime


def TableView(page: ft.Page, on_back=None):
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
                    name=ft.icons.TABLE_RESTAURANT,
                    size=50,
                    color=ft.colors.WHITE
                ),
                ft.Text(
                    "Gerenciar Mesas",
                    size=30,
                    weight=ft.FontWeight.BOLD,
                    color=ft.colors.WHITE
                ),
                ft.Container(expand=True),
                ft.ElevatedButton(
                    "Nova Mesa",
                    icon=ft.icons.ADD,
                    style=ft.ButtonStyle(
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN
                    ),
                    on_click=lambda _: show_add_table_dialog()
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

    # Grid de mesas
    tables_grid = ft.GridView(
        expand=1,
        runs_count=5,
        max_extent=240,  # Aumentado
        child_aspect_ratio=0.7,  # Diminuído para deixar os cards mais altos
        spacing=16,
        run_spacing=16,
    )

    # Remover variáveis e lógica de paginação
    # PAGE_SIZE = 12
    # current_page = [1]

    def load_tables():
        tables_grid.controls.clear()
        conn = sqlite3.connect('database/restaurant.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, number, capacity, status, current_order_id, created_at 
            FROM tables 
            ORDER BY number
        ''')
        tables = cursor.fetchall()
        conn.close()

        for table in tables:
            table_id, number, capacity, status, order_id, created_at = table
            
            # Cores baseadas no status
            status_colors = {
                'livre': ft.colors.GREEN,
                'ocupada': ft.colors.RED,
                'reservada': ft.colors.ORANGE,
                'limpeza': ft.colors.GREY
            }
            
            status_text = {
                'livre': 'Livre',
                'ocupada': 'Ocupada',
                'reservada': 'Reservada',
                'limpeza': 'Limpeza'
            }

            table_card = ft.Container(
                content=ft.Stack([
                    ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            f"Mesa {number}",
                                    size=24,
                            weight=ft.FontWeight.BOLD,
                            color=ft.colors.WHITE
                        ),
                        ft.Text(
                            f"Capacidade: {capacity}",
                                    size=16,
                            color=ft.colors.WHITE
                        ),
                        ft.Container(
                            content=ft.Text(
                                status_text.get(status, status),
                                        size=14,
                                color=ft.colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=status_colors.get(status, ft.colors.GREY),
                                    padding=8,
                            border_radius=5
                        ),
                        ft.Container(height=16),
                            ],
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            alignment=ft.MainAxisAlignment.CENTER
                        ),
                        expand=True
                    ),
                    ft.Container(
                        content=ft.PopupMenuButton(
                            items=[
                                ft.PopupMenuItem(text="Editar", on_click=lambda e, t=table: show_confirmation_dialog(t, "edit")),
                                ft.PopupMenuItem(text="Excluir", on_click=lambda e, t=table: show_confirmation_dialog(t, "delete")),
                            ],
                            icon=ft.icons.MORE_VERT
                        ),
                        alignment=ft.alignment.top_right,
                        padding=ft.padding.only(top=4, right=4)
                    )
                ]),
                bgcolor=ft.colors.BLUE_800,
                padding=12,
                border_radius=14,
                border=ft.border.all(2, status_colors.get(status, ft.colors.GREY))
            )
            tables_grid.controls.append(table_card)
        page.update()

    def show_add_table_dialog():
        number_field = ft.TextField(
            label="Número da Mesa",
            hint_text="Ex: 1",
            width=200
        )
        capacity_field = ft.TextField(
            label="Capacidade",
            hint_text="Ex: 4",
            width=200
        )

        def save_table(e):
            try:
                number = int(number_field.value)
                capacity = int(capacity_field.value)
                
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                try:
                    cursor.execute('''
                        INSERT INTO tables (number, capacity, status, created_at)
                        VALUES (?, ?, 'livre', ?)
                    ''', (number, capacity, datetime.now().isoformat()))
                    conn.commit()
                except sqlite3.IntegrityError:
                    page.show_snack_bar(ft.SnackBar(
                        content=ft.Text(f"Já existe uma mesa com o número {number}", color=ft.colors.WHITE),
                        bgcolor=ft.colors.RED_400
                    ))
                    return
                finally:
                    conn.close()
                
                dialog.open = False
                load_tables()  # Esta função já atualiza a página
                
            except ValueError:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Por favor, insira valores válidos", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))

        dialog = ft.AlertDialog(
            title=ft.Text("Nova Mesa"),
            content=ft.Column(
                controls=[
                    number_field,
                    capacity_field
                ],
                spacing=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Salvar", on_click=save_table)
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    def edit_table(table):
        table_id, number, capacity, status, order_id, created_at = table
        
        number_field = ft.TextField(
            label="Número da Mesa",
            value=str(number),
            width=200
        )
        capacity_field = ft.TextField(
            label="Capacidade",
            value=str(capacity),
            width=200
        )
        status_dropdown = ft.Dropdown(
            label="Status",
            value=status,
            width=200,
            options=[
                ft.dropdown.Option("livre", "Livre"),
                ft.dropdown.Option("ocupada", "Ocupada"),
                ft.dropdown.Option("reservada", "Reservada"),
                ft.dropdown.Option("limpeza", "Limpeza")
            ]
        )

        def save_changes(e):
            try:
                new_number = int(number_field.value)
                new_capacity = int(capacity_field.value)
                new_status = status_dropdown.value
                
                conn = sqlite3.connect('database/restaurant.db')
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE tables 
                    SET number = ?, capacity = ?, status = ?
                    WHERE id = ?
                ''', (new_number, new_capacity, new_status, table_id))
                conn.commit()
                conn.close()
                
                dialog.open = False
                load_tables()  # Esta função já atualiza a página
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"Mesa {new_number} atualizada com sucesso!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.GREEN_400
                ))
            except ValueError:
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text("Por favor, insira valores válidos", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))

        dialog = ft.AlertDialog(
            title=ft.Text("Editar Mesa"),
            content=ft.Column(
                controls=[
                    number_field,
                    capacity_field,
                    status_dropdown
                ],
                spacing=20
            ),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Salvar", on_click=save_changes)
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    def delete_table(table):
        table_id, number, capacity, status, order_id, created_at = table
        
        def confirm_delete(e):
            if status == 'ocupada':
                page.show_snack_bar(ft.SnackBar(
                    content=ft.Text(f"Não é possível excluir a Mesa {number} pois está ocupada!", color=ft.colors.WHITE),
                    bgcolor=ft.colors.RED_400
                ))
                dialog.open = False
                page.update()
                return
            conn = sqlite3.connect('database/restaurant.db')
            cursor = conn.cursor()
            cursor.execute('DELETE FROM tables WHERE id = ?', (table_id,))
            conn.commit()
            conn.close()
            
            dialog.open = False
            load_tables()  # Esta função já atualiza a página
            page.show_snack_bar(ft.SnackBar(
                content=ft.Text(f"Mesa {number} excluída com sucesso!", color=ft.colors.WHITE),
                bgcolor=ft.colors.GREEN_400
            ))

        dialog = ft.AlertDialog(
            title=ft.Text("Confirmar Exclusão"),
            content=ft.Text(f"Deseja realmente excluir a Mesa {number}?"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Excluir", on_click=confirm_delete, style=ft.ButtonStyle(color=ft.colors.RED))
            ]
        )
        
        page.dialog = dialog
        dialog.open = True
        page.update()

    def view_orders(table):
        table_id, number, capacity, status, order_id, created_at = table
        # TODO: Implementar visualização de pedidos da mesa
        page.show_snack_bar(ft.SnackBar(content=ft.Text(f"Visualizar pedidos da Mesa {number}")))

    def show_confirmation_dialog(table, action):
        def on_confirm(e):
            dialog.open = False
            page.update()
            if action == "edit":
                edit_table(table)
            elif action == "delete":
                delete_table(table)

        dialog = ft.AlertDialog(
            title=ft.Text(f"Confirmar Ação"),
            content=ft.Text(f"Deseja realmente {action} a Mesa {table[1]}?"),
            actions=[
                ft.TextButton("Sim", on_click=on_confirm),
                ft.TextButton("Não", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    # Carregar mesas ao inicializar
    load_tables()

    return ft.Container(
        content=ft.Column(
            controls=[
                header,
                ft.Container(height=20),
                tables_grid
            ],
            scroll=ft.ScrollMode.AUTO,
            expand=True
        ),
        padding=ft.padding.only(left=20, right=20, bottom=20)
    ) 