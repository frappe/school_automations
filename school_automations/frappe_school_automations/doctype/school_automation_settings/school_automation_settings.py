# Copyright (c) 2025, Frappe and contributors
# For license information, please see license.txt

import frappe
from frappe.integrations.doctype.google_drive.google_drive import get_google_drive_object
from frappe.model.document import Document
from googleapiclient.errors import HttpError


class SchoolAutomationSettings(Document):
	def validate(self):
		doc_before_save = self.get_doc_before_save()
		if doc_before_save and doc_before_save.drive_root_folder_name != self.drive_root_folder_name:
			self.drive_root_folder_id = ''


def check_or_create_root_folder_in_google_drive():
	google_drive, _ = get_google_drive_object()
	automation_settings = frappe.get_cached_doc('School Automation Settings')

	if automation_settings.drive_root_folder_id:
		return

	folder = folder_exists_in_drive(google_drive, automation_settings.drive_root_folder_name)
	if not folder:
		folder = create_folder_in_google_drive(google_drive, automation_settings.drive_root_folder_name)

	frappe.db.set_single_value('School Automation Settings', 'drive_root_folder_id', folder.get('id'))
	frappe.db.commit()


def create_folder_in_google_drive(drive, folder_name: str):
	file_metadata = {
		'name': folder_name,
		'mimeType': 'application/vnd.google-apps.folder',
	}

	try:
		folder = drive.files().create(body=file_metadata, fields='id').execute()
		return folder
	except HttpError as e:
		frappe.throw(f'School Automation - Could not create folder in Google Drive - Error Code {e}')


def folder_exists_in_drive(drive, folder_name: str):
	try:
		google_drive_folders = drive.files().list(q="mimeType='application/vnd.google-apps.folder'").execute()
	except HttpError as e:
		frappe.throw(f'School Automation - Could not find folder in Google Drive - Error Code {e}')

	for f in google_drive_folders.get('files'):
		if f.get('name') == folder_name:
			return f
