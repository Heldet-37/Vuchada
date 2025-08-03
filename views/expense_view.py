import flet as ft
import sqlite3
import datetime
import os

DB_PATH = os.path.join("database", "restaurant.db")

CATEGORIES = [
    "Aluguel", "Salários", "Compras", "Contas", "Manutenção", "Outros"
]

def get_expenses():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT e.id, e.created_at, e.amount, e.category, e.description, u.username
        FROM expenses e
        LEFT JOIN users u ON e.user_id = u.id
        ORDER BY e.created_at DESC
    ''')
    expenses = cursor.fetchall()
    conn.close()
    return expenses

def add_expense(created_at, amount, category, description, user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO expenses (created_at, amount, category, description, user_id)
        VALUES (?, ?, ?, ?, ?)
    ''', (created_at, amount, category, description, user_id))
    conn.commit()
    conn.close()

def ExpenseView(page: ft.Page, user, on_back=None):
    today = datetime.date.today()
    total_text = ft.Text("Total de Despesas: 0 MZN", size=18, weight=ft.FontWeight.BOLD)
    msg = ft.Text("")
    expenses_list = ft.Column([], spacing=10)

    def show_add_expense_modal(e=None):
        date_field = ft.TextField(label="Data", value=str(today), width=120)
        amount_field = ft.TextField(label="Valor (MZN)", width=120)
        category_field = ft.Dropdown(label="Categoria", width=150, options=[ft.dropdown.Option(c, c) for c in CATEGORIES], value="Outros")
        desc_field = ft.TextField(label="Descrição", width=200)
        modal_msg = ft.Text("")
        def save_expense(ev):
            try:
                add_expense(
                    date_field.value,
                    float(amount_field.value.replace(",", ".")),
                    category_field.value,
                    desc_field.value,
                    user[0] if user else None
                )
                modal_msg.value = "Despesa adicionada!"
                dialog.open = False
                update_expenses()
                page.snack_bar = ft.SnackBar(ft.Text("Despesa adicionada!"), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True
                page.update()
            except Exception as ex:
                modal_msg.value = f"Erro: {ex}"
                page.update()
        dialog = ft.AlertDialog(
            title=ft.Text("Adicionar Despesa"),
            content=ft.Column([
                date_field,
                amount_field,
                category_field,
                desc_field,
                modal_msg
            ], spacing=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Salvar", on_click=save_expense)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def update_expenses(e=None):
        expenses = get_expenses()
        total = 0
        expenses_list.controls.clear()
        for row in expenses:
            total += row[2]
            expenses_list.controls.append(
                ft.Container(
                    bgcolor=ft.colors.WHITE,
                    border_radius=16,
                    border=ft.border.all(1, ft.colors.GREY_200),
                    shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06)),
                    margin=ft.margin.all(4),
                    padding=0,
                    content=ft.Column([
                        ft.Text(f"{row[1][:16]}", size=14, color=ft.colors.BLUE_900, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{row[3]}", size=14, color=ft.colors.BLUE_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{row[2]:.2f} MZN", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.GREEN_700, text_align=ft.TextAlign.CENTER),
                        ft.Text(row[4] or "", size=13, color=ft.colors.GREY_800, text_align=ft.TextAlign.CENTER),
                        ft.Text(row[5] or "", size=12, color=ft.colors.GREY_700, text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
                )
            )
        total_text.value = f"Total de Despesas: {total:.2f} MZN"
        page.update()

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                tooltip="Voltar",
                on_click=on_back
            ),
            ft.Icon(
                name=ft.icons.MONEY_OFF,
                size=50,
                color=ft.colors.WHITE
            ),
            ft.Text(
                "Despesas",
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

    add_btn = ft.ElevatedButton(
        "Adicionar Despesa",
        icon=ft.icons.ADD,
        bgcolor=ft.colors.BLUE_700,
        color=ft.colors.WHITE,
        on_click=show_add_expense_modal
    )

    content = ft.Column([
        header,
        ft.Container(height=20),
        add_btn,
        msg,
        ft.Container(height=20),
        total_text,
        expenses_list
    ], spacing=18, expand=True)

    update_expenses()
    return content 