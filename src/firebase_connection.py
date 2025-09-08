import firebase_admin
from firebase_admin import credentials

cred = credentials.Certificate("firebase-adminsdk-fbsvc@equinox-2025.iam.gserviceaccount.com")
firebase_admin.initialize_app(cred)