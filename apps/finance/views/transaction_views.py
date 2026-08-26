from uuid import uuid4
from decimal import Decimal
from math import floor
from calendar import monthrange

import sweetify
from datetime import date

from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, CreateView, UpdateView

from apps.finance.forms.transaction_forms import TransactionForm
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


def _add_months(dt, months):
    total_months = dt.month + months - 1
    year = dt.year + total_months // 12
    month = total_months % 12 + 1
    day = min(dt.day, monthrange(year, month)[1])
    return date(year, month, day)


class TransactionList(LoginRequiredMixin, ListView):
    model = Transaction
    context_object_name = "transactions"
    template_name = "transaction/transaction_list.html"
    paginate_by = 100

    def get_queryset(self):
        start_date = self.request.GET.get("start_date")
        end_date = self.request.GET.get("end_date")
        account = self.request.GET.get("account")

        if not start_date or not end_date:
            today = date.today()
            start_date = date(today.year, today.month, 1)
            end_date = start_date.replace(
                day=monthrange(start_date.year, start_date.month)[1]
            )

        transactions = Transaction.objects.filter(
            user=self.request.user, transaction_date__range=[
                start_date, end_date]
        ).order_by("-transaction_date", "-due_date", "-created_at")

        if account:
            transactions = transactions.filter(account__id=account)

        return transactions

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["accounts"] = Account.objects.filter(user=self.request.user)
        return context


class TransactionCreate(LoginRequiredMixin, CreateView):
    model = Transaction
    template_name = "transaction/transaction_form.html"
    form_class = TransactionForm
    success_url = reverse_lazy("transaction-create")

    def get_initial(self):
        return {"user": self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = Account.objects.filter(user=self.request.user)
        context["account_types"] = {
            str(a.pk): a.type for a in accounts
        }
        return context

    def form_valid(self, form):
        form.instance.user = self.request.user

        installment_count = form.cleaned_data.get("installment_count")
        first_due_date = form.cleaned_data.get("first_due_date")
        installment_mode = form.cleaned_data.get("installment_mode") or "divide"
        date_behavior = form.cleaned_data.get("date_behavior") or "keep"

        if installment_count and installment_count >= 2 and first_due_date:
            return self._create_installments(form, installment_count, first_due_date, installment_mode, date_behavior)

        sweetify.toast(
            self.request,
            "Transação incluida com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return super(TransactionCreate, self).form_valid(form)

    def _create_installments(self, form, total, first_due_date, mode, date_behavior):
        instance = form.save(commit=False)
        instance.user = self.request.user

        group = uuid4()
        base_value = instance.transaction_value
        base_description = instance.description or ""

        if mode == "divide":
            parcela_value = Decimal(str(floor(base_value * 100 / total))) / Decimal("100")
        else:
            parcela_value = base_value

        with transaction.atomic():
            for i in range(total):
                if mode == "divide" and i == total - 1:
                    current_value = base_value - (parcela_value * (total - 1))
                else:
                    current_value = parcela_value

                due = _add_months(first_due_date, i)
                tx_date = _add_months(instance.transaction_date, i) if date_behavior == "increment" else instance.transaction_date
                desc = f"{base_description} ({i + 1}/{total})" if base_description else f"{i + 1}/{total}"

                Transaction.objects.create(
                    user=instance.user,
                    account=instance.account,
                    category=instance.category,
                    description=desc,
                    transaction_value=current_value,
                    type=instance.type,
                    transaction_date=tx_date,
                    due_date=due,
                    is_paid=instance.is_paid if i == 0 else False,
                    active=instance.active,
                    installment_group=group,
                    installment_number=i + 1,
                    total_installments=total,
                )

        sweetify.toast(
            self.request,
            f"{total} parcelas incluidas com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return HttpResponseRedirect(reverse_lazy("transaction-create"))


class TransactionUpdate(LoginRequiredMixin, UpdateView):
    model = Transaction
    template_name = "transaction/transaction_form.html"
    form_class = TransactionForm
    success_url = reverse_lazy("transactions")

    def get_initial(self):
        return {"user": self.request.user}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        accounts = Account.objects.filter(user=self.request.user)
        context["account_types"] = {
            str(a.pk): a.type for a in accounts
        }
        return context

    def form_valid(self, form):
        instance = form.save(commit=False)
        group = instance.installment_group

        if group:
            installment_count = form.cleaned_data.get("installment_count")
            first_due_date = form.cleaned_data.get("first_due_date")
            installment_mode = form.cleaned_data.get("installment_mode") or "divide"
            date_behavior = form.cleaned_data.get("date_behavior") or "keep"

            if installment_count and installment_count >= 2 and first_due_date:
                return self._update_installments(form, group, installment_count, first_due_date, installment_mode, date_behavior)

            Transaction.objects.filter(
                installment_group=group,
                installment_number__gte=instance.installment_number,
            ).update(
                account=instance.account,
                category=instance.category,
                transaction_value=instance.transaction_value,
                type=instance.type,
            )

            sweetify.toast(
                self.request,
                "Parcelas alteradas com sucesso",
                icon="success",
                button="OK",
                timer=2000,
            )
            return super(TransactionUpdate, self).form_valid(form)

        sweetify.toast(
            self.request,
            "Transação alterada com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return super(TransactionUpdate, self).form_valid(form)

    def _update_installments(self, form, group, total, first_due_date, mode, date_behavior):
        instance = form.save(commit=False)
        base_value = instance.transaction_value
        base_description = instance.description or ""

        if mode == "divide":
            parcela_value = Decimal(str(floor(base_value * 100 / total))) / Decimal("100")
        else:
            parcela_value = base_value

        with transaction.atomic():
            for i in range(total):
                if i == total - 1:
                    current_value = base_value - (parcela_value * (total - 1))
                else:
                    current_value = parcela_value

                due = _add_months(first_due_date, i)
                tx_date = _add_months(instance.transaction_date, i) if date_behavior == "increment" else instance.transaction_date
                desc = f"{base_description} ({i + 1}/{total})" if base_description else f"{i + 1}/{total}"

                Transaction.objects.update_or_create(
                    installment_group=group,
                    installment_number=i + 1,
                    defaults={
                        "user": instance.user,
                        "account": instance.account,
                        "category": instance.category,
                        "description": desc,
                        "transaction_value": current_value,
                        "type": instance.type,
                        "transaction_date": tx_date,
                        "due_date": due,
                        "is_paid": instance.is_paid if i == 0 else False,
                        "active": instance.active,
                        "total_installments": total,
                    },
                )

        sweetify.toast(
            self.request,
            f"{total} parcelas alteradas com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return HttpResponseRedirect(reverse_lazy("transactions"))

    def get_queryset(self):
        base_qs = super(TransactionUpdate, self).get_queryset()
        return base_qs.filter(user=self.request.user)


class TransactionDelete(LoginRequiredMixin, DeleteView):
    model = Transaction
    context_object_name = "transaction"
    template_name = "transaction/transaction_confirm_delete.html"
    success_url = reverse_lazy("transactions")

    def form_valid(self, form):
        group = self.object.installment_group

        if group:
            Transaction.objects.filter(installment_group=group).delete()
            sweetify.toast(
                self.request,
                "Parcelas excluidas com sucesso",
                icon="error",
                button="OK",
                timer=2000,
            )
        else:
            sweetify.toast(
                self.request,
                "Transação excluida com sucesso",
                icon="error",
                button="OK",
                timer=2000,
            )
        return super(TransactionDelete, self).form_valid(form)

    def get_queryset(self):
        base_qs = super(TransactionDelete, self).get_queryset()
        return base_qs.filter(user=self.request.user)
