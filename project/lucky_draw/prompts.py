WELCOME = (
    "🎉 **Welcome to the Lucky Draw!**\n\n"
    "To enter, please submit your receipt by typing **image**."
)

RECEIPT_PROCESSED = (
    "✅ **Receipt Processed!**\n\n"
    "- **Receipt No:** {receipt_no}\n"
    "- **Amount:** ${amount:.2f}\n"
    "- **Confidence Level:** {confidence_level:.0f}%\n\n"
    "Please provide your details in the following format:\n\n"
    "```\n"
    "Name: [your full name]\n"
    "Number: [your phone number]\n"
    "Email: [your email address]\n"
    "```"
)

SUCCESS = (
    "🎉 **Your lucky draw entry has been submitted successfully!**\n\n"
    "- **Receipt No:** {receipt_no}\n"
    "- **Status:** {status}\n\n"
    "Good luck! We will contact you via your phone number or email if you've won!"
)

DUPLICATE = (
    "⚠️ We found an existing approved entry under your phone number "
    "(Receipt No: {existing_receipt_no}). Each person can only enter the lucky draw once."
)

REJECTED_LOW_AMOUNT = (
    "❌ Unfortunately, your receipt amount (${amount:.2f}) does not meet the minimum "
    "requirement of $20.00 for the lucky draw. You are welcome to try again with a "
    "qualifying receipt!"
)

CONFIRM_EXIT = (
    "It looks like your message isn't related to the lucky draw.\n"
    "Would you like to exit the lucky draw entry? (yes/no)"
)

EXIT_CONFIRMED = (
    "No problem! You've exited the lucky draw entry.\n\n"
    "I'm a document assistant — feel free to ask me anything about the available documents!"
)

RETRY_DETAILS = (
    "⚠️ Some details are missing or invalid. Please provide all three fields in the following format:\n\n"
    "```\n"
    "Name: [your full name]\n"
    "Number: [your phone number]\n"
    "Email: [your email address]\n"
    "```\n\n"
    "({remaining} attempt(s) remaining)"
)

MAX_RETRIES_EXCEEDED = (
    "❌ Too many invalid attempts. The lucky draw entry has been cancelled.\n"
    "You can start again anytime by mentioning the lucky draw!"
)

AWAITING_RECEIPT_REMINDER = (
    "Please submit your receipt by typing **image** to continue with the lucky draw entry."
)

AWAITING_DETAILS_REMINDER = (
    "Please provide your details in the following format to continue:\n\n"
    "```\n"
    "Name: [your full name]\n"
    "Number: [your phone number]\n"
    "Email: [your email address]\n"
    "```"
)
