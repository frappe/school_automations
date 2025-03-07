# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class RecordingDriveUploadLog(Document):
	def on_submit(self):
		frappe.db.set_value("LMS Live Class", self.live_class, {
			"custom_recording_uploaded": True,
			"custom_recording_url": self.drive_link
		})

		try:
			make_announcement_to_batch_students(self.live_class, self.drive_link)
		except Exception:
			frappe.log_error("Unable to make batch announcement for Recording!")


def make_announcement_to_batch_students(class_id: str, recording_link: str):
	from frappe.core.doctype.communication.email import make

	live_class_doc = frappe.get_doc('LMS Live Class', class_id)
	batch_name = live_class_doc.batch_name
	students = frappe.db.get_all('LMS Batch Enrollment', filters={'batch': batch_name}, pluck='member')

	instructor_email = frappe.db.get_all(
		'Course Instructor',
		filters={'parent': batch_name, 'parenttype': 'LMS Batch'},
		fields=['instructor.email as email'],
		pluck='email',
		limit=1,
	)[0]

	content = f"""Hi!

Recording for **{live_class_doc.title}** is now available on this [link]({recording_link}).


Regards,
Team Frappe School
"""

	make(
		'LMS Batch',
		batch_name,
		subject='Live class recording now available!',
		cc=instructor_email,
		send_email=1,
		recipients=students,
		content=frappe.utils.md_to_html(content),
	)
