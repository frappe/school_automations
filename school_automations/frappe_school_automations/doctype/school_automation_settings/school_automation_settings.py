# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class SchoolAutomationSettings(Document):
	def validate(self):
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.drive_root_folder_name != self.drive_root_folder_name:
			self.drive_root_folder_id = ''
