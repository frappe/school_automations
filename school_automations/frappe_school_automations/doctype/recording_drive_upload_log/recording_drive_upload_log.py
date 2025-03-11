# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RecordingDriveUploadLog(Document):
	def on_submit(self):
		frappe.db.set_value(
			'LMS Live Class',
			self.live_class,
			{'custom_recording_uploaded': True}
		)
