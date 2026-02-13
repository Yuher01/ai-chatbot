from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


class LuckyDrawStep(Enum):
    INACTIVE = "inactive"
    AWAITING_RECEIPT = "awaiting_receipt"
    AWAITING_DETAILS = "awaiting_details"
    CONFIRMING_EXIT = "confirming_exit"


class EntryStatus(Enum):
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"
    APPLIED = "applied"


@dataclass
class ReceiptData:
    receipt_no: int
    amount: float
    confidence_level: float


@dataclass
class UserDetails:
    name: str
    phone_number: str
    email: str


@dataclass
class FlowState:
    step: LuckyDrawStep = LuckyDrawStep.INACTIVE
    receipt: Optional[ReceiptData] = None
    previous_step: Optional[LuckyDrawStep] = None
    retry_count: int = 0
    max_retries: int = 3

    def reset(self):
        self.step = LuckyDrawStep.INACTIVE
        self.receipt = None
        self.previous_step = None
        self.retry_count = 0
