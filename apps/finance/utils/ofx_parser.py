from decimal import Decimal
from datetime import date, datetime

import ofxparse


def parse_ofx(file_path):
    with open(file_path) as f:
        ofx = ofxparse.OfxParser.parse(f)

    result = []
    for acc in ofx.accounts:
        for txn in acc.statement.transactions:
            amount = abs(Decimal(str(txn.amount)))
            tipo = "C" if Decimal(str(txn.amount)) > 0 else "D"

            if isinstance(txn.date, datetime):
                txn_date = txn.date.date()
            elif isinstance(txn.date, date):
                txn_date = txn.date
            else:
                txn_date = date.today()

            result.append(
                {
                    "bank_fit_id": txn.id,
                    "transaction_date": txn_date,
                    "description": txn.payee or txn.memo or "",
                    "transaction_value": amount,
                    "type": tipo,
                    "bank_account_id": acc.account_id,
                    "bank_routing": acc.routing_number,
                }
            )
    return result
