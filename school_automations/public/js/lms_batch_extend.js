frappe.ui.form.on('LMS Batch', {
	refresh(frm) {
		if (frm.doc.custom_recordings_url) {
			frm.add_web_link(frm.doc.custom_recordings_url, "View Recordings");
		}
	}
})
