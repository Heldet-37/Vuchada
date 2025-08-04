import flet as ft
from views.login_view import LoginView
from views.employee_dashboard_view import EmployeeDashboardView
from views.admin_dashboard_view import AdminDashboardView
from views.employee_view import EmployeeView
from views.product_view import ProductView
from views.table_view import TableView
from views.category_view import CategoryView
from views.order_view import OrderView
from views.report_view import ReportView
from views.pdv_view import PDVView
from views.my_sales_view import MySalesView
from views.all_sales_view import AllSalesView
from views.config_view import ConfigView
from views.financial_report_view import FinancialReportView
from views.expense_view import ExpenseView
from views.best_sellers_view import BestSellersView
from database import init_db


def main(page: ft.Page):
    init_db()
    page.title = "PDV Restaurante"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.window_full_screen = True
    page.window_resizable = False
    page.window_maximizable = False
    page.theme_mode = ft.ThemeMode.LIGHT
    page.bgcolor = ft.colors.WHITE

    user_session = {'user': None}

    def navigate(route, user):
        page.clean()
        user_session['user'] = user
        if route == "/admin":
            page.add(AdminDashboardView(page, user, lambda r: navigate(r, user), on_logout=logout))
        elif route == "/usuarios":
            page.add(EmployeeView(page, on_back=lambda e: navigate("/admin", user)))
        elif route == "/produtos":
            if user[4] == "admin":
                page.add(ProductView(page, on_back=lambda e: navigate("/admin", user)))
            else:
                page.add(ProductView(page, on_back=lambda e: page.clean() or page.add(EmployeeDashboardView(page, user, lambda r: navigate(r, user), on_logout=logout))))
        elif route == "/mesas":
            page.add(TableView(page, on_back=lambda e: navigate("/pdv", user)))
        elif route == "/categorias":
            if user[4] == "admin":
                page.add(CategoryView(page, on_back=lambda e: navigate("/admin", user)))
            else:
                page.add(CategoryView(page, on_back=lambda e: page.clean() or page.add(EmployeeDashboardView(page, user, lambda r: navigate(r, user), on_logout=logout))))
        elif route == "/pedidos":
            page.add(OrderView(page, on_back=lambda e: navigate("/pdv", user), user=user))
        elif route == "/pdv":
            if user[4] == "admin":
                page.add(PDVView(page, on_back=lambda e: navigate("/admin", user), user=user, on_navigate=lambda r: navigate(r, user)))
            else:
                page.add(PDVView(page, on_back=lambda e: page.clean() or page.add(EmployeeDashboardView(page, user, lambda r: navigate(r, user), on_logout=logout)), user=user, on_navigate=lambda r: navigate(r, user)))
        elif route == "/relatorios":
            page.add(ReportView(page, on_back=lambda e: navigate("/admin", user)))
        elif route == "/minhas-vendas":
            if user[4] == "admin":
                page.add(MySalesView(page, user, on_back=lambda e: navigate("/admin", user)))
            else:
                page.add(MySalesView(page, user, on_back=lambda e: page.clean() or page.add(EmployeeDashboardView(page, user, lambda r: navigate(r, user), on_logout=logout))))
        elif route == "/todas-vendas":
            page.add(AllSalesView(page, user, on_back=lambda e: navigate("/admin", user)))
        elif route == "/relatorio-financeiro":
            page.add(FinancialReportView(page, user, on_back=lambda e: navigate("/admin", user)))
        elif route == "/configuracoes":
            page.add(ConfigView(page, user, on_back=lambda e: navigate("/admin", user)))
        elif route == "/despesas":
            page.add(ExpenseView(page, user, on_back=lambda e: navigate("/admin", user)))
        elif route == "/produtos-mais-vendidos":
            page.add(BestSellersView(page, user, lambda r: navigate(r, user), on_logout=logout))
        else:
            page.add(ft.Text("Página não encontrada"))

    def logout():
        user_session['user'] = None
        page.clean()
        page.add(LoginView(page, on_login_success))

    def on_login_success(user):
        if user[4] == "admin":
            navigate("/admin", user)
        else:
            page.clean()
            page.add(EmployeeDashboardView(page, user, lambda r: navigate(r, user), on_logout=logout))

    page.add(LoginView(page, on_login_success))


if __name__ == "__main__":
    import flet as ft
    ft.app(target=main, assets_dir="static") 