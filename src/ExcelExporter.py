import pandas as pd
import os

class FirestoreExcelExporter:
    def __init__(self, db, output_dir="exports"):
        """
        db: a Firestore client instance
        output_dir: folder where Excel files will be saved
        """
        self.db = db
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def _export_event(self, event_ref, event_name):
        """
        Export all registrations for a single event into an Excel file.
        Handles both individual and institution registration types.
        """
        registrations_ref = event_ref.collection("registrations")
        registrations = registrations_ref.stream()
        rows = []

        for reg in registrations:
            reg_data = reg.to_dict()

            # Individual registrations
            if "participants" in reg_data:
                team_name = reg_data.get("team_name", "")
                for p in reg_data.get("participants", []):
                    rows.append({
                        "type": "individual",
                        "team_name": team_name,
                        "name": p.get("name", ""),
                        "email_id": p.get("email_id", ""),
                        "phone_no": p.get("phone_no", "")
                    })

            # Institution registrations
            elif "institution_name" in reg_data:
                delegate = {
                    "delegate_head_name": reg_data.get("delegate_head_name", ""),
                    "delegate_email": reg_data.get("email", ""),
                    "delegate_phone": reg_data.get("phone_no", ""),
                    "institution_name": reg_data.get("institution_name", "")
                }
                for team in reg_data.get("teams", []):
                    team_name = team.get("team_name", "")
                    for p in team.get("participants", []):
                        rows.append({
                            "type": "institution",
                            **delegate,
                            "team_name": team_name,
                            "name": p.get("name", ""),
                            "reg_no": p.get("reg_no", "")
                        })

        if not rows:
            print(f"⚠️ No registrations for {event_name}")
            return

        df = pd.DataFrame(rows)
        path = os.path.join(self.output_dir, f"{event_name}.xlsx")
        df.to_excel(path, index=False)
        print(f"✅ Exported {event_name} -> {path}")

    def export_all_events(self, registration_types=["individual", "institution"]):
        """
        Traverse all registrations for given types and export each event as a separate Excel file.
        """
        registrations_ref = self.db.collection("registrations")

        for reg_type in registration_types:
            clubs = registrations_ref.document(reg_type).collection("clubs").stream()
            for club in clubs:
                events = club.reference.collection("events").stream()
                for event in events:
                    event_data = event.to_dict()
                    event_name = event_data.get("event_name", event.id)
                    self._export_event(event.reference, event_name)
