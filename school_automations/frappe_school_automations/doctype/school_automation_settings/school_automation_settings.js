// Copyright (c) 2025, Frappe and contributors
// For license information, please see license.txt

frappe.ui.form.on("School Automation Settings", {
	refresh(frm) {

	},
	authorize_google_drive_access: function (frm) {
		frappe.db.get_single_value("Google Drive", "refresh_token").then((value) => {
			if (!value) {
				frappe.call({
					method: "frappe.integrations.doctype.google_drive.google_drive.authorize_access",
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
