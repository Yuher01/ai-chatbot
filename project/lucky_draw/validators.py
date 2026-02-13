import re
from typing import Optional, Tuple
from .models import UserDetails


def _extract_field(text: str, label: str) -> Optional[str]:
    pattern = rf'{label}\s*[:=\-]\s*(.+)'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None


def parse_user_details(text: str) -> Tuple[Optional[UserDetails], list[str]]:
    name = _extract_field(text, "name")
    phone = _extract_field(text, "number")
    email = _extract_field(text, "email")

    missing = []
    if not name:
        missing.append("Name")
    if not phone:
        missing.append("Number")
    if not email:
        missing.append("Email")

    if missing:
        return None, missing

    return UserDetails(name=name, phone_number=phone, email=email), []
