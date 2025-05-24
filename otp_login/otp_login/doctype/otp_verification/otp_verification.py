# Copyright (c) 2025, satya and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.utils import now_datetime, add_to_date

class OTPVerification(Document):
	pass
    
def before_insert(self,method=None):
	self.expires_on = add_to_date(now_datetime(), minutes=5)
	self.is_verified = 0
