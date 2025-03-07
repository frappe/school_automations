frappe.ui.form.on('LMS Batch', {
	refresh(frm) {
		const recordings_url = frm.doc.custom_recordings_url;
		if (recordings_url) {
			frm.add_web_link(recordings_url, "View Recordings");
		}
	}
})
