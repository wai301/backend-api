from firebase_config import get_firestore_db, get_server_timestamp
import json

def test_connection():
    try:
        db = get_firestore_db()
        
        # ทดสอบเขียนข้อมูล
        test_ref = db.collection('test').document('connection_test')
        test_ref.set({
            'message': 'Connection test successful',
            'timestamp': get_server_timestamp()
        })
        
        # ทดสอบอ่านข้อมูล
        doc = test_ref.get()
        print(f"Test document data: {doc.to_dict()}")
        
        print("Firebase connection test passed!")
        return True
        
    except Exception as e:
        print(f"Firebase connection test failed: {e}")
        return False

if __name__ == "__main__":
    test_connection()