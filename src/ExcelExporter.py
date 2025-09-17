import pandas as pd
import os

class FirestoreExcelExporter:
	def __init__(self, db, output_dir="exports"):
		self.db = db
		self.output_dir = output_dir
		os.makedirs(self.output_dir, exist_ok=True)

	def _get_event_dataframe(self, event_ref, registration_type):
		rows = []
		registrations_ref = event_ref.collection("registrations").stream()

		for reg in registrations_ref:
			reg_data = reg.to_dict()

			if registration_type == "individual" and "participants" in reg_data:
				team_name = reg_data.get("team_name", "")
				for p in reg_data.get("participants", []):
					rows.append({
						"team_name": team_name,
						"name": p.get("name", ""),
						"email_id": p.get("email_id", ""),
						"phone_no": p.get("phone_no", "")
					})

			elif registration_type == "institution":
				delegate = {
					"delegate_head_name": reg_data.get("delegate_head", ""),
					"delegate_email": reg_data.get("delegate_email_id", ""),
					"delegate_phone": reg_data.get("delegate_phone_no", ""),
					"institution_name": reg_data.get("institution_name", "")
				}
				for team in reg_data.get("teams", []):
					team_name = team.get("team_name", "")
					for p in team.get("participants", []):
						rows.append({
							**delegate,
							"name": p.get("name", ""),
							"phone": p.get("phone_no", ""),
							"reg_no": p.get("reg_no", "")
						})
		if rows:
			return pd.DataFrame(rows)
		return None

	def _get_all_events(self, registration_type):
		events_list = []
		base_ref = self.db.collection("registrations").document(registration_type).collection("clubs")
		club_ids = [c.id for c in base_ref.list_documents()]

		for club_id in club_ids:
			club_ref = base_ref.document(club_id)
			event_ids = [e.id for e in club_ref.collection("events").list_documents()]

			for event_id in event_ids:
				event_ref = club_ref.collection("events").document(event_id)
				event_data = event_ref.get().to_dict() or {}
				event_name = event_data.get("event_name", event_id)
				events_list.append((event_name, club_id, event_ref))

		return events_list

	def export_events_to_excel(self, registration_type):
		"""
		Export all events for a registration type into one Excel file,
		with one sheet per event.
		"""
		output_file = os.path.join(self.output_dir, f"{registration_type}_registrations.xlsx")
		sheet_name_count = {}

		with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
			events = self._get_all_events(registration_type)
			for event_name, club_id, event_ref in events:
				df = self._get_event_dataframe(event_ref, registration_type)
				if df is not None:
					# Make human-readable sheet name
					base_name = f"{event_name} {club_id}".replace("/", "_")[:31]
					count = sheet_name_count.get(base_name, 0)
					sheet_name_count[base_name] = count + 1
					sheet_name = f"{base_name}_{count}" if count > 0 else base_name
					sheet_name = sheet_name[:31]
					df.to_excel(writer, sheet_name=sheet_name, index=False)
					print(f"Added sheet: {sheet_name}")

		print(f"All {registration_type} events exported to {output_file}")

	def export_all_events(self):
		self.export_events_to_excel("individual")
		self.export_events_to_excel("institution")
