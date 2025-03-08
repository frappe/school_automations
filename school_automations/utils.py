import io
import os

import frappe
import frappe.utils
import requests
from apiclient.http import MediaFileUpload
from frappe.integrations.doctype.google_drive.google_drive import get_google_drive_object
from frappe.utils import get_bench_path
from googleapiclient.errors import HttpError
from lms.lms.doctype.lms_batch.lms_batch import authenticate

ZOOM_API_BASE_PATH = 'https://api.zoom.us/v2'


def upload_zoom_recording_to_drive(class_id: str):
	batch_name, join_url, already_uploaded = frappe.db.get_value(
		'LMS Live Class', class_id, ['batch_name', 'join_url', 'custom_recording_uploaded']
	)

	if already_uploaded:
		return

	check_or_create_root_folder_in_google_drive()

	meeting_id = int(join_url.split('/')[-1])
	url = f'{ZOOM_API_BASE_PATH}/meetings/{meeting_id}/recordings'
	headers = {
		'Authorization': 'Bearer ' + authenticate(),
		'content-type': 'application/json',
	}
	response = requests.get(url, headers=headers)
	data = response.json()

	recording_files = data.get('recording_files')
	if not recording_files:
		frappe.throw('Cloud recording not available yet!')

	upload_count = 0
	for f in recording_files:
		if f['recording_type'] == 'shared_screen_with_speaker_view':
			# download this recording
			download_url = f['download_url']
			file_extension = f['file_extension']
			upload_count += 1

			if upload_count > 1:
				file_name = f"{data['topic']}.{file_extension.lower()}"
			else:
				file_name = f"{data['topic']} - Part {upload_count}.{file_extension.lower()}"

			file_doc = download_and_create_file_doc(download_url, file_name)
			batch_folder = create_batch_folder_if_not_exists_in_google_drive(class_id)

			uploaded_file = upload_to_google_drive(file_doc.file_url, batch_folder.get('id'))
			frappe.get_doc(
				{
					'doctype': 'Recording Drive Upload Log',
					'live_class': class_id,
					'drive_link': f"https://drive.google.com/file/d/{uploaded_file.get('id')}/view",
				}
			).insert().submit()

			recording_id = f.get('id')

			frappe.enqueue(
				'school_automations.utils.cleanup_recording',
				queue='long',
				meeting_id=meeting_id,
				file_name=file_doc.name,
				recording_id=recording_id,
				enqueue_after_commit=True,
			)


def download_and_create_file_doc(download_url, file_name):
	headers = {
		'Authorization': 'Bearer ' + authenticate(),
		'content-type': 'application/json',
	}
	response = requests.get(download_url, headers=headers)
	binary_data = io.BytesIO(response.content)
	hex_data = binary_data.getvalue()

	# save to Frappe's file system
	recording_file = frappe.get_doc(
		{
			'doctype': 'File',
			'file_name': file_name,
			'content': hex_data,
		}
	).save()

	return recording_file


def upload_to_google_drive(file_url: str, folder_id: str):
	google_drive, _ = get_google_drive_object()

	file_path = f'{get_bench_path()}/sites/{frappe.local.site}/public/{file_url}'
	file_metadata = {'name': os.path.basename(file_path), 'parents': [folder_id]}
	media = MediaFileUpload(file_path, mimetype='video/mp4', resumable=True)
	uploaded_file = google_drive.files().create(body=file_metadata, media_body=media, fields='id').execute()

	file_id = uploaded_file.get('id')
	permission = {'type': 'anyone', 'role': 'reader'}
	google_drive.permissions().create(fileId=file_id, body=permission).execute()
	return uploaded_file


# Maybe TODO
@frappe.whitelist(allow_guest=True)
def handle_zoom_webhook():
	pass


def check_or_create_root_folder_in_google_drive():
	google_drive, _ = get_google_drive_object()
	automation_settings = frappe.get_cached_doc('School Automation Settings')

	if automation_settings.drive_root_folder_id:
		return

	folder = create_folder_if_not_exists(google_drive, automation_settings.drive_root_folder_name)

	frappe.db.set_single_value('School Automation Settings', 'drive_root_folder_id', folder.get('id'))
	frappe.db.commit()


def create_batch_folder_if_not_exists_in_google_drive(class_id: str):
	batch_name, batch_title, recording_url = frappe.db.get_value(
		'LMS Live Class', class_id, ['batch_name', 'batch_name.title', 'batch_name.custom_recordings_url']
	)
	root_folder_id = frappe.get_cached_doc('School Automation Settings').drive_root_folder_id
	google_drive, _ = get_google_drive_object()
	folder = create_folder_if_not_exists(google_drive, batch_title, root_folder_id)

	if not recording_url:
		frappe.db.set_value(
			'LMS Batch',
			batch_name,
			'custom_recordings_url',
			f"https://drive.google.com/drive/folders/{folder.get('id')}",
		)
	return folder


def create_folder_if_not_exists(drive, folder_name, parent_folder_id: str = None):
	folder = folder_exists_in_drive(drive, folder_name, parent_folder_id)
	if not folder:
		folder = create_folder_in_google_drive(drive, folder_name, parent_folder_id)
	return folder


def create_folder_in_google_drive(drive, folder_name: str, parent_folder_id: str = None):
	file_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder'}

	if parent_folder_id:
		file_metadata['parents'] = [parent_folder_id]

	try:
		folder = drive.files().create(body=file_metadata, fields='id').execute()
		permission = {'type': 'anyone', 'role': 'reader'}
		drive.permissions().create(fileId=folder.get('id'), body=permission).execute()
		return folder
	except HttpError as e:
		frappe.throw(f'School Automation - Could not create folder {folder} in Google Drive - Error Code {e}')


def folder_exists_in_drive(drive, folder_name: str, parent_folder_id: str = None):
	query = "mimeType='application/vnd.google-apps.folder'"
	if parent_folder_id:
		query += f" and '{parent_folder_id}' in parents"

	try:
		google_drive_folders = drive.files().list(q=query, spaces='drive', fields='files(id, name)').execute()
	except HttpError as e:
		frappe.throw(f'School Automation - Could not find folder in Google Drive - Error Code {e}')

	for f in google_drive_folders.get('files'):
		if f.get('name') == folder_name:
			return f


def cleanup_recording(meeting_id: int, recording_id: str, file_name: str):
	"""Deletes recordings of this class from school site and Zoom"""
	url = f'{ZOOM_API_BASE_PATH}/meetings/{meeting_id}/recordings/{recording_id}'
	headers = {
		'Authorization': 'Bearer ' + authenticate(),
		'content-type': 'application/json',
	}
	requests.delete(url, headers=headers)

	# Delete the local copy
	frappe.delete_doc('File', file_name, delete_permanently=True, force=True)


def pull_recordings_for_yesterdays_live_classes():
	today = frappe.utils.today()
	yesterday = frappe.utils.add_days(today, -1)

	classes = frappe.db.get_all(
		'LMS Live Class', filters={'custom_recording_uploaded': False, 'date': yesterday}, pluck='name'
	)

	for class_id in classes:
		frappe.enqueue(
			'school_automations.utils.upload_zoom_recording_to_drive', queue='long', class_id=class_id
		)


@frappe.whitelist()
def queue_recording_download(class_id: str):
	frappe.enqueue(upload_zoom_recording_to_drive, queue='long', class_id=class_id)
