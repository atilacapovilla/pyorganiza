from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.shortcuts import redirect
from django.shortcuts import render

from apps.finance.forms.transfer_forms import TransferForm
from apps.finance.models.transaction import Transaction


@login_required
@transaction.atomic
def Transfer(request):
    template_name = "transfer/transfer_form.html"
    form = TransferForm(request.user, request.POST or None)

    if request.method == "POST":
        if form.is_valid():
            transaction_date = form.cleaned_data.get("transaction_date")
            account_origin = form.cleaned_data.get("account_origin")
            account_destination = form.cleaned_data.get("account_destination")
            category = form.cleaned_data.get("category")
            transaction_value = form.cleaned_data.get("transaction_value")
            description = form.cleaned_data.get("description")

            Transaction.objects.create(
                due_date=transaction_date,
                transaction_date=transaction_date,
                account_id=account_origin,
                category_id=category,
                transaction_value=transaction_value,
                description=description,
                type="D",
                is_paid=True,
                user=request.user,
            )

            Transaction.objects.create(
                due_date=transaction_date,
                transaction_date=transaction_date,
                account_id=account_destination,
                category_id=category,
                transaction_value=transaction_value,
                description=description,
                type="C",
                is_paid=True,
                user=request.user,
            )

            messages.success(
                request,
                "Transferência concluída com sucesso",
            )

            return redirect("transactions")

    context = {"form": form}
    return render(request, template_name, context)
