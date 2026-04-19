"""Guardrails — PII, injection, scope detection."""
import re

_PII = {
    "email":       r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b",
    "phone":       r"\b[6-9]\d{9}\b",
    "aadhaar":     r"\b\d{4}\s?\d{4}\s?\d{4}\b",
    "pan":         r"\b[A-Z]{5}[0-9]{4}[A-Z]\b",
    "credit_card": r"\b(?:\d[ -]?){13,16}\b",
    "ssn":         r"\b\d{3}-\d{2}-\d{4}\b",
}
_INJECTION = [r"(?i)(ignore previous|forget instructions|you are now|act as|jailbreak|override|bypass|disregard)"]
_OOS = [
    r"(?i)\b(hack|exploit|ddos|malware|ransomware)\b",
    r"(?i)\b(stock tip|investment advice|buy sell|crypto trading)\b",
    r"(?i)\b(password|secret key|api key)\b.*\b(show|tell|give|what is)\b",
]

def mask_pii(text: str) -> tuple[str, list[str]]:
    found, masked = [], text
    for t, p in _PII.items():
        if re.search(p, masked):
            found.append(t)
            masked = re.sub(p, f"[{t.upper()}_REDACTED]", masked)
    return masked, found

def validate(query: str) -> tuple[bool, str, str]:
    if not query or len(query.strip()) < 3:
        return False, "Query too short.", query
    for p in _INJECTION:
        if re.search(p, query):
            return False, "Potential prompt injection blocked.", query
    for p in _OOS:
        if re.search(p, query):
            return False, "Query is outside the enterprise assistant scope.", query
    cleaned, _ = mask_pii(query)
    return True, "", cleaned

def sanitize(text: str) -> str:
    masked, _ = mask_pii(text)
    return masked
