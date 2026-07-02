import sweetify
from datetime import date
from calendar import monthrange

from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView, CreateView, UpdateView

from apps.finance.forms.transaction_forms import TransactionForm
from apps.finance.models.account import Account
from apps.finance.models.transaction import Transaction


class TransactionList(LoginRequiredMixin, ListView):
    model = TransactionForm
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
            user=self.request.user, transaction_date__range=[start_date, end_date]
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

    def form_valid(self, form):
        form.instance.user = self.request.user
        sweetify.toast(
            self.request,
            "Transação incluida com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return super(TransactionCreate, self).form_valid(form)


class TransactionUpdate(LoginRequiredMixin, UpdateView):
    model = Transaction
    template_name = "transaction/transaction_form.html"
    form_class = TransactionForm
    success_url = reverse_lazy("transactions")

    def get_initial(self):
        return {"user": self.request.user}

    def form_valid(self, form):
        sweetify.toast(
            self.request,
            "Transação alterada com sucesso",
            icon="success",
            button="OK",
            timer=2000,
        )
        return super(TransactionUpdate, self).form_valid(form)

    def get_queryset(self):
        base_qs = super(TransactionUpdate, self).get_queryset()
        return base_qs.filter(user=self.request.user)


class TransactionDelete(LoginRequiredMixin, DeleteView):
    model = Transaction
    context_object_name = "transaction"
    template_name = "transaction/transaction_confirm_delete.html"
    success_url = reverse_lazy("transactions")

    def form_valid(self, form):
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
