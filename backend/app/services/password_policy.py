"""Rules for a NEW password (registration). Login must not use them: older accounts keep working.

Mirrored on the frontend in `components/auth/password-rules.js` so the form can show each rule
ticking off while the user types; this module is the one that is enforced.
"""

MIN_LENGTH = 12
MAX_LENGTH = 128
MIN_IDENTITY_PART = 3  # shorter e-mail names / usernames would block half of all passwords


def failed_rules(password: str, email: str | None = None, username: str | None = None) -> list[str]:
    """Return the ids of the rules `password` breaks: length, upper, digit, special, identity."""
    failed: list[str] = []
    if len(password) < MIN_LENGTH:
        failed.append("length")
    if not any(char.isupper() for char in password):
        failed.append("upper")
    if not any(char.isdecimal() for char in password):
        failed.append("digit")
    if not any(not char.isalnum() and not char.isspace() for char in password):
        failed.append("special")

    email_name = email.split("@")[0] if email else ""
    parts = [part.lower() for part in (email_name, username) if part]
    lowered = password.lower()
    if any(len(part) >= MIN_IDENTITY_PART and part in lowered for part in parts):
        failed.append("identity")
    return failed
