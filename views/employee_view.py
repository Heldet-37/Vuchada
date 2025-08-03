import flet as ft
from database.models import get_user_by_username, create_user, hash_password
from database.db import get_connection

ADMIN_USERNAME = "Alves37"


def EmployeeView(page: ft.Page, on_back=None):
    error_text = ft.Text("", color=ft.colors.RED, size=14)
    editing_id = {'id': None}  # Usar dict para mutabilidade no escopo

    def fetch_employees():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, name, role, active FROM users WHERE username != ?", (ADMIN_USERNAME,))
        employees = cursor.fetchall()
        conn.close()
        return employees

    def add_employee(e):
        dialog.title = ft.Text("Novo Funcionário")
        username_field.value = ""
        name_field.value = ""
        password_field.value = ""
        role_field.value = None
        error_text.value = ""
        editing_id['id'] = None
        dialog.open = True
        page.update()

    def save_employee(e):
        username = username_field.value.strip()
        name = name_field.value.strip()
        password = password_field.value.strip()
        role = role_field.value
        if not (username and name and role):
            error_text.value = "Preencha todos os campos."
            page.update()
            return
        if editing_id['id'] is None:
            # Adição
            if get_user_by_username(username):
                error_text.value = "Usuário já existe!"
                page.update()
                return
            try:
                create_user(username, password, name, role)
                dialog.open = False
                error_text.value = ""
                page.update()
                refresh()
            except Exception as ex:
                error_text.value = f"Erro ao salvar: {ex}"
                page.update()
        else:
            # Edição
            try:
                conn = get_connection()
                cursor = conn.cursor()
                if password:
                    hashed_password = hash_password(password)
                    cursor.execute("UPDATE users SET username=?, name=?, password=?, role=? WHERE id=?", (username, name, hashed_password, role, editing_id['id']))
                else:
                    cursor.execute("UPDATE users SET username=?, name=?, role=? WHERE id=?", (username, name, role, editing_id['id']))
                conn.commit()
                conn.close()
                dialog.open = False
                error_text.value = ""
                page.update()
                refresh()
            except Exception as ex:
                error_text.value = f"Erro ao editar: {ex}"
                page.update()

    def delete_employee(emp_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ?", (emp_id,))
        conn.commit()
        conn.close()
        refresh()

    def toggle_active(emp_id, current):
        new_status = 0 if current else 1
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET active = ? WHERE id = ?", (new_status, emp_id))
        conn.commit()
        conn.close()
        refresh()

    def edit_employee(emp):
        username_field.value = emp[1]
        name_field.value = emp[2]
        password_field.value = ""
        role_field.value = emp[3]
        dialog.title = ft.Text(f"Editar Funcionário: {emp[2]}")
        error_text.value = ""
        editing_id['id'] = emp[0]
        dialog.open = True
        page.update()

    def refresh():
        employees = fetch_employees()
        table.rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text(str(emp[0]))),
                    ft.DataCell(ft.Text(emp[1])),
                    ft.DataCell(ft.Text(emp[2])),
                    ft.DataCell(ft.Text(emp[3])),
                    ft.DataCell(ft.Text("Ativo", color=ft.colors.GREEN) if emp[4] else ft.Text("Inativo", color=ft.colors.RED)),
                    ft.DataCell(
                        ft.Row([
                            ft.IconButton(icon=ft.icons.EDIT, icon_color=ft.colors.BLUE, tooltip="Editar", on_click=lambda e, emp=emp: edit_employee(emp)),
                            ft.IconButton(icon=ft.icons.POWER_SETTINGS_NEW, icon_color=ft.colors.ORANGE if emp[4] else ft.colors.GREEN, tooltip="Desativar" if emp[4] else "Ativar", on_click=lambda e, emp_id=emp[0], current=emp[4]: toggle_active(emp_id, current)),
                            ft.IconButton(icon=ft.icons.DELETE, icon_color=ft.colors.RED, tooltip="Excluir", on_click=lambda e, emp_id=emp[0]: delete_employee(emp_id))
                        ], spacing=5)
                    )
                ]
            ) for emp in employees
        ]
        page.update()

    # Campos do dialog de novo funcionário
    username_field = ft.TextField(label="Usuário")
    name_field = ft.TextField(label="Nome")
    password_field = ft.TextField(label="Senha", password=True)
    role_field = ft.Dropdown(label="Função", options=[ft.dropdown.Option("admin"), ft.dropdown.Option("funcionario")])

    dialog = ft.AlertDialog(
        modal=True,
        title=ft.Text("Novo Funcionário"),
        content=ft.Column([
            username_field,
            name_field,
            password_field,
            role_field,
            error_text
        ], tight=True),
        actions=[
            ft.TextButton("Cancelar", on_click=lambda e: setattr(dialog, 'open', False)),
            ft.ElevatedButton("Salvar", on_click=save_employee)
        ]
    )

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Usuário")),
            ft.DataColumn(ft.Text("Nome")),
            ft.DataColumn(ft.Text("Função")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Ações")),
        ],
        rows=[]
    )

    refresh()

    header = ft.Container(
        content=ft.Row([
            ft.Icon(ft.icons.PEOPLE, size=36, color=ft.colors.WHITE),
            ft.Text("Funcionários", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
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

    return ft.Column([
        header,
        ft.Container(height=20),
        ft.Row([
            ft.Text("Lista de Funcionários", size=20, weight=ft.FontWeight.BOLD),
            ft.Container(expand=True),
            ft.ElevatedButton("Novo Funcionário", icon=ft.icons.PERSON_ADD, on_click=add_employee)
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
        ft.Container(
            content=table,
            border=ft.border.all(1, ft.colors.BLACK26),
            border_radius=10,
            padding=10,
            margin=ft.margin.only(right=20, bottom=20)
        ),
        dialog
    ], expand=True) 