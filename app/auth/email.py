# Email sending functionality
def send_verification_email(email: str, code: str):
    """Send verification email (MVP: log to console)"""
    print(f"[EMAIL VERIFICATION] To: {email}")
    print(f"[EMAIL VERIFICATION] Code: {code}")
    print(f"[EMAIL VERIFICATION] This code expires in 24 hours")
    # TODO: Integrate real email service (SendGrid/Mailgun) in production
