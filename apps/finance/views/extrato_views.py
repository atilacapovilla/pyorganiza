from datetime import date, datetime

from django.contrib.auth.decorators import login_required
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.contrib.staticfiles import finders
from weasyprint import HTML, CSS

from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


@login_required
def extrato(request):
    today = date.today()
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    account_id = request.GET.get("account")
    status = request.GET.get("status", "todos")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = date(today.year, today.month, 1)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = today

    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__range=[start_date, end_date],
    ).order_by("transaction_date", "due_date")

    if account_id:
        transactions = transactions.filter(account__id=account_id)

    if status == "pagos":
        transactions = transactions.filter(is_paid=True)
    elif status == "abertos":
        transactions = transactions.filter(is_paid=False)
    elif status == "vencidos":
        transactions = transactions.filter(is_paid=False, due_date__lt=today)

    total_creditos = transactions.filter(type="C").aggregate(
        total=Sum("transaction_value")
    )["total"] or 0
    total_debitos = transactions.filter(type="D").aggregate(
        total=Sum("transaction_value")
    )["total"] or 0

    running_balance = 0
    extrato_rows = []
    for t in transactions:
        if t.type == "C":
            running_balance += t.transaction_value
        else:
            running_balance -= t.transaction_value
        extrato_rows.append({
            "transaction": t,
            "running_balance": running_balance,
        })

    accounts = Account.objects.filter(user=request.user)

    context = {
        "extrato_rows": extrato_rows,
        "total_creditos": total_creditos,
        "total_debitos": total_debitos,
        "saldo_final": total_creditos - total_debitos,
        "accounts": accounts,
        "start_date": start_date,
        "end_date": end_date,
        "selected_account": account_id,
        "selected_status": status,
    }
    return render(request, "extrato/extrato_list.html", context)


@login_required
def extrato_pdf(request):
    today = date.today()
    start_date_str = request.GET.get("start_date")
    end_date_str = request.GET.get("end_date")
    account_id = request.GET.get("account")
    status = request.GET.get("status", "todos")

    if start_date_str:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
    else:
        start_date = date(today.year, today.month, 1)

    if end_date_str:
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()
    else:
        end_date = today

    transactions = Transaction.objects.filter(
        user=request.user,
        transaction_date__range=[start_date, end_date],
    ).order_by("transaction_date", "due_date")

    if account_id:
        account_obj = Account.objects.get(pk=account_id, user=request.user)
        transactions = transactions.filter(account__id=account_id)
        account_nome = account_obj.name
    else:
        account_nome = "Todas as contas"

    if status == "pagos":
        transactions = transactions.filter(is_paid=True)
        status_label = "Pagas"
    elif status == "abertos":
        transactions = transactions.filter(is_paid=False)
        status_label = "Em aberto"
    elif status == "vencidos":
        transactions = transactions.filter(is_paid=False, due_date__lt=today)
        status_label = "Vencidas e não pagas"
    else:
        status_label = "Todas"

    total_creditos = transactions.filter(type="C").aggregate(
        total=Sum("transaction_value")
    )["total"] or 0
    total_debitos = transactions.filter(type="D").aggregate(
        total=Sum("transaction_value")
    )["total"] or 0

    running_balance = 0
    extrato_rows = []
    for t in transactions:
        if t.type == "C":
            running_balance += t.transaction_value
        else:
            running_balance -= t.transaction_value
        extrato_rows.append({
            "transaction": t,
            "running_balance": running_balance,
        })

    context = {
        "extrato_rows": extrato_rows,
        "total_creditos": total_creditos,
        "total_debitos": total_debitos,
        "saldo_final": total_creditos - total_debitos,
        "start_date": start_date,
        "end_date": end_date,
        "account_nome": account_nome,
        "status_label": status_label,
        "data_emissao": today,
    }

    html_string = render_to_string("extrato/extrato_pdf.html", context)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'inline; filename="extrato_{start_date.strftime("%Y%m%d")}_a_{end_date.strftime("%Y%m%d")}.pdf"'
    )
    HTML(string=html_string).write_pdf(
        response, stylesheets=[CSS(finders.find("css/extrato_pdf.css"))]
    )
    return response
