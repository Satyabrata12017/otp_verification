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
    doc.used_for = "Email Verification"
    doc.expires_on = expires_on
    doc.insert(ignore_permissions=True)

    # Cache OTP for quick access
    frappe.cache().set_value(f"otp:{email}", otp, expires_in_sec=300)

    # Try to get subject & message from Notification
    notification = frappe.get_all(
        "Notification",
        filters={
            "enabled": 1,
            "document_type": "OTP Verification",
        },
        fields=["name", "subject", "message"],
        limit=1
    )

    if notification:
        notif = notification[0]
        subject = frappe.render_template(notif.subject, {"doc": doc})
        message = frappe.render_template(notif.message, {"doc": doc})
    else:
        # Fallback
        subject = "Your OTP"
        message = f"Your OTP is <b>{otp}</b>. It is valid for 5 minutes."

    # Send OTP via email
    frappe.sendmail(
        recipients=email,
        subject=subject,
        message=message
    )

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
        filters={"email": email, "otp": otp,"used_for":"Email Verification"},
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



import random
import string
from frappe.utils import now_datetime, add_to_date

OTP_EXPIRY_MINUTES = 5

def generate_otp():
    return ''.join(random.choices(string.digits, k=6))

@frappe.whitelist(allow_guest=True)
def send_signup_otp(email):
    otp = generate_otp()
    expiry = add_to_date(now_datetime(), minutes=OTP_EXPIRY_MINUTES)

    # Optional: Remove previous OTP
    frappe.db.delete("OTP Verification", {"email": email, "used_for": "Sign Up"})

    # Create OTP Verification doc
    doc = frappe.get_doc({
        "doctype": "OTP Verification",
        "email": email,
        "otp": otp,
        "used_for": "Sign Up",
        "expires_on": expiry,
        "is_verified": 0
    })
    doc.insert(ignore_permissions=True)

    # Fetch Notification template
    notification = frappe.get_all(
        "Notification",
        filters={
            "enabled": 1,
            "document_type": "OTP Verification"
        },
        fields=["name", "subject", "message"],
        limit=1
    )

    if notification:
        notif = notification[0]
        subject = frappe.render_template(notif.subject, {"doc": doc})
        message = frappe.render_template(notif.message, {"doc": doc})
    else:
        # Fallback message if no notification is set
        subject = "Your Signup OTP"
        message = f"Your OTP is <b>{otp}</b>. It is valid for {OTP_EXPIRY_MINUTES} minutes."

    # Send the email
    frappe.sendmail(
        recipients=email,
        subject=subject,
        message=message
    )

    return {"message": {"status": "success", "message": "OTP sent"}}


@frappe.whitelist(allow_guest=True)
def verify_signup_otp(email, otp):
    record = frappe.db.get_value("OTP Verification", {"email": email, "otp": otp, "is_verified": 0,"used_for":"Sign Up"}, ["name", "expires_on"])

    if not record:
        return {"message": {"status": "failed", "message": "Invalid or expired OTP"}}

    name, expiry = record
    if now_datetime() > expiry:
        return {"message": {"status": "failed", "message": "OTP expired"}}

    frappe.db.set_value("OTP Verification", name, "is_verified", 1)
    return {"message": {"status": "success", "message": "OTP verified"}}

