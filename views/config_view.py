import flet as ft
import sqlite3
import shutil
import os

SETTINGS_FIELDS = [
    ("restaurant_name", "Nome do Restaurante"),
    ("address", "Endereço"),
    ("phone", "Telefone"),
]
CURRENCY_OPTIONS = [
    ("MT", "Metical (MT)"),
    ("R$", "Real (R$)"),
    ("$", "Dólar ($)"),
    ("€", "Euro (€)"),
    ("ZAR", "Rand (ZAR)"),
]

DB_PATH = os.path.join("database", "restaurant.db")
BACKUP_DIR = os.path.join(os.getcwd(), "backups")


def get_settings():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )''')
    settings = {}
    for key, _ in SETTINGS_FIELDS:
        cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
        row = cursor.fetchone()
        settings[key] = row[0] if row else ''
    # Moeda
    cursor.execute('SELECT value FROM settings WHERE key = ?', ("currency",))
    row = cursor.fetchone()
    settings["currency"] = row[0] if row else "MT"
    conn.close()
    return settings

def save_settings(new_settings):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    for key, value in new_settings.items():
        cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def list_backups():
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
    return [f for f in os.listdir(BACKUP_DIR) if f.endswith('.db')]

def ConfigView(page: ft.Page, user, on_back=None):
    settings = get_settings()
    fields = {}
    for key, label in SETTINGS_FIELDS:
        fields[key] = ft.TextField(label=label, value=settings.get(key, ''), width=350)
    currency_field = ft.Dropdown(
        label="Moeda",
        width=200,
        value=settings.get("currency", "MT"),
        options=[ft.dropdown.Option(code, label) for code, label in CURRENCY_OPTIONS]
    )
    msg = ft.Text("")
    backup_msg = ft.Text("")
    reset_msg = ft.Text("")
    file_picker = ft.FilePicker()

    def on_save(e):
        new_settings = {key: fields[key].value for key, _ in SETTINGS_FIELDS}
        new_settings["currency"] = currency_field.value
        save_settings(new_settings)
        msg.value = "Configurações salvas com sucesso!"
        page.snack_bar = ft.SnackBar(ft.Text(msg.value), bgcolor=ft.colors.GREEN)
        page.snack_bar.open = True
        page.update()

    def on_backup(e):
        def do_backup(ev):
            name = backup_name_field.value.strip()
            if not name:
                backup_msg.value = "Informe um nome para o backup."
                page.update()
                return
            if not os.path.exists(BACKUP_DIR):
                os.makedirs(BACKUP_DIR)
            backup_path = os.path.join(BACKUP_DIR, f"{name}.db")
            shutil.copy(DB_PATH, backup_path)
            backup_msg.value = f"Backup criado: {backup_path}"
            dialog.open = False
            page.snack_bar = ft.SnackBar(ft.Text("Backup realizado com sucesso!"), bgcolor=ft.colors.BLUE)
            page.snack_bar.open = True
            page.update()
        backup_name_field = ft.TextField(label="Nome do Backup", width=250)
        dialog = ft.AlertDialog(
            title=ft.Text("Fazer Backup"),
            content=backup_name_field,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Salvar Backup", on_click=do_backup)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def on_restore(e):
        backups = list_backups()
        if not backups:
            backup_msg.value = "Nenhum backup encontrado."
            page.snack_bar = ft.SnackBar(ft.Text("Nenhum backup encontrado."), bgcolor=ft.colors.RED)
            page.snack_bar.open = True
            page.update()
            return
        selected = {"file": None}
        def do_restore(ev):
            if not selected["file"]:
                backup_msg.value = "Selecione um backup."
                page.update()
                return
            try:
                shutil.copy(os.path.join(BACKUP_DIR, selected["file"]), DB_PATH)
                backup_msg.value = "Banco restaurado com sucesso! Reinicie o sistema."
                dialog.open = False
                page.snack_bar = ft.SnackBar(ft.Text("Banco restaurado! Reinicie o sistema."), bgcolor=ft.colors.GREEN)
                page.snack_bar.open = True
            except Exception as ex:
                backup_msg.value = f"Erro ao restaurar: {ex}"
            page.update()
        backup_list = ft.ListView(
            controls=[
                ft.ListTile(
                    title=ft.Text(f),
                    selected=False,
                    on_click=lambda e, f=f: selected.update({"file": f})
                ) for f in backups
            ],
            height=200
        )
        dialog = ft.AlertDialog(
            title=ft.Text("Restaurar Backup"),
            content=ft.Column([
                ft.Text("Selecione um backup para restaurar:"),
                backup_list
            ], spacing=12),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Restaurar", on_click=do_restore)
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    def on_reset(e):
        def confirm_reset(ev):
            try:
                os.remove(DB_PATH)
                reset_msg.value = "Banco de dados resetado! O sistema será reiniciado."
                page.snack_bar = ft.SnackBar(ft.Text("Banco resetado! O sistema será reiniciado."), bgcolor=ft.colors.RED)
                page.snack_bar.open = True
                page.update()
                # Recarregar a página para forçar login novamente
                page.launch_url(page.route)
            except Exception as ex:
                reset_msg.value = f"Erro ao resetar: {ex}"
            dialog.open = False
            page.update()
        dialog = ft.AlertDialog(
            title=ft.Text("Resetar Banco de Dados"),
            content=ft.Text("Tem certeza que deseja resetar o banco de dados? Esta ação é irreversível!"),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: (setattr(dialog, 'open', False), page.update())),
                ft.TextButton("Resetar", on_click=confirm_reset, style=ft.ButtonStyle(color=ft.colors.RED))
            ]
        )
        page.dialog = dialog
        dialog.open = True
        page.update()

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.icons.ARROW_BACK,
                icon_color=ft.colors.WHITE,
                tooltip="Voltar",
                on_click=lambda e: on_back(e) if on_back else None
            ),
            ft.Icon(
                name=ft.icons.SETTINGS,
                size=50,
                color=ft.colors.WHITE
            ),
            ft.Text(
                "Configurações do Sistema",
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

    return ft.Column([
        header,
        ft.Container(height=16),
        ft.ResponsiveRow([
            ft.Container(
                content=ft.Column([
                    *(fields[key] for key, _ in SETTINGS_FIELDS),
                    currency_field,
                    ft.Container(height=12),
                    ft.ElevatedButton("Salvar Configurações", icon=ft.icons.SAVE, on_click=on_save, bgcolor=ft.colors.GREEN, color=ft.colors.WHITE),
                    msg
                ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=16),
                col={"sm": 12, "md": 7, "xl": 6},
                padding=ft.padding.all(24),
                bgcolor=ft.colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06)),
            ),
            ft.Container(
                content=ft.Column([
                    ft.Text("Backup e Restauração", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
                    ft.Container(height=8),
                    ft.ElevatedButton("Fazer Backup", icon=ft.icons.DOWNLOAD, on_click=on_backup, bgcolor=ft.colors.BLUE_700, color=ft.colors.WHITE),
                    ft.ElevatedButton("Restaurar Banco", icon=ft.icons.UPLOAD, on_click=on_restore, bgcolor=ft.colors.AMBER_700, color=ft.colors.WHITE),
                    backup_msg,
                    ft.Divider(),
                    ft.Text("Resetar Sistema", size=18, weight=ft.FontWeight.BOLD, color=ft.colors.RED_700),
                    ft.Container(height=8),
                    ft.ElevatedButton("Resetar Banco de Dados", icon=ft.icons.DELETE, on_click=on_reset, bgcolor=ft.colors.RED_700, color=ft.colors.WHITE),
                    reset_msg
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=16),
                col={"sm": 12, "md": 5, "xl": 4},
                padding=ft.padding.all(24),
                bgcolor=ft.colors.WHITE,
                border_radius=12,
                shadow=ft.BoxShadow(blur_radius=8, color=ft.colors.with_opacity(ft.colors.BLACK, 0.06)),
            )
        ], spacing=32, run_spacing=32, alignment=ft.MainAxisAlignment.CENTER),
    ], expand=True, scroll=ft.ScrollMode.AUTO) 