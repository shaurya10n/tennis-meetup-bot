import firebase_admin
from firebase_admin import credentials, firestore, initialize_app
import os
from welcome import _OfflineGCPCredentials

os.environ["FIRESTORE_EMULATOR_HOST"] = "localhost:9000"


firebase_admin.delete_app(firebase_admin.get_app())
initialize_app(credential=_OfflineGCPCredentials(), options={'projectId': 'tennismeetupbot'})
db = firestore.client()
print("Firestore connected successfully!")

# Test the connection
db = firestore.client()
print("Firebase initialized")

# Try to write and read a test document
try:
    test_ref = db.collection('test').document('test')
    test_ref.set({'test': 'data'})
    result = test_ref.get()
    print(f"Test document data: {result.to_dict()}")
except Exception as e:
    print(f"Firebase test failed: {e}")
