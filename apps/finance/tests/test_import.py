from datetime import date
from decimal import Decimal

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.finance.models.imported_transaction import ImportedTransaction
from apps.finance.models.transaction import Transaction
from apps.finance.tests.base import BaseFinanceTestCase

OFX_SAMPLE = b"""OFXHEADER:100
DATA:OFXSGML
VERSION:102
SECURITY:NONE
ENCODING:USASCII
CHARSET:1252
COMPRESSION:NONE
OLDFILEUID:NONE
NEWFILEUID:NONE

<OFX>
<BANKMSGSRSV1>
<STMTTRNRS>
<TRNUID>1
<STATUS>
<CODE>0
<SEVERITY>INFO
</STATUS>
<STMTRS>
<BANKTRANLIST>
<DTSTART>20260801000000
<DTEND>20260831000000
<STMTTRN>
<TRNTYPE>DEBIT
<DTPOSTED>20260815000000
<TRNAMT>-150.75
<FITID>TX001
<NAME>MERCADO ABC
<MEMO>Compra mercado
</STMTTRN>
<STMTTRN>
<TRNTYPE>CREDIT
<DTPOSTED>20260820000000
<TRNAMT>2500.00
<FITID>TX002
<NAME>SALARIO
<MEMO>Pagamento salario
</STMTTRN>
</BANKTRANLIST>
</STMTRS>
</STMTTRNRS>
</BANKMSGSRSV1>
</OFX>
"""


class ImportUploadTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.url = reverse("import-upload")

    def _upload(self, fit_id="TX001", amount="-150.75"):
        content = OFX_SAMPLE.replace(
            b"TX001", fit_id.encode()
        ).replace(b"-150.75", amount.encode())
        return self.client.post(
            self.url,
            {
                "account": self.checking_account.pk,
                "file": SimpleUploadedFile("extrato.ofx", content),
            },
        )

    def test_upload_creates_imported_transactions(self):
        response = self._upload()

        self.assertRedirects(response, reverse("import-reconciliation"))
        imported = ImportedTransaction.objects.order_by("bank_fit_id")
        self.assertEqual(imported.count(), 2)

        debit = imported.get(bank_fit_id="TX001")
        self.assertEqual(debit.type, "D")
        self.assertEqual(debit.transaction_value, Decimal("150.75"))
        self.assertEqual(debit.status, "pending")
        self.assertEqual(debit.account_id, self.checking_account.pk)
        self.assertEqual(debit.transaction_date, date(2026, 8, 15))

        credit = imported.get(bank_fit_id="TX002")
        self.assertEqual(credit.type, "C")

    def test_reupload_does_not_duplicate(self):
        self._upload()
        self._upload()

        self.assertEqual(ImportedTransaction.objects.count(), 2)

    def test_import_requires_login(self):
        self.client.logout()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 302)


class ReconciliationTests(BaseFinanceTestCase):
    def setUp(self):
        super().setUp()
        self.imported = ImportedTransaction.objects.create(
            user=self.user,
            account=self.checking_account,
            bank_fit_id="TX001",
            transaction_date=date(2026, 8, 15),
            description="MERCADO ABC",
            transaction_value=Decimal("150.75"),
            type="D",
        )

    def _existing_transaction(self):
        return self._create_transaction(
            value="150.75",
            type="D",
            is_paid=True,
            description="Compra mercado",
        )

    def test_match_links_to_existing_transaction(self):
        existing = self._existing_transaction()

        self.client.post(
            reverse("import-match", args=[self.imported.pk]),
            {"transaction_id": existing.pk},
        )

        self.imported.refresh_from_db()
        self.assertEqual(self.imported.status, "matched")
        self.assertEqual(self.imported.matched_transaction_id, existing.pk)

    def test_accept_creates_transaction_and_marks_imported(self):
        child_category = self._create_category(
            name="Supermercado", parent=self.expense_category
        )

        self.client.post(
            reverse("import-accept", args=[self.imported.pk]),
            {"category_id": child_category.pk},
        )

        self.imported.refresh_from_db()
        self.assertEqual(self.imported.status, "imported")

        created = Transaction.objects.get(description="MERCADO ABC")
        self.assertEqual(created.account_id, self.checking_account.pk)
        self.assertEqual(created.category_id, child_category.pk)
        self.assertEqual(created.transaction_value, Decimal("150.75"))
        self.assertTrue(created.is_paid)

    def test_accept_requires_category(self):
        self.client.post(reverse("import-accept", args=[self.imported.pk]))

        self.imported.refresh_from_db()
        self.assertEqual(self.imported.status, "pending")
        self.assertFalse(Transaction.objects.exists())

    def test_ignore_marks_ignored(self):
        self.client.post(reverse("import-ignore", args=[self.imported.pk]))

        self.imported.refresh_from_db()
        self.assertEqual(self.imported.status, "ignored")
        self.assertFalse(Transaction.objects.exists())

    def test_cannot_access_other_users_import(self):
        foreign = ImportedTransaction.objects.create(
            user=self.other_user,
            account=self._create_account(user=self.other_user),
            bank_fit_id="TX-OTHER",
            transaction_date=date(2026, 8, 15),
            description="De outro usuário",
            transaction_value=Decimal("10"),
            type="D",
        )

        for url_name in ("import-match", "import-accept", "import-ignore"):
            response = self.client.post(reverse(url_name, args=[foreign.pk]), {})
            self.assertEqual(response.status_code, 404)

        self.client.logout()
