frappe.ui.form.on('LMS Live Class', {
	refresh(frm) {
		const meeting_id = frm.doc.join_url.split("/").reverse()[0];

		const button = frm.add_custom_button("Upload Recording to Google Drive", () => {
			frappe.call({
				method: "school_automations.utils.queue_recording_download",
				args: {
					meeting_id,
					class_id: frm.doc.name
				},
				btn: button
			}).then(() => {
				frappe.show_alert("Meeting will be uploaded soon! Check Drive Upload Log for more.")
			})
		})
	}
})
