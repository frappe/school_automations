frappe.ui.form.on('LMS Live Class', {
	refresh(frm) {
		const is_already_uploaded = frm.doc.custom_recording_uploaded;

		if (!is_already_uploaded) {
			const button = frm.add_custom_button("Upload Recording to Google Drive", () => {
				frappe.call({
					method: "school_automations.utils.queue_recording_download",
					args: {
						class_id: frm.doc.name
					},
					btn: button
				}).then(() => {
					frappe.show_alert("Meeting will be uploaded soon! Check Drive Upload Log for more.")
				})
			})
		}
	}
})
