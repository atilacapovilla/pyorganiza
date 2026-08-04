import tempfile
from datetime import date

import sweetify
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from apps.finance.forms.import_forms import ImportUploadForm
from apps.finance.models.category import Category
from apps.finance.models.imported_transaction import ImportedTransaction
from apps.finance.models.transaction import Transaction
from apps.finance.utils.ofx_parser import parse_ofx


@login_required
def import_upload(request):
    if request.method == "POST":
        form = ImportUploadForm(request.user, request.POST, request.FILES)
        if form.is_valid():
            ofx_file = request.FILES["file"]
            account = form.cleaned_data["account"]

            with tempfile.NamedTemporaryFile(suffix=".ofx", delete=False) as tmp:
                for chunk in ofx_file.chunks():
                    tmp.write(chunk)
                tmp_path = tmp.name

            try:
                transactions = parse_ofx(tmp_path)
            except Exception as e:
                messages.error(request, f"Erro ao ler arquivo OFX: {e}")
                return render(
                    request, "import/import_form.html", {"form": ImportUploadForm(request.user)}
                )

            created = 0
            duplicates = 0
            for txn in transactions:
                _, was_created = ImportedTransaction.objects.get_or_create(
                    user=request.user,
                    bank_fit_id=txn["bank_fit_id"],
                    defaults={
                        "account": account,
                        "transaction_date": txn["transaction_date"],
                        "description": txn["description"],
                        "transaction_value": txn["transaction_value"],
                        "type": txn["type"],
                    },
                )
                if was_created:
                    created += 1
                else:
                    duplicates += 1

            sweetify.toast(
                request,
                f"{created} transações importadas. {duplicates} duplicatas ignoradas.",
                icon="success",
                button="OK",
                timer=3000,
            )
            return redirect("import-reconciliation")
    else:
        form = ImportUploadForm(request.user)

    return render(request, "import/import_form.html", {"form": form})


@login_required
def import_reconciliation(request):
    pending = ImportedTransaction.objects.filter(
        user=request.user, status="pending"
    ).order_by("transaction_date")

    status_filter = request.GET.get("status", "pending")
    if status_filter == "all":
        transactions = ImportedTransaction.objects.filter(user=request.user).order_by(
            "-created_at"
        )
    else:
        transactions = ImportedTransaction.objects.filter(
            user=request.user, status=status_filter
        ).order_by("transaction_date")

    categories = Category.objects.filter(user=request.user, parent__isnull=False).order_by(
        "category_type", "parent__name", "name"
    )

    context = {
        "pending": pending,
        "transactions": transactions,
        "current_status": status_filter,
        "categories": categories,
    }
    return render(request, "import/reconciliation.html", context)


@login_required
def import_match(request, pk):
    imported = get_object_or_404(ImportedTransaction, pk=pk, user=request.user)
    txn_id = request.POST.get("transaction_id")

    if txn_id:
        matched = get_object_or_404(Transaction, pk=txn_id, user=request.user)
        imported.matched_transaction = matched
        imported.status = "matched"
        imported.save()
        sweetify.toast(request, "Transação conciliada!", icon="success", button="OK", timer=2000)

    return redirect("import-reconciliation")


@login_required
def import_accept(request, pk):
    imported = get_object_or_404(ImportedTransaction, pk=pk, user=request.user)
    category_id = request.POST.get("category_id")

    if not category_id:
        sweetify.toast(request, "Selecione uma categoria!", icon="warning", button="OK", timer=2000)
        return redirect("import-reconciliation")

    Transaction.objects.create(
        transaction_date=imported.transaction_date,
        due_date=imported.transaction_date,
        is_paid=True,
        account=imported.account,
        category_id=category_id,
        description=imported.description[:50] if imported.description else "",
        transaction_value=imported.transaction_value,
        type=imported.type,
        user=request.user,
    )
    imported.status = "imported"
    imported.save()

    sweetify.toast(request, "Transação importada!", icon="success", button="OK", timer=2000)
    return redirect("import-reconciliation")


@login_required
def import_ignore(request, pk):
    imported = get_object_or_404(ImportedTransaction, pk=pk, user=request.user)
    imported.status = "ignored"
    imported.save()
    return redirect("import-reconciliation")
