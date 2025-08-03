import flet as ft
from controllers.auth_controller import authenticate, ensure_default_admin


def LoginView(page: ft.Page, on_login_success):
    ensure_default_admin()
    username = ft.TextField(
        label="Usuário",
        prefix_icon=ft.icons.PERSON,
        autofocus=True,
        width=300
    )
    password = ft.TextField(
        label="Senha",
        password=True,
        can_reveal_password=True,
        prefix_icon=ft.icons.LOCK,
        width=300
    )
    error_text = ft.Text("", color=ft.colors.RED, size=12)

    def do_login(e):
        user = authenticate(username.value, password.value)
        if user:
            error_text.value = ""
            on_login_success(user)
        else:
            error_text.value = "Usuário ou senha inválidos!"
        page.update()

    login_card = ft.Container(
        content=ft.Column([
            ft.Text("Bem-vindo(a)", size=28, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_900),
            ft.Text("Faça login para acessar o sistema", size=14, color=ft.colors.GREY_700),
            username,
            password,
            ft.ElevatedButton(
                "Entrar",
                icon=ft.icons.LOGIN,
                style=ft.ButtonStyle(
                    bgcolor=ft.colors.BLUE_900,
                    color=ft.colors.WHITE,
                    padding=20,
                    shape=ft.RoundedRectangleBorder(radius=8)
                ),
                on_click=do_login,
                width=300
            ),
            error_text
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        alignment=ft.MainAxisAlignment.CENTER,
        spacing=10),
        padding=40,
        bgcolor=ft.colors.WHITE,
        border_radius=ft.BorderRadius(0, 16, 0, 16),
        width=400,
        height=400
    )

    left_card = ft.Container(
        content=ft.Column([
            ft.Icon(ft.icons.SHOPPING_CART, size=64, color=ft.colors.WHITE),
            ft.Text("Sistema de Gestão", size=26, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Text("Sua solução completa para gestão comercial", size=14, color=ft.colors.WHITE70),
            ft.Text("Neotrix", size=20, weight=ft.FontWeight.BOLD, color=ft.colors.WHITE),
            ft.Text("Tecnologias ao seu alcance", size=12, color=ft.colors.WHITE70, italic=True),
        ],
        alignment=ft.MainAxisAlignment.CENTER,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        spacing=10),
        bgcolor=ft.colors.BLUE_800,
        padding=40,
        border_radius=ft.BorderRadius(16, 0, 16, 0),
        width=400,
        height=400,
    )

    return ft.Container(
        content=ft.Row([
            left_card,
            login_card
        ], spacing=0, alignment=ft.MainAxisAlignment.CENTER, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        alignment=ft.alignment.center,
        expand=True
    ) 