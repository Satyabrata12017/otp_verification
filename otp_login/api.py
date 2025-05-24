import frappe
import random
from frappe.utils import now_datetime
from frappe import whitelist

@whitelist(allow_guest=True)
def generate(email):
    otp = str(random.randint(100000, 999999))

    doc = frappe.new_doc("OTP Verification")
    doc.email = email
    doc.otp = otp
    doc.insert(ignore_permissions=True)

    frappe.sendmail(
        recipients=email,
        subject="Your OTP Code",
        message=f"Your OTP is: <b>{otp}</b><br>This OTP expires in 5 minutes."
    )

    return {"message": "OTP sent successfully"}

@whitelist(allow_guest=True)
def verify(email, otp):
    docs = frappe.get_all("OTP Verification",
                          filters={"email": email, "otp": otp, "is_verified": 0},
                          fields=["name", "expires_on"])
    if not docs:
        return {"status": "failed", "reason": "Invalid OTP"}

    if now_datetime() > docs[0]["expires_on"]:
        return {"status": "failed", "reason": "OTP expired"}

    frappe.db.set_value("OTP Verification", docs[0]["name"], "is_verified", 1)
    return {"status": "success"}
