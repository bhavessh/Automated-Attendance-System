import os
import sys
from datetime import datetime
import json

# Ensure backend path is importable
HERE = os.path.dirname(__file__)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

print('Running quick backend checks')

try:
    import app
    print('Imported backend.app')
except Exception as e:
    print('Error importing app:', e)
    raise

print('USE_MONGO:', getattr(app, 'USE_MONGO', False))
print('MONGODB_URI env:', os.getenv('MONGODB_URI'))

# Test Mongo connectivity by inserting a test doc (without running the server)
if getattr(app, 'USE_MONGO', False) and getattr(app, 'mongo', None):
    try:
        coll = app.mongo.db._test_collection
        res = coll.insert_one({'test': 'ok', 'created_at': datetime.utcnow().isoformat()})
        doc = coll.find_one({'_id': res.inserted_id})
        print('Mongo insert OK:', str(res.inserted_id), 'doc.test=', doc.get('test'))
    except Exception as e:
        print('Mongo test failed:', e)
else:
    print('Mongo not configured; skipping insert test')

# Use Flask test client to exercise API endpoints without starting server
try:
    client = app.test_client()

    # Create student
    payload = {
        'roll_number': 'R1000',
        'admission_number': 'ADM1000',
        'full_name': 'Automated Test Student',
        'class_name': '1',
        'section': 'A',
        'date_of_birth': '2010-01-01'
    }
    resp = client.post('/api/students', json=payload)
    print('/api/students POST ->', resp.status_code, resp.get_json())

    # List students
    resp = client.get('/api/students')
    try:
        data = resp.get_json()
    except Exception:
        data = {'status_code': resp.status_code}
    print('/api/students GET ->', resp.status_code, data.get('count') if isinstance(data, dict) else data)

    # Try a simple reports summary call
    resp = client.get('/api/reports/summary')
    try:
        print('/api/reports/summary ->', resp.status_code, resp.get_json() if resp.is_json else '[non-json response]')
    except Exception:
        print('/api/reports/summary ->', resp.status_code)

except Exception as e:
    print('Error during API checks:', e)
    raise

print('Quick checks completed')
