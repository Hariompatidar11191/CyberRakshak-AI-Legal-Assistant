
import re

EMERGENCY_KEYWORDS = [
    "money stolen",
    "money deducted",
    "unauthorized transaction",
    "unauthorised transaction",
    "bank fraud",
    "upi fraud",
    "upi scam",
    "account hacked",
    "otp fraud",
    "debit card fraud",
    "credit card fraud",
    "online banking fraud",
    "cyber financial fraud",
    "पैसे कट गए",
    "पैसे चोरी",
    "बैंक से पैसे निकल गए",
    "यूपीआई धोखाधड़ी",
    "ओटीपी धोखाधड़ी",
    "खाते से पैसे निकल गए"
]


def detect_emergency(message: str) -> bool:

    message = re.sub(
        r"\s+",
        " ",
        message.lower()
    ).strip()

    return any(
        keyword in message
        for keyword in EMERGENCY_KEYWORDS
    )
