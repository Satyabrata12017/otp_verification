import frappe
import random
from frappe import _
from frappe.utils import now_datetime, add_to_date


@frappe.whitelist(allow_guest=True)
def send_otp(email):
    if not email:
        frappe.throw(_("Email is required"))

    otp = str(random.randint(100000, 999999))
    expires_on = add_to_date(now_datetime(), minutes=5)

    # Save OTP in DB
    doc = frappe.new_doc("OTP Verification")
    doc.email = email
    doc.otp = otp
    doc.expires_on = expires_on
    doc.insert(ignore_permissions=True)

    # Cache OTP for quick access
    frappe.cache().set_value(f"otp:{email}", otp, expires_in_sec=300)

    # For production, use Email/SMS to send OTP
    # frappe.sendmail(recipients=email, subject="Your OTP", message=f"Your OTP is {otp}")

    return {"message": "OTP sent."}


@frappe.whitelist(allow_guest=True)
def verify_otp(email, otp):
    if not email or not otp:
        frappe.throw(_("Email and OTP are required"))

    # Get OTP from cache
    cached_otp = frappe.cache().get_value(f"otp:{email}")
    if not cached_otp:
        return {"message": "OTP expired or not found."}

    if str(otp) != str(cached_otp):
        return {"message": "Invalid OTP."}

    # Check if OTP has expired in DB
    otp_doc = frappe.get_all(
        "OTP Verification",
        filters={"email": email, "otp": otp},
        fields=["name", "expires_on"],
        order_by="creation desc",
        limit=1
    )

    if not otp_doc:
        return {"message": "OTP not found."}

    if otp_doc[0].expires_on < now_datetime():
        return {"message": "OTP has expired."}

    # OTP is valid
    frappe.cache().delete_value(f"otp:{email}")
    return {"message": "OTP verified successfully."}
