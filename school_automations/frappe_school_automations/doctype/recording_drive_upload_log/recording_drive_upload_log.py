# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RecordingDriveUploadLog(Document):
	def on_submit(self):
		live_class = frappe.get_doc('LMS Live Class', self.live_class)
		live_class.custom_recording_uploaded = True
		live_class.append("custom_recordings", {
			"log": self.name,
			"drive_url": self.drive_link
		})
		live_class.save()
