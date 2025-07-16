// Copyright (c) 2025, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("School Automation Settings", {
	refresh(frm) {
		const root_folder_id = frm.doc.drive_root_folder_id;

		if (root_folder_id) {
			frm.add_web_link(
				`https://drive.google.com/drive/folders/${root_folder_id}`,
				"View Drive Folder"
			);
		}
	},
	authorize_google_drive_access: function (frm) {
		frappe.db.get_single_value("Google Drive", "refresh_token").then((value) => {
			if (!value) {
				frappe.call({
					method: "offsite_backups.offsite_backups.doctype.google_drive.google_drive.authorize_access",
					args: {
						reauthorize: frm.doc.authorization_code ? 1 : 0,
					},
					callback: function (r) {
						if (!r.exc) {
							window.open(r.message.url);
						}
					},
				});
			} else {
				frappe.show_alert("Google Drive is already connected!");
			}
		});

	},
});
