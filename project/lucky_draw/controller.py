from .models import FlowState, LuckyDrawStep, EntryStatus
from .database import LuckyDrawDB
from .receipt_processor import ReceiptProcessor
from .validators import parse_user_details
from .intent_detector import IntentDetector
from . import prompts

EXIT_CONFIRMATIONS = {"yes", "y", "yeah", "yep", "sure", "ok", "okay", "ya", "yup"}


class LuckyDrawController:

    def __init__(self, db_path: str):
        self.db = LuckyDrawDB(db_path)
        self.processor = ReceiptProcessor(self.db)
        self.state = FlowState()
        self.intent_detector = IntentDetector()

    @property
    def is_active(self) -> bool:
        return self.state.step != LuckyDrawStep.INACTIVE

    def handle(self, message: str) -> str | None:
        text = message.strip()

        if not self.is_active:
            if self.intent_detector.is_lucky_draw_intent(text):
                self.state.step = LuckyDrawStep.AWAITING_RECEIPT
                return prompts.WELCOME
            return None

        step = self.state.step

        if step == LuckyDrawStep.AWAITING_RECEIPT:
            return self._handle_awaiting_receipt(text)
        if step == LuckyDrawStep.AWAITING_DETAILS:
            return self._handle_awaiting_details(text)
        if step == LuckyDrawStep.CONFIRMING_EXIT:
            return self._handle_confirming_exit(text)

        return None

    def _handle_awaiting_receipt(self, text: str) -> str:
        if text.lower() == "image":
            receipt = self.processor.process()
            self.state.receipt = receipt
            self.state.step = LuckyDrawStep.AWAITING_DETAILS
            return prompts.RECEIPT_PROCESSED.format(
                receipt_no=receipt.receipt_no,
                amount=receipt.amount,
                confidence_level=receipt.confidence_level,
            )

        self.state.previous_step = LuckyDrawStep.AWAITING_RECEIPT
        self.state.step = LuckyDrawStep.CONFIRMING_EXIT
        return prompts.CONFIRM_EXIT

    def _handle_awaiting_details(self, text: str) -> str:
        details, missing = parse_user_details(text)

        if details is None:
            if len(missing) == 3:
                self.state.previous_step = LuckyDrawStep.AWAITING_DETAILS
                self.state.step = LuckyDrawStep.CONFIRMING_EXIT
                return prompts.CONFIRM_EXIT

            self.state.retry_count += 1
            if self.state.retry_count >= self.state.max_retries:
                self.state.reset()
                return prompts.MAX_RETRIES_EXCEEDED

            remaining = self.state.max_retries - self.state.retry_count
            return prompts.RETRY_DETAILS.format(remaining=remaining)

        return self._process_entry(details)

    def _process_entry(self, details) -> str:
        receipt = self.state.receipt

        existing = self.db.find_approved_by_phone(details.phone_number)
        if existing:
            self.db.insert_entry(
                receipt_no=receipt.receipt_no,
                name=details.name,
                phone_number=details.phone_number,
                email=details.email,
                transaction_amount=receipt.amount,
                confidence_level=receipt.confidence_level,
                status=EntryStatus.APPLIED,
            )
            self.state.reset()
            return prompts.DUPLICATE.format(existing_receipt_no=existing["receipt_no"])

        if receipt.amount < 20:
            self.db.insert_entry(
                receipt_no=receipt.receipt_no,
                name=details.name,
                phone_number=details.phone_number,
                email=details.email,
                transaction_amount=receipt.amount,
                confidence_level=receipt.confidence_level,
                status=EntryStatus.REJECTED,
            )
            self.state.reset()
            return prompts.REJECTED_LOW_AMOUNT.format(amount=receipt.amount)

        if receipt.amount >= 20 and receipt.confidence_level >= 90:
            status = EntryStatus.APPROVED
        else:
            status = EntryStatus.PENDING

        self.db.insert_entry(
            receipt_no=receipt.receipt_no,
            name=details.name,
            phone_number=details.phone_number,
            email=details.email,
            transaction_amount=receipt.amount,
            confidence_level=receipt.confidence_level,
            status=status,
        )
        self.state.reset()

        status_display = "Approved" if status == EntryStatus.APPROVED else "Pending Review"
        return prompts.SUCCESS.format(
            receipt_no=receipt.receipt_no,
            status=status_display,
        )

    def _handle_confirming_exit(self, text: str) -> str:
        if text.lower().strip() in EXIT_CONFIRMATIONS:
            self.state.reset()
            return prompts.EXIT_CONFIRMED

        previous = self.state.previous_step
        self.state.step = previous
        self.state.previous_step = None

        if previous == LuckyDrawStep.AWAITING_RECEIPT:
            return prompts.AWAITING_RECEIPT_REMINDER
        if previous == LuckyDrawStep.AWAITING_DETAILS:
            return prompts.AWAITING_DETAILS_REMINDER

        self.state.reset()
        return prompts.EXIT_CONFIRMED
