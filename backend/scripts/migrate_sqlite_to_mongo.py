"""
Migration script: move data from SQLite to MongoDB without importing the Flask app.

It reads the SQLite database file directly and writes documents to MongoDB using
`pymongo`. Numeric SQL IDs are stored as string `_id` in Mongo to preserve
references. This makes the script runnable even when the app has been converted
to Mongo-only.

Usage:
    python backend/scripts/migrate_sqlite_to_mongo.py

Ensure `MONGODB_URI` is set in the environment or in backend/.env.
"""
import os
import sqlite3
import json
from datetime import datetime

try:
    from pymongo import MongoClient
except Exception:
    MongoClient = None


def _load_env(env_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')):
    if not os.path.exists(env_path):
        return
    with open(env_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' in line:
                k, v = line.split('=', 1)
                os.environ.setdefault(k.strip(), v.strip())


def migrate():
    # Load .env if present
    _load_env()

    mongo_uri = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
    if not mongo_uri:
        print('MONGODB_URI not set. Set it in environment or backend/.env and retry.')
        return

    if MongoClient is None:
        print('pymongo not installed. Install with `pip install pymongo` and retry.')
        return

    # Determine SQLite DB path
    default_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'attendance_system.db')
    db_uri = os.getenv('DATABASE_URL')
    if db_uri and db_uri.startswith('sqlite:///'):
        # sqlite:///path/to/db -> extract path
        db_path = db_uri.replace('sqlite:///', '')
    else:
        db_path = default_db

    if not os.path.exists(db_path):
        print(f'SQLite DB not found at {db_path}')
        return

    client = MongoClient(mongo_uri)
    db = client.get_default_database()

    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # Helper to insert if not exists
    def upsert_collection(collection_name, doc, id_key='_id'):
        col = db[collection_name]
        if id_key in doc and col.find_one({id_key: doc[id_key]}):
            return False
        col.insert_one(doc)
        return True

    # Users
    try:
        cur.execute('SELECT * FROM users')
        users = cur.fetchall()
        migrated = 0
        for u in users:
            ur = dict(u)
            _id = str(ur.get('id') or ur.get('Id') or ur.get('ID'))
            doc = {
                '_id': _id,
                'username': ur.get('username'),
                'email': ur.get('email'),
                'role': ur.get('role'),
                'full_name': ur.get('full_name'),
                'is_active': bool(ur.get('is_active')),
                'created_at': ur.get('created_at')
            }
            if upsert_collection('users', doc):
                migrated += 1
        print(f'Migrated {migrated} users')
    except Exception as e:
        print('Error migrating users:', e)

    # Students
    try:
        cur.execute('SELECT * FROM students')
        rows = cur.fetchall()
        migrated = 0
        for r in rows:
            rr = dict(r)
            _id = str(rr.get('id') or rr.get('Id') or rr.get('ID'))
            face_enc = []
            try:
                if rr.get('face_encodings'):
                    face_enc = json.loads(rr.get('face_encodings'))
            except Exception:
                face_enc = []
            doc = {
                '_id': _id,
                'roll_number': rr.get('roll_number'),
                'admission_number': rr.get('admission_number'),
                'full_name': rr.get('full_name'),
                'class_name': rr.get('class_name'),
                'section': rr.get('section'),
                'date_of_birth': rr.get('date_of_birth'),
                'parent_contact': rr.get('parent_contact'),
                'parent_email': rr.get('parent_email'),
                'profile_image': rr.get('profile_image'),
                'is_active': bool(rr.get('is_active')),
                'created_at': rr.get('created_at'),
                'face_encodings': face_enc
            }
            if upsert_collection('students', doc):
                migrated += 1
        print(f'Migrated {migrated} students')
    except Exception as e:
        print('Error migrating students:', e)

    # Classes
    try:
        cur.execute('SELECT * FROM classes')
        rows = cur.fetchall()
        migrated = 0
        for r in rows:
            rr = dict(r)
            _id = str(rr.get('id') or rr.get('Id') or rr.get('ID'))
            doc = {
                '_id': _id,
                'name': rr.get('name'),
                'section': rr.get('section'),
                'academic_year': rr.get('academic_year'),
                'is_active': bool(rr.get('is_active')),
                'created_at': rr.get('created_at')
            }
            if upsert_collection('classes', doc):
                migrated += 1
        print(f'Migrated {migrated} classes')
    except Exception as e:
        print('Error migrating classes:', e)

    # Attendance records
    try:
        cur.execute('SELECT * FROM attendance_records')
        rows = cur.fetchall()
        migrated = 0
        for r in rows:
            rr = dict(r)
            doc = {
                'student_id': str(rr.get('student_id')),
                'date': rr.get('date'),
                'time_in': rr.get('time_in'),
                'time_out': rr.get('time_out'),
                'status': rr.get('status'),
                'confidence_score': rr.get('confidence_score'),
                'marked_by': rr.get('marked_by'),
                'notes': rr.get('notes'),
                'created_at': rr.get('created_at'),
                'updated_at': rr.get('updated_at')
            }
            db.attendance_records.insert_one(doc)
            migrated += 1
        print(f'Migrated {migrated} attendance records')
    except Exception as e:
        print('Error migrating attendance records:', e)

    # System settings
    try:
        cur.execute('SELECT * FROM system_settings')
        rows = cur.fetchall()
        migrated = 0
        for r in rows:
            rr = dict(r)
            _id = str(rr.get('id') or rr.get('Id') or rr.get('ID'))
            doc = {
                '_id': _id,
                'key': rr.get('key'),
                'value': rr.get('value'),
                'description': rr.get('description'),
                'updated_at': rr.get('updated_at')
            }
            if upsert_collection('system_settings', doc):
                migrated += 1
        print(f'Migrated {migrated} system settings')
    except Exception as e:
        print('Error migrating system settings:', e)

    conn.close()
    print('Migration completed')


if __name__ == '__main__':
    migrate()
