from .models import ReceiptData
from .database import LuckyDrawDB


class ReceiptProcessor:

    def __init__(self, db: LuckyDrawDB):
        self.db = db

    def process(self) -> ReceiptData:
        next_no = self.db.get_max_receipt_no() + 1
        return ReceiptData(
            receipt_no=next_no,
            amount=25.00,
            confidence_level=90.0,
        )
