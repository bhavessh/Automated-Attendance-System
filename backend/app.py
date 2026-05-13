import json
import os
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
except Exception:
    def load_dotenv(path='.env'):
        try:
            here = os.path.dirname(os.path.abspath(__file__))
            env_path = os.path.join(here, path)
            if os.path.exists(env_path):
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith('#'):
                            continue
                        if '=' in line:
                            k, v = line.split('=', 1)
                            os.environ.setdefault(k.strip(), v.strip())
        except Exception:
            pass
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
# SQLAlchemy will be initialized only when Mongo is not used
try:
    from sqlalchemy import UniqueConstraint
except Exception:
    UniqueConstraint = None
from werkzeug.security import check_password_hash, generate_password_hash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

# Load environment variables
load_dotenv()

# Initialize Flask app
base_dir = os.path.dirname(os.path.abspath(__file__))
instance_dir = os.path.join(base_dir, 'instance')
app = Flask(__name__, instance_path=instance_dir, instance_relative_config=True)
CORS(app, resources={r"/api/*": {"origins": [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:3002",
    "http://127.0.0.1:3002"
] }}, supports_credentials=True, allow_headers=["Content-Type", "Authorization"], methods=["GET", "HEAD", "POST", "OPTIONS", "PUT", "PATCH", "DELETE"])


os.makedirs(app.instance_path, exist_ok=True)
default_db_path = os.path.join(app.instance_path, 'attendance_system.db')
default_db_uri = f"sqlite:///{default_db_path.replace(os.sep, '/')}"
env_db_uri = os.getenv('DATABASE_URL')
if env_db_uri and env_db_uri.startswith('sqlite:///instance/'):
    env_db_uri = default_db_uri

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key-here')
app.config['SQLALCHEMY_DATABASE_URI'] = env_db_uri or default_db_uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt-secret-string')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)
app.config['UPLOAD_FOLDER'] = 'uploads/faces'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Initialize extensions
db = None
#cors = CORS(app)
jwt = JWTManager(app)

# Optional MongoDB initialization (use when MONGODB_URI provided)
mongo = None
USE_MONGO = False
mongo_uri = os.getenv('MONGODB_URI') or os.getenv('MONGO_URI')
if mongo_uri:
    app.config['MONGO_URI'] = mongo_uri
    try:
        mongo = PyMongo(app)
        USE_MONGO = True
        print(f"OK Connected to MongoDB: {mongo_uri.split('@')[-1]}")
    except Exception as e:
        print(f"Warning: MongoDB init failed: {e}")
        mongo = None
# Require MongoDB for this branch (pure-Mongo mode)
if not USE_MONGO or not mongo:
    raise RuntimeError("MONGODB_URI not configured or connection failed. This deployment requires MongoDB. Set MONGODB_URI in backend/.env or environment variables.")

# --- Mongo helper utilities ---
def _mongo_user_to_dict(user_doc):
    if not user_doc:
        return None
    return {
        'id': str(user_doc.get('_id')),
        'username': user_doc.get('username'),
        'email': user_doc.get('email'),
        'role': user_doc.get('role'),
        'full_name': user_doc.get('full_name'),
        'is_active': user_doc.get('is_active', True),
    }

def _mongo_student_to_dict(doc):
    if not doc:
        return None
    return {
        'id': str(doc.get('_id')),
        'roll_number': doc.get('roll_number'),
        'admission_number': doc.get('admission_number'),
        'full_name': doc.get('full_name'),
        'class_name': doc.get('class_name'),
        'section': doc.get('section'),
        'date_of_birth': doc.get('date_of_birth'),
        'parent_contact': doc.get('parent_contact'),
        'parent_email': doc.get('parent_email'),
        'profile_image': doc.get('profile_image'),
        'is_active': doc.get('is_active', True),
        'created_at': doc.get('created_at')
    }

def _mongo_find_student_by_admission(adm):
    return mongo.db.students.find_one({'admission_number': adm})

def _mongo_find_roll_conflict(roll_number, class_name, section, exclude_id=None):
    q = {'roll_number': roll_number, 'class_name': class_name, 'section': section}
    if exclude_id:
        try:
            q['_id'] = {'$ne': ObjectId(exclude_id)}
        except Exception:
            pass
    return mongo.db.students.find_one(q)


# Create upload directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import models and routes after app initialization
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create basic test route for now
@app.route('/api/health')
def health_check():
    return {'status': 'ok', 'message': 'Attendance System API is running'}


@app.route('/api/mongo-test')
def mongo_test():
    if not USE_MONGO or not mongo:
        return jsonify({'mongo': False, 'message': 'MongoDB not configured (set MONGODB_URI)'}), 400
    try:
        coll = mongo.db._test_collection
        res = coll.insert_one({'test': 'ok', 'created_at': datetime.utcnow().isoformat()})
        doc = coll.find_one({'_id': res.inserted_id})
        return jsonify({'mongo': True, 'inserted_id': str(res.inserted_id), 'doc': {'test': doc.get('test')}}), 200
    except Exception as e:
        return jsonify({'mongo': False, 'error': str(e)}), 500

@app.route('/api/test')
def test_route():
    return {'message': 'Test endpoint working', 'database_uri': app.config['SQLALCHEMY_DATABASE_URI']}


@app.route('/api/mongo-test-echo')
def mongo_test_echo():
    """Duplicate debug endpoint to verify /api/mongo-test behavior."""
    if not USE_MONGO or not mongo:
        return jsonify({'mongo': False, 'message': 'MongoDB not configured (set MONGODB_URI)'}), 400
    try:
        coll = mongo.db._test_collection
        res = coll.insert_one({'test': 'ok', 'created_at': datetime.utcnow().isoformat()})
        doc = coll.find_one({'_id': res.inserted_id})
        return jsonify({'mongo': True, 'inserted_id': str(res.inserted_id), 'doc': {'test': doc.get('test')}}), 200
    except Exception as e:
        return jsonify({'mongo': False, 'error': str(e)}), 500


@app.route('/api/routes')
def list_routes():
    """Return registered URL rules for debugging."""
    rules = []
    for r in app.url_map.iter_rules():
        rules.append({'rule': r.rule, 'methods': list(r.methods)})
    return jsonify({'routes': rules}), 200

# SQLAlchemy model classes removed — app runs in pure-Mongo mode

# Login endpoint
@app.route('/api/auth/login', methods=['POST'])
def login():
    """User authentication endpoint"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        user_doc = mongo.db.users.find_one({'username': username})
        if user_doc and check_password_hash(user_doc.get('password_hash', ''), password) and user_doc.get('is_active', True):
            access_token = create_access_token(identity=str(user_doc.get('_id')))
            return jsonify({
                'access_token': access_token,
                'user': _mongo_user_to_dict(user_doc),
                'message': 'Login successful'
            }), 200
        return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500


# Ensure OPTIONS preflight and CORS headers are always returned for API routes
@app.route('/api/auth/login', methods=['OPTIONS'])
def login_options():
    # empty response for preflight; headers added in after_request
    return ('', 204)


@app.after_request
def _add_cors_headers(response):
    origin = request.headers.get('Origin')
    if origin:
        # Echo back the Origin instead of using wildcard when credentials used
        response.headers['Access-Control-Allow-Origin'] = origin
        response.headers['Vary'] = 'Origin'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
    return response


# Handle OPTIONS preflight globally to ensure headers are present
@app.before_request
def _handle_options_global():
    if request.method == 'OPTIONS' and request.path.startswith('/api/'):
        origin = request.headers.get('Origin', '*')
        res = app.make_response(('', 204))
        res.headers['Access-Control-Allow-Origin'] = origin
        res.headers['Vary'] = 'Origin'
        res.headers['Access-Control-Allow-Credentials'] = 'true'
        res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        res.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
        return res


# Catch-all OPTIONS for /api/* in case other handlers bypass before_request
@app.route('/api/<path:any_path>', methods=['OPTIONS'])
def _options_catch_all(any_path):
    origin = request.headers.get('Origin', '*')
    res = app.make_response(('', 204))
    res.headers['Access-Control-Allow-Origin'] = origin
    res.headers['Vary'] = 'Origin'
    res.headers['Access-Control-Allow-Credentials'] = 'true'
    res.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    res.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, PATCH, DELETE'
    return res

if not USE_MONGO:
    # Student model
    class Student(db.Model):
        __tablename__ = 'students'
        
        id = db.Column(db.Integer, primary_key=True)
        # roll_number should be unique per (class_name, section)
        roll_number = db.Column(db.String(50), nullable=False)
        # admission_number remains globally unique
        admission_number = db.Column(db.String(50), unique=True, nullable=False)
        full_name = db.Column(db.String(200), nullable=False)
        class_name = db.Column(db.String(50), nullable=False)
        section = db.Column(db.String(10), nullable=False)
        date_of_birth = db.Column(db.Date)
        parent_contact = db.Column(db.String(15))
        parent_email = db.Column(db.String(120))
        address = db.Column(db.Text)
        face_encodings = db.Column(db.Text)  # JSON string of face encodings
        profile_image = db.Column(db.String(255))  # Path to profile image
        is_active = db.Column(db.Boolean, default=True)
        created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
        updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
        # Composite uniqueness at DB level
        __table_args__ = (
            UniqueConstraint('class_name', 'section', 'roll_number', name='uq_students_class_section_roll'),
        )
        
        def to_dict(self):
            return {
                'id': self.id,
                'roll_number': self.roll_number,
                'admission_number': self.admission_number,
                'full_name': self.full_name,
                'class_name': self.class_name,
                'section': self.section,
                'date_of_birth': self.date_of_birth.isoformat() if self.date_of_birth else None,
                'parent_contact': self.parent_contact,
                'parent_email': self.parent_email,
                'profile_image': self.profile_image,
                'is_active': self.is_active,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

    # Attendance Record model
    class AttendanceRecord(db.Model):
        __tablename__ = 'attendance_records'
        
        id = db.Column(db.Integer, primary_key=True)
        student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
        date = db.Column(db.Date, nullable=False)
        time_in = db.Column(db.Time)
        time_out = db.Column(db.Time)
        status = db.Column(db.String(20), default='present')  # present, absent, late
        confidence_score = db.Column(db.Float)  # Face recognition confidence
        marked_by = db.Column(db.String(50), default='system')  # system, manual
        notes = db.Column(db.Text)
        created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
        updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
        
        # Relationship
        student = db.relationship('Student', backref='attendance_records')
        
        def to_dict(self):
            return {
                'id': self.id,
                'student_id': self.student_id,
                'student_name': self.student.full_name if self.student else None,
                'date': self.date.isoformat() if self.date else None,
                'time_in': self.time_in.strftime('%H:%M:%S') if self.time_in else None,
                'time_out': self.time_out.strftime('%H:%M:%S') if self.time_out else None,
                'status': self.status,
                'confidence_score': self.confidence_score,
                'marked_by': self.marked_by,
                'notes': self.notes,
                'created_at': self.created_at.isoformat() if self.created_at else None
            }

def _default_settings_payload():
    return {
        'faceRecognition': {
            'threshold': 0.6,
            'minFaceSize': 80
        },
        'users': {
            'allowTeacherEdits': False
        },
        'powerbi': {
            'workspaceId': '',
            'datasetId': '',
            'enabled': False
        },
        'notifications': {
            'emailEnabled': False,
            'smsEnabled': False
        },
        'backup': {
            'enabled': False,
            'schedule': 'daily'
        }
    }

def _get_or_create_settings():
    settings = SystemSetting.query.filter_by(key='system_settings').first()
    if settings:
        return settings
    settings = SystemSetting(
        key='system_settings',
        value=json.dumps(_default_settings_payload())
    )
    db.session.add(settings)
    db.session.commit()
    return settings

def _parse_date(value, field_name):
    if not value:
        return None
    try:
        return datetime.strptime(value, '%Y-%m-%d').date()
    except ValueError:
        raise ValueError(f"Invalid {field_name} format. Use YYYY-MM-DD")

def _attendance_query(start_date=None, end_date=None, class_name=None, section=None):
    query = db.session.query(AttendanceRecord).join(Student)
    if start_date:
        query = query.filter(AttendanceRecord.date >= start_date)
    if end_date:
        query = query.filter(AttendanceRecord.date <= end_date)
    if class_name:
        query = query.filter(Student.class_name == class_name)
    if section:
        query = query.filter(Student.section == section)
    return query

# Student Management Endpoints
@app.route('/api/students', methods=['GET'])
def get_students():
    """Get all students"""
    try:
        class_name = request.args.get('class')
        section = request.args.get('section')
        search = request.args.get('search')

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        q = {'is_active': True}
        if class_name:
            q['class_name'] = class_name
        if section:
            q['section'] = section
        if search:
            q['$or'] = [
                {'full_name': {'$regex': search, '$options': 'i'}},
                {'roll_number': {'$regex': search, '$options': 'i'}},
                {'admission_number': {'$regex': search, '$options': 'i'}}
            ]
        docs = list(mongo.db.students.find(q))
        students_data = [_mongo_student_to_dict(d) for d in docs]
        return jsonify({'students': students_data, 'count': len(students_data)}), 200
    
    except Exception as e:
        print(f"Get students error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/settings', methods=['GET'])
def get_system_settings():
    """Get system settings"""
    try:
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        doc = mongo.db.system_settings.find_one({'key': 'system_settings'})
        if doc:
            return jsonify({'settings': doc.get('value')}), 200
        payload = _default_settings_payload()
        mongo.db.system_settings.insert_one({'key': 'system_settings', 'value': payload, 'updated_at': datetime.utcnow().isoformat()})
        return jsonify({'settings': payload}), 200
    except Exception as e:
        print(f"Get settings error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/settings', methods=['PUT'])
def update_system_settings():
    """Update system settings"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        mongo.db.system_settings.update_one({'key': 'system_settings'}, {'$set': {'value': data, 'updated_at': datetime.utcnow().isoformat()}}, upsert=True)
        return jsonify({'message': 'Settings updated', 'settings': data}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Update settings error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/reports/summary', methods=['GET'])
def get_reports_summary():
    """Daily attendance summary for reports"""
    try:
        start_date = _parse_date(request.args.get('start_date'), 'start_date')
        end_date = _parse_date(request.args.get('end_date'), 'end_date')
        class_name = request.args.get('class')
        section = request.args.get('section')

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        match = {}
        if start_date or end_date:
            date_query = {}
            if start_date:
                date_query['$gte'] = start_date.isoformat()
            if end_date:
                date_query['$lte'] = end_date.isoformat()
            match['date'] = date_query

        if class_name or section:
            student_q = {'is_active': True}
            if class_name:
                student_q['class_name'] = class_name
            if section:
                student_q['section'] = section
            students = list(mongo.db.students.find(student_q, {'_id': 1}))
            student_ids = [str(s.get('_id')) for s in students]
            match['student_id'] = {'$in': student_ids} if student_ids else {'$in': []}

        pipeline = [
            {'$match': match} if match else {'$match': {}},
            {'$group': {
                '_id': '$date',
                'total': {'$sum': 1},
                'present': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}},
                'absent': {'$sum': {'$cond': [{'$eq': ['$status', 'absent']}, 1, 0]}},
                'late': {'$sum': {'$cond': [{'$eq': ['$status', 'late']}, 1, 0]}}
            }},
            {'$sort': {'_id': -1}}
        ]
        agg = list(mongo.db.attendance_records.aggregate(pipeline))
        summary = []
        for row in agg:
            total = row.get('total', 0)
            present = row.get('present', 0)
            rate = round((present / total) * 100, 2) if total else 0.0
            summary.append({
                'date': row.get('_id'),
                'total': total,
                'present': present,
                'absent': row.get('absent', 0),
                'late': row.get('late', 0),
                'attendance_rate': rate
            })
        return jsonify({'summary': summary}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Reports summary error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reports/student-analytics', methods=['GET'])
def get_student_analytics():
    """Student-wise attendance analytics"""
    try:
        start_date = _parse_date(request.args.get('start_date'), 'start_date')
        end_date = _parse_date(request.args.get('end_date'), 'end_date')
        class_name = request.args.get('class')
        section = request.args.get('section')

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
            match = {}
            if start_date or end_date:
                date_q = {}
                if start_date:
                    date_q['$gte'] = start_date.isoformat()
                if end_date:
                    date_q['$lte'] = end_date.isoformat()
                match['date'] = date_q

            if class_name or section:
                student_q = {'is_active': True}
                if class_name:
                    student_q['class_name'] = class_name
                if section:
                    student_q['section'] = section
                students = list(mongo.db.students.find(student_q, {'_id': 1, 'full_name': 1, 'class_name': 1, 'section': 1}))
                student_ids = [str(s['_id']) for s in students]
                if student_ids:
                    match['student_id'] = {'$in': student_ids}
                else:
                    # no students match filter
                    return jsonify({'students': []}), 200

        pipeline = [
            {'$match': match} if match else {'$match': {}},
            {'$group': {
                '_id': '$student_id',
                'total': {'$sum': 1},
                'present': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}},
                'absent': {'$sum': {'$cond': [{'$eq': ['$status', 'absent']}, 1, 0]}},
                'late': {'$sum': {'$cond': [{'$eq': ['$status', 'late']}, 1, 0]}}
            }},
        ]
        agg = list(mongo.db.attendance_records.aggregate(pipeline))
        analytics = []
        for row in agg:
            sid = row.get('_id')
            sdoc = mongo.db.students.find_one({'_id': ObjectId(sid)}) if ObjectId.is_valid(sid) else mongo.db.students.find_one({'_id': sid})
            rate = round((row.get('present', 0) / row.get('total', 0)) * 100, 2) if row.get('total', 0) else 0.0
            analytics.append({
                'student_id': sid,
                'student_name': sdoc.get('full_name') if sdoc else None,
                'class_name': sdoc.get('class_name') if sdoc else None,
                'section': sdoc.get('section') if sdoc else None,
                'total': row.get('total', 0),
                'present': row.get('present', 0),
                'absent': row.get('absent', 0),
                'late': row.get('late', 0),
                'attendance_rate': rate
            })
        return jsonify({'students': analytics}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Student analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reports/class-analytics', methods=['GET'])
def get_class_analytics():
    """Class and section performance metrics"""
    try:
        start_date = _parse_date(request.args.get('start_date'), 'start_date')
        end_date = _parse_date(request.args.get('end_date'), 'end_date')

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
            match = {}
            if start_date or end_date:
                date_q = {}
                if start_date:
                    date_q['$gte'] = start_date.isoformat()
                if end_date:
                    date_q['$lte'] = end_date.isoformat()
                match['date'] = date_q

            # aggregate by student to get class & section
            pipeline = [
                {'$match': match} if match else {'$match': {}},
                {'$group': {'_id': '$student_id', 'count': {'$sum': 1}, 'present': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}}, 'absent': {'$sum': {'$cond': [{'$eq': ['$status', 'absent']}, 1, 0]}}, 'late': {'$sum': {'$cond': [{'$eq': ['$status', 'late']}, 1, 0]}}}},
            ]
            agg = list(mongo.db.attendance_records.aggregate(pipeline))
            # bucket by class & section
            buckets = {}
            for row in agg:
                sid = row.get('_id')
                sdoc = mongo.db.students.find_one({'_id': ObjectId(sid)}) if ObjectId.is_valid(sid) else mongo.db.students.find_one({'_id': sid})
                if not sdoc:
                    continue
                key = (sdoc.get('class_name'), sdoc.get('section'))
                if key not in buckets:
                    buckets[key] = {'total': 0, 'present': 0, 'absent': 0, 'late': 0}
                buckets[key]['total'] += row.get('count', 0)
                buckets[key]['present'] += row.get('present', 0)
                buckets[key]['absent'] += row.get('absent', 0)
                buckets[key]['late'] += row.get('late', 0)

            analytics = []
            for (cls, sec), vals in sorted(buckets.items()):
                total = vals['total']
                rate = round((vals['present'] / total) * 100, 2) if total else 0.0
                analytics.append({'class_name': cls, 'section': sec, 'total': total, 'present': vals['present'], 'absent': vals['absent'], 'late': vals['late'], 'attendance_rate': rate})
            return jsonify({'classes': analytics}), 200
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        print(f"Class analytics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/reports/attendance', methods=['GET'])
def export_attendance_report():
    """Export attendance report to Excel or PDF"""
    try:
        format_type = request.args.get('format', 'excel').lower()
        start_date = _parse_date(request.args.get('start_date'), 'start_date')
        end_date = _parse_date(request.args.get('end_date'), 'end_date')
        class_name = request.args.get('class')
        section = request.args.get('section')

        export_rows = []
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        q = {}
        if start_date or end_date:
            date_q = {}
            if start_date:
                date_q['$gte'] = start_date.isoformat()
            if end_date:
                date_q['$lte'] = end_date.isoformat()
            q['date'] = date_q

        if class_name or section:
            student_q = {'is_active': True}
            if class_name:
                student_q['class_name'] = class_name
            if section:
                student_q['section'] = section
            students = list(mongo.db.students.find(student_q, {'_id': 1, 'full_name': 1, 'roll_number': 1, 'class_name': 1, 'section': 1}))
            student_ids = [str(s['_id']) for s in students]
            if student_ids:
                q['student_id'] = {'$in': student_ids}
            else:
                q['student_id'] = {'$in': []}

        records = list(mongo.db.attendance_records.find(q).sort('date', 1))
        for record in records:
            student_doc = None
            sid = record.get('student_id')
            if sid:
                student_doc = mongo.db.students.find_one({'_id': ObjectId(sid)}) if ObjectId.is_valid(sid) else mongo.db.students.find_one({'_id': sid})
            export_rows.append({
                'date': record.get('date'),
                'student_id': record.get('student_id'),
                'student_name': student_doc.get('full_name') if student_doc else None,
                'roll_number': student_doc.get('roll_number') if student_doc else None,
                'class': student_doc.get('class_name') if student_doc else None,
                'section': student_doc.get('section') if student_doc else None,
                'status': record.get('status'),
                'time_in': record.get('time_in'),
                'time_out': record.get('time_out'),
                'marked_by': record.get('marked_by')
            })

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        if format_type == 'excel':
            from io import BytesIO

            import pandas as pd

            output = BytesIO()
            df = pd.DataFrame(export_rows)
            df.to_excel(output, index=False)
            output.seek(0)
            filename = f"attendance_report_{timestamp}.xlsx"
            return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

        if format_type == 'pdf':
            from io import BytesIO

            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas

            output = BytesIO()
            c = canvas.Canvas(output, pagesize=letter)
            width, height = letter
            y = height - 40

            c.setFont('Helvetica-Bold', 14)
            c.drawString(40, y, 'Attendance Report')
            y -= 24
            c.setFont('Helvetica', 9)
            c.drawString(40, y, f"Generated: {datetime.now().isoformat(timespec='seconds')}")
            y -= 20

            headers = ['Date', 'Student', 'Class', 'Section', 'Status', 'Time In']
            c.setFont('Helvetica-Bold', 9)
            c.drawString(40, y, ' | '.join(headers))
            y -= 14
            c.setFont('Helvetica', 9)

            for row in export_rows:
                line = f"{row.get('date', '')} | {row.get('student_name', '')} | {row.get('class', '')} | {row.get('section', '')} | {row.get('status', '')} | {row.get('time_in', '')}"
                if y < 40:
                    c.showPage()
                    y = height - 40
                    c.setFont('Helvetica-Bold', 9)
                    c.drawString(40, y, ' | '.join(headers))
                    y -= 14
                    c.setFont('Helvetica', 9)
                c.drawString(40, y, line[:120])
                y -= 12

            c.save()
            output.seek(0)
            filename = f"attendance_report_{timestamp}.pdf"
            return send_file(output, as_attachment=True, download_name=filename, mimetype='application/pdf')

        return jsonify({'error': 'Unsupported format. Use excel or pdf'}), 400
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        print(f"Export attendance report error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'error': str(e), 'traceback': traceback.format_exc()}), 500

@app.route('/api/students', methods=['POST'])
def create_student():
    """Create new student"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        # Enforce uniqueness rules: admission_number global; roll_number unique within class+section
        roll_number = data.get('roll_number')
        admission_number = data.get('admission_number')
        class_name = data.get('class_name')
        section = data.get('section')

        if not all([roll_number, admission_number, class_name, section]):
            return jsonify({'error': 'roll_number, admission_number, class_name and section are required'}), 400

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        # Check admission uniqueness
        if _mongo_find_student_by_admission(admission_number):
            return jsonify({'error': 'A student with this admission number already exists'}), 400

        if _mongo_find_roll_conflict(roll_number, class_name, section):
            return jsonify({'error': 'A student with this roll number already exists in this class and section'}), 400

        date_of_birth = data.get('date_of_birth')
        student_doc = {
            'roll_number': roll_number,
            'admission_number': admission_number,
            'full_name': data.get('full_name'),
            'class_name': class_name,
            'section': section,
            'date_of_birth': date_of_birth,
            'parent_contact': data.get('parent_contact'),
            'parent_email': data.get('parent_email'),
            'address': data.get('address'),
            'face_encodings': [],
            'profile_image': None,
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        res = mongo.db.students.insert_one(student_doc)
        student_doc['_id'] = res.inserted_id
        return jsonify({'message': 'Student created successfully', 'student': _mongo_student_to_dict(student_doc)}), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Create student error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/students/<student_id>', methods=['PUT'])
def update_student(student_id):
    """Update student details with uniqueness validation"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        # student_id is expected to be a string ObjectId
        try:
            sdoc = mongo.db.students.find_one({'_id': ObjectId(student_id)})
        except Exception:
            return jsonify({'error': 'Invalid student id'}), 400
        if not sdoc:
            return jsonify({'error': 'Student not found'}), 404

        full_name = data.get('full_name', sdoc.get('full_name'))
        class_name = data.get('class_name', sdoc.get('class_name'))
        section = data.get('section', sdoc.get('section'))
        roll_number = data.get('roll_number', sdoc.get('roll_number'))
        admission_number = data.get('admission_number', sdoc.get('admission_number'))

        # Admission number uniqueness
        exists_adm = mongo.db.students.find_one({'admission_number': admission_number, '_id': {'$ne': sdoc.get('_id')}})
        if exists_adm:
            return jsonify({'error': 'A student with this admission number already exists'}), 400

        # Roll number uniqueness per class+section
        exists_roll = mongo.db.students.find_one({
            'roll_number': roll_number,
            'class_name': class_name,
            'section': section,
            '_id': {'$ne': sdoc.get('_id')}
        })
        if exists_roll:
            return jsonify({'error': 'A student with this roll number already exists in this class and section'}), 400

        updates = {
            'full_name': full_name,
            'class_name': class_name,
            'section': section,
            'roll_number': roll_number,
            'admission_number': admission_number,
            'parent_contact': data.get('parent_contact', sdoc.get('parent_contact')),
            'parent_email': data.get('parent_email', sdoc.get('parent_email')),
            'address': data.get('address', sdoc.get('address'))
        }

        if 'date_of_birth' in data:
            dob_value = data.get('date_of_birth')
            updates['date_of_birth'] = dob_value if dob_value else None

        mongo.db.students.update_one({'_id': sdoc.get('_id')}, {'$set': updates})
        newdoc = mongo.db.students.find_one({'_id': sdoc.get('_id')})
        return jsonify({'message': 'Student updated successfully', 'student': _mongo_student_to_dict(newdoc)}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Update student error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/students/<student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student and their attendance records"""
    try:
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        try:
            sdoc = mongo.db.students.find_one({'_id': ObjectId(student_id)})
        except Exception:
            return jsonify({'error': 'Invalid student id'}), 400
        if not sdoc:
            return jsonify({'error': 'Student not found'}), 404
        mongo.db.attendance_records.delete_many({'student_id': str(sdoc.get('_id'))})
        mongo.db.students.delete_one({'_id': sdoc.get('_id')})
        return jsonify({'message': 'Student deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Delete student error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

# Attendance Management Endpoints
@app.route('/api/attendance/manual', methods=['POST'])
def mark_manual_attendance():
    """Manually mark attendance"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400
        
        student_id = data.get('student_id')
        attendance_date_str = data.get('date')
        status = data.get('status', 'present')
        notes = data.get('notes')
        time_in_str = data.get('time_in')
        
        if not student_id or not attendance_date_str:
            return jsonify({'error': 'student_id and date are required'}), 400
        
        # Parse date
        try:
            attendance_date = datetime.strptime(attendance_date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Parse time if provided
        time_in = None
        if time_in_str:
            try:
                time_in = datetime.strptime(time_in_str, '%H:%M').time()
            except ValueError:
                return jsonify({'error': 'Invalid time format. Use HH:MM'}), 400
        else:
            time_in = datetime.now().time()
        
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        try:
            student = mongo.db.students.find_one({'_id': ObjectId(student_id)})
        except Exception:
            return jsonify({'error': 'Invalid student id'}), 400
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        # Check if attendance already exists for this date
        existing_record = mongo.db.attendance_records.find_one({'student_id': str(student.get('_id')), 'date': attendance_date.isoformat()})
        if existing_record:
            return jsonify({'error': 'Attendance already marked for this date'}), 400

        attendance_doc = {
            'student_id': str(student.get('_id')),
            'date': attendance_date.isoformat(),
            'time_in': time_in.strftime('%H:%M:%S') if time_in else None,
            'status': status,
            'marked_by': 'manual',
            'notes': notes,
            'created_at': datetime.utcnow().isoformat()
        }
        res = mongo.db.attendance_records.insert_one(attendance_doc)
        attendance_doc['_id'] = res.inserted_id
        return jsonify({'message': 'Attendance marked successfully', 'attendance': attendance_doc}), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Mark manual attendance error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/attendance/date/<string:date_str>', methods=['GET'])
def get_attendance_by_date(date_str):
    """Get attendance records for specific date"""
    try:
        try:
            attendance_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        class_name = request.args.get('class')
        section = request.args.get('section')
        
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        q = {'date': attendance_date.isoformat()}
        if class_name or section:
            student_q = {'is_active': True}
            if class_name:
                student_q['class_name'] = class_name
            if section:
                student_q['section'] = section
            students = list(mongo.db.students.find(student_q, {'_id': 1, 'full_name': 1, 'roll_number': 1, 'class_name': 1, 'section': 1}))
            student_ids = [str(s.get('_id')) for s in students]
            q['student_id'] = {'$in': student_ids}
        attendance_records = list(mongo.db.attendance_records.find(q))
        attendance_data = []
        for record in attendance_records:
            student_doc = mongo.db.students.find_one({'_id': ObjectId(record.get('student_id'))}) if record.get('student_id') else None
            attendance_data.append({
                'id': str(record.get('_id')),
                'student_id': record.get('student_id'),
                'student_name': student_doc.get('full_name') if student_doc else None,
                'date': record.get('date'),
                'time_in': record.get('time_in'),
                'time_out': record.get('time_out'),
                'status': record.get('status'),
                'marked_by': record.get('marked_by'),
                'notes': record.get('notes')
            })

        return jsonify({'date': date_str, 'attendance': attendance_data, 'count': len(attendance_data)}), 200
    
    except Exception as e:
        print(f"Get attendance by date error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/attendance/<attendance_id>', methods=['DELETE'])
def delete_attendance_record(attendance_id):
    """Delete a specific attendance record"""
    try:
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        try:
            aid = ObjectId(attendance_id) if ObjectId.is_valid(attendance_id) else attendance_id
        except Exception:
            aid = attendance_id
        rec = None
        if isinstance(aid, ObjectId):
            rec = mongo.db.attendance_records.find_one({'_id': aid})
        else:
            rec = mongo.db.attendance_records.find_one({'_id': aid})

        if not rec:
            return jsonify({'error': 'Attendance record not found'}), 404

        rec_out = rec.copy()
        rec_out['id'] = str(rec_out.get('_id'))
        mongo.db.attendance_records.delete_one({'_id': rec.get('_id')})
        return jsonify({'message': 'Attendance record deleted successfully', 'attendance': rec_out}), 200

    except Exception as e:
        db.session.rollback()
        print(f"Delete attendance record error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/attendance/student/<student_id>', methods=['GET'])
def get_student_attendance_history(student_id):
    """Get attendance history for specific student"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        try:
            sdoc = mongo.db.students.find_one({'_id': ObjectId(student_id)})
        except Exception:
            return jsonify({'error': 'Invalid student id'}), 400
        if not sdoc:
            return jsonify({'error': 'Student not found'}), 404

        q = {'student_id': str(sdoc.get('_id'))}
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                q['date'] = {'$gte': start_date.isoformat()}
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                if 'date' in q:
                    q['date']['$lte'] = end_date.isoformat()
                else:
                    q['date'] = {'$lte': end_date.isoformat()}
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400

        records = list(mongo.db.attendance_records.find(q).sort('date', -1))
        attendance_data = []
        for r in records:
            attendance_data.append({
                'id': str(r.get('_id')),
                'student_id': r.get('student_id'),
                'date': r.get('date'),
                'time_in': r.get('time_in'),
                'time_out': r.get('time_out'),
                'status': r.get('status'),
                'confidence_score': r.get('confidence_score'),
                'marked_by': r.get('marked_by'),
                'notes': r.get('notes')
            })

        return jsonify({'student': _mongo_student_to_dict(sdoc), 'attendance_history': attendance_data, 'count': len(attendance_data)}), 200
    
    except Exception as e:
        print(f"Get student attendance history error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/attendance/statistics', methods=['GET'])
def get_attendance_statistics():
    """Return dashboard statistics (total students, present today, rate, alertsCount).
    Optional query params: class, section
    """
    try:
        class_name = request.args.get('class')
        section = request.args.get('section')
        today = datetime.now().date()

        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500

        student_filter = {'is_active': True}
        if class_name:
            student_filter['class_name'] = class_name
        if section:
            student_filter['section'] = section

        total_students = mongo.db.students.count_documents(student_filter)

        # Prepare attendance filter for today
        date_str = today.isoformat()
        attendance_filter = {'date': date_str}
        # restrict by student ids if class/section filters present
        if class_name or section:
            students = list(mongo.db.students.find(student_filter, {'_id': 1}))
            student_ids = [str(s.get('_id')) for s in students]
            attendance_filter['student_id'] = {'$in': student_ids} if student_ids else {'$in': []}

        present_today = mongo.db.attendance_records.count_documents({**attendance_filter, 'status': 'present'})
        absent_today = mongo.db.attendance_records.count_documents({**attendance_filter, 'status': 'absent'})

        rate = round((present_today / total_students) * 100, 2) if total_students else 0.0

        # trend for last 7 days
        trend_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            ds = day.isoformat()
            day_filter = {'date': ds}
            if class_name or section:
                day_filter['student_id'] = attendance_filter.get('student_id', {'$in': []})
            p_count = mongo.db.attendance_records.count_documents({**day_filter, 'status': 'present'})
            a_count = mongo.db.attendance_records.count_documents({**day_filter, 'status': 'absent'})
            l_count = mongo.db.attendance_records.count_documents({**day_filter, 'status': 'late'})
            trend_data.append({
                'date': day.strftime('%m-%d'),
                'present': p_count,
                'absent': a_count,
                'late': l_count
            })

        return jsonify({'statistics': {
            'totalStudents': total_students,
            'presentToday': present_today,
            'attendanceRate': rate,
            'alertsCount': absent_today,
            'trend': trend_data
        }}), 200
    except Exception as e:
        print(f"Get attendance statistics error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

import base64
import json
import os
from io import BytesIO

# Optional heavy deps (CV/face recognition). Import lazily and handle absence.
HAVE_CV2 = False
HAVE_FACE_RECOG = False
HAVE_NUMPY = False
HAVE_PIL = False
try:
    import cv2
    HAVE_CV2 = True
except Exception:
    cv2 = None

try:
    import face_recognition
    HAVE_FACE_RECOG = True
except Exception:
    face_recognition = None

try:
    import numpy as np
    HAVE_NUMPY = True
except Exception:
    np = None

from flask import send_file
try:
    from PIL import Image
    HAVE_PIL = True
except Exception:
    Image = None
from werkzeug.utils import secure_filename


# Face Recognition Endpoints
@app.route('/api/students/<student_id>/upload-photo', methods=['POST'])
def upload_student_photo(student_id):
    """Upload or capture student photo (file or base64) and register face"""
    try:
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        # find student
        try:
            student = mongo.db.students.find_one({'_id': ObjectId(student_id)}) if ObjectId.is_valid(student_id) else mongo.db.students.find_one({'_id': student_id})
        except Exception:
            return jsonify({'error': 'Invalid student id'}), 400
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        image_array = None
        saved_filepath = None

        if 'image_data' in request.form:
            try:
                image_data = request.form['image_data']
                if image_data.startswith('data:image'):
                    image_data = image_data.split(',', 1)[1]
                image_bytes = base64.b64decode(image_data)
                pil_image = Image.open(BytesIO(image_bytes)).convert('RGB')
                image_array = np.array(pil_image)
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = secure_filename(f"student_{student_id}_capture.png")
                saved_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pil_image.save(saved_filepath)
            except Exception as e:
                return jsonify({'error': f'Invalid image data: {str(e)}'}), 400
        elif 'photo' in request.files:
            file = request.files['photo']
            if not file or file.filename == '':
                return jsonify({'error': 'No photo selected'}), 400
            filename = secure_filename(f"student_{student_id}_{file.filename}")
            saved_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(saved_filepath), exist_ok=True)
            file.save(saved_filepath)
            try:
                image_array = face_recognition.load_image_file(saved_filepath)
            except Exception as e:
                if saved_filepath and os.path.exists(saved_filepath):
                    os.remove(saved_filepath)
                return jsonify({'error': f'Failed to read uploaded image: {str(e)}'}), 400
        else:
            return jsonify({'error': 'No photo or image data provided'}), 400

        try:
            face_encodings = face_recognition.face_encodings(image_array)
            if len(face_encodings) == 0:
                if saved_filepath and os.path.exists(saved_filepath):
                    os.remove(saved_filepath)
                return jsonify({'error': 'No face detected in the image.'}), 400
            if len(face_encodings) > 1:
                return jsonify({'error': 'Multiple faces detected. Provide a single face image.'}), 400

            face_encoding = face_encodings[0].tolist()
            updates = {
                'face_encodings': [face_encoding],
                'profile_image': os.path.basename(saved_filepath) if saved_filepath else student.get('profile_image'),
                'updated_at': datetime.utcnow().isoformat()
            }
            mongo.db.students.update_one({'_id': student.get('_id')}, {'$set': updates})
            newdoc = mongo.db.students.find_one({'_id': student.get('_id')})
            return jsonify({'message': 'Photo captured and face registered successfully!', 'student': _mongo_student_to_dict(newdoc)}), 200
        except Exception as e:
            if saved_filepath and os.path.exists(saved_filepath):
                os.remove(saved_filepath)
            return jsonify({'error': f'Face processing failed: {str(e)}'}), 400

    except Exception as e:
        print(f"Upload photo error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/attendance/recognize', methods=['POST'])
def recognize_faces_for_attendance():
    """Recognize faces in uploaded image and mark attendance"""
    try:
        print(f"Face recognition request received")
        print(f"Request files: {list(request.files.keys())}")
        image_array = None
        temp_filepath = None
        
        # Check if it's a base64 image from camera capture
        if 'image_data' in request.form:
            try:
                # Handle base64 encoded image
                image_data = request.form['image_data']
                if image_data.startswith('data:image'):
                    # Remove data URL prefix
                    image_data = image_data.split(',')[1]
                
                # Decode base64 image
                image_bytes = base64.b64decode(image_data)
                pil_image = Image.open(BytesIO(image_bytes)).convert('RGB')
                
                # Convert PIL image to numpy array for face_recognition
                image_array = np.array(pil_image)
                
                print(f"Processed base64 image, size: {image_array.shape}")
                
            except Exception as e:
                print(f"Error processing base64 image: {e}")
                return jsonify({'error': f'Invalid image data: {str(e)}'}), 400
        
        # Fallback to file upload
        elif 'photo' in request.files:
            file = request.files['photo']
            if not file or file.filename == '':
                return jsonify({'error': 'No photo selected'}), 400
            
            # Save temporary file
            temp_filename = secure_filename(f"temp_{file.filename}")
            temp_filepath = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
            file.save(temp_filepath)
        else:
            print("Error: No photo in request.files and no image_data in form")
            return jsonify({'error': 'No photo or image data provided'}), 400
        
        try:
            # Load and process the image
            if image_array is not None:
                # Use the numpy array directly
                image = image_array
            else:
                # Load from file
                image = face_recognition.load_image_file(temp_filepath)
            
            face_locations = face_recognition.face_locations(image)
            face_encodings = face_recognition.face_encodings(image, face_locations)
            
            if len(face_encodings) == 0:
                if temp_filepath and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                return jsonify({'error': 'No faces detected in the image'}), 400
            
            # Get all students with face encodings
            recognized_students = []
            if not mongo:
                if temp_filepath and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                return jsonify({'error': 'MongoDB not configured'}), 500

            students_with_faces = list(mongo.db.students.find({'face_encodings': {'$exists': True, '$ne': []}, 'is_active': True}))
            if not students_with_faces:
                if temp_filepath and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                return jsonify({'error': 'No registered student faces found'}), 400

            for face_encoding in face_encodings:
                best_match = None
                best_distance = float('inf')
                for sdoc in students_with_faces:
                    stored_list = sdoc.get('face_encodings') or []
                    for stored_encoding in stored_list:
                        try:
                            distance = face_recognition.face_distance([np.array(stored_encoding)], face_encoding)[0]
                        except Exception:
                            continue
                        if distance < 0.6 and distance < best_distance:
                            best_match = sdoc
                            best_distance = distance

                if best_match:
                    confidence = max(0, 100 - (best_distance * 100))
                    today = datetime.now().date().isoformat()
                    sid = str(best_match.get('_id'))
                    existing_attendance = mongo.db.attendance_records.find_one({'student_id': sid, 'date': today})
                    if existing_attendance:
                        recognized_students.append({
                            'student_id': sid,
                            'student_name': best_match.get('full_name'),
                            'roll_number': best_match.get('roll_number'),
                            'confidence': round(confidence, 2),
                            'already_marked': True,
                            'existing_status': existing_attendance.get('status'),
                            'existing_time': existing_attendance.get('time_in')
                        })
                    else:
                        attendance_doc = {
                            'student_id': sid,
                            'date': today,
                            'time_in': datetime.now().strftime('%H:%M:%S'),
                            'status': 'present',
                            'confidence_score': confidence,
                            'marked_by': 'face_recognition',
                            'notes': 'Automatically marked via face recognition',
                            'created_at': datetime.utcnow().isoformat()
                        }
                        res = mongo.db.attendance_records.insert_one(attendance_doc)
                        attendance_doc['id'] = str(res.inserted_id)
                        recognized_students.append({
                            'student_id': sid,
                            'student_name': best_match.get('full_name'),
                            'roll_number': best_match.get('roll_number'),
                            'confidence': round(confidence, 2),
                            'already_marked': False,
                            'status': 'present',
                            'time_marked': attendance_doc.get('time_in')
                        })
            
            # Clean up temp file if it exists
            if temp_filepath and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            
            return jsonify({
                'message': f'Recognized {len(recognized_students)} student(s)',
                'recognized_students': recognized_students,
                'faces_detected': len(face_encodings),
                'students_recognized': len(recognized_students)
            }), 200
            
        except Exception as e:
            if temp_filepath and os.path.exists(temp_filepath):
                os.remove(temp_filepath)
            return jsonify({'error': f'Face recognition failed: {str(e)}'}), 400
    
    except Exception as e:
        print(f"Face recognition error: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/students/<student_id>/photo', methods=['GET'])
def get_student_photo(student_id):
    """Get student profile photo"""
    try:
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        try:
            sdoc = mongo.db.students.find_one({'_id': ObjectId(student_id)}) if ObjectId.is_valid(student_id) else mongo.db.students.find_one({'_id': student_id})
        except Exception:
            return jsonify({'error': 'Invalid student id'}), 400
        if not sdoc or not sdoc.get('profile_image'):
            return jsonify({'error': 'Photo not found'}), 404
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], sdoc.get('profile_image'))
        if not os.path.exists(photo_path):
            return jsonify({'error': 'Photo file not found'}), 404
        return send_file(photo_path)
    
    except Exception as e:
        return jsonify({'error': f'Failed to retrieve photo: {str(e)}'}), 500

# Try to import models and routes
def _migrate_sqlite_roll_index():
    """For SQLite, rebuild 'students' table to drop global UNIQUE on roll_number and add composite UNIQUE (class_name, section, roll_number).
    This is required because SQLite cannot drop a UNIQUE index created by a table constraint directly.
    """
    try:
        engine = db.engine
        if not engine.url.drivername.startswith('sqlite'):
            return
        conn = engine.raw_connection()
        cur = conn.cursor()

        # Detect if there is a unique constraint only on roll_number
        cur.execute("PRAGMA index_list('students')")
        indexes = cur.fetchall()
        has_roll_unique_only = False
        for _, idx_name, is_unique, *_ in indexes:
            if not is_unique:
                continue
            cur.execute(f"PRAGMA index_info('{idx_name}')")
            cols = [r[2] for r in cur.fetchall()]
            if cols == ['roll_number']:
                has_roll_unique_only = True
                break

        if not has_roll_unique_only:
            # Nothing to do
            cur.close()
            conn.close()
            return

        print("Rebuilding SQLite 'students' table to adjust roll number uniqueness…")
        cur.execute("PRAGMA foreign_keys=OFF")
        cur.execute("BEGIN TRANSACTION")

        # Create new table with desired schema
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS students_new (
                id INTEGER PRIMARY KEY,
                roll_number VARCHAR(50) NOT NULL,
                admission_number VARCHAR(50) UNIQUE NOT NULL,
                full_name VARCHAR(200) NOT NULL,
                class_name VARCHAR(50) NOT NULL,
                section VARCHAR(10) NOT NULL,
                date_of_birth DATE,
                parent_contact VARCHAR(15),
                parent_email VARCHAR(120),
                address TEXT,
                face_encodings TEXT,
                profile_image VARCHAR(255),
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                CONSTRAINT uq_students_class_section_roll UNIQUE (class_name, section, roll_number)
            )
            """
        )

        # Copy data
        cur.execute(
            """
            INSERT INTO students_new (
                id, roll_number, admission_number, full_name, class_name, section,
                date_of_birth, parent_contact, parent_email, address, face_encodings,
                profile_image, is_active, created_at, updated_at
            )
            SELECT id, roll_number, admission_number, full_name, class_name, section,
                   date_of_birth, parent_contact, parent_email, address, face_encodings,
                   profile_image, is_active, created_at, updated_at
            FROM students
            """
        )

        # Replace old table
        cur.execute("DROP TABLE students")
        cur.execute("ALTER TABLE students_new RENAME TO students")

        # Recreate helpful indexes
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_class_section ON students(class_name, section)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_students_roll_number ON students(roll_number)")

        cur.execute("COMMIT")
        cur.execute("PRAGMA foreign_keys=ON")
        cur.close()
        conn.close()
        print("SQLite students table rebuilt successfully")
    except Exception as e:
        try:
            cur.execute("ROLLBACK")
        except Exception:
            pass
        print(f"SQLite migration warning: {e}")

@app.route('/api/attendance/<attendance_id>/status', methods=['PUT'])
def update_attendance_status(attendance_id):
    try:
        data = request.get_json(force=True)
        new_status = data.get('status')
        if new_status not in ['present', 'absent', 'late']:
            return jsonify({'error': 'Invalid status'}), 400
        if not mongo:
            return jsonify({'error': 'MongoDB not configured'}), 500
        try:
            aid = ObjectId(attendance_id) if ObjectId.is_valid(attendance_id) else attendance_id
        except Exception:
            aid = attendance_id
        rec = mongo.db.attendance_records.find_one({'_id': aid}) if isinstance(aid, ObjectId) else mongo.db.attendance_records.find_one({'_id': aid})
        if not rec:
            return jsonify({'error': 'Attendance record not found'}), 404
        mongo.db.attendance_records.update_one({'_id': rec.get('_id')}, {'$set': {'status': new_status, 'updated_at': datetime.utcnow().isoformat()}})
        rec_updated = mongo.db.attendance_records.find_one({'_id': rec.get('_id')})
        rec_updated['id'] = str(rec_updated.get('_id'))
        return jsonify({'message': 'Status updated', 'attendance': rec_updated}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/classes', methods=['GET', 'POST'])
def handle_classes():
    if not mongo:
        return jsonify({'error': 'MongoDB not configured'}), 500
    if request.method == 'GET':
        docs = list(mongo.db.classes.find())
        classes = []
        for d in docs:
            classes.append({'id': str(d.get('_id')), 'name': d.get('name'), 'section': d.get('section'), 'academic_year': d.get('academic_year')})
        return jsonify({'classes': classes}), 200
    elif request.method == 'POST':
        data = request.get_json(force=True)
        doc = {'name': data.get('name'), 'section': data.get('section'), 'academic_year': data.get('academic_year'), 'created_at': datetime.utcnow().isoformat()}
        res = mongo.db.classes.insert_one(doc)
        doc['id'] = str(res.inserted_id)
        return jsonify({'message': 'Class created', 'class': doc}), 201

@app.route('/api/classes/<class_id>', methods=['PUT', 'DELETE'])
def manage_class(class_id):
    if not mongo:
        return jsonify({'error': 'MongoDB not configured'}), 500
    try:
        cid = ObjectId(class_id) if ObjectId.is_valid(class_id) else class_id
    except Exception:
        cid = class_id
    doc = mongo.db.classes.find_one({'_id': cid}) if isinstance(cid, ObjectId) else mongo.db.classes.find_one({'_id': cid})
    if not doc:
        return jsonify({'error': 'Class not found'}), 404
    if request.method == 'DELETE':
        mongo.db.users.update_many({'class_id': str(doc.get('_id'))}, {'$set': {'class_id': None}})
        mongo.db.classes.delete_one({'_id': doc.get('_id')})
        return jsonify({'message': 'Class deleted'}), 200
    elif request.method == 'PUT':
        data = request.get_json(force=True)
        updates = {
            'name': data.get('name', doc.get('name')),
            'section': data.get('section', doc.get('section')),
            'academic_year': data.get('academic_year', doc.get('academic_year')),
            'updated_at': datetime.utcnow().isoformat()
        }
        mongo.db.classes.update_one({'_id': doc.get('_id')}, {'$set': updates})
        newdoc = mongo.db.classes.find_one({'_id': doc.get('_id')})
        newdoc['id'] = str(newdoc.get('_id'))
        return jsonify({'message': 'Class updated', 'class': newdoc}), 200

@app.route('/api/admin/teachers', methods=['GET', 'POST'])
def handle_teachers():
    if not mongo:
        return jsonify({'error': 'MongoDB not configured'}), 500
    if request.method == 'GET':
        docs = list(mongo.db.users.find({'role': 'teacher'}))
        teachers = [ _mongo_user_to_dict(d) for d in docs ]
        return jsonify({'teachers': teachers}), 200
    elif request.method == 'POST':
        data = request.get_json(force=True)
        from werkzeug.security import generate_password_hash
        doc = {
            'username': data.get('username'),
            'email': data.get('email'),
            'full_name': data.get('full_name'),
            'role': 'teacher',
            'password_hash': generate_password_hash(data.get('password')),
            'class_id': data.get('class_id'),
            'is_active': True,
            'created_at': datetime.utcnow().isoformat()
        }
        res = mongo.db.users.insert_one(doc)
        doc['_id'] = res.inserted_id
        return jsonify({'message': 'Teacher created', 'teacher': _mongo_user_to_dict(doc)}), 201

@app.route('/api/admin/teachers/<teacher_id>', methods=['PUT', 'DELETE'])
def manage_teacher(teacher_id):
    if not mongo:
        return jsonify({'error': 'MongoDB not configured'}), 500
    try:
        tid = ObjectId(teacher_id) if ObjectId.is_valid(teacher_id) else teacher_id
    except Exception:
        tid = teacher_id
    teacher = mongo.db.users.find_one({'_id': tid, 'role': 'teacher'}) if isinstance(tid, ObjectId) else mongo.db.users.find_one({'_id': tid, 'role': 'teacher'})
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404
    if request.method == 'DELETE':
        mongo.db.users.delete_one({'_id': teacher.get('_id')})
        return jsonify({'message': 'Teacher deleted'}), 200
    elif request.method == 'PUT':
        data = request.get_json(force=True)
        from werkzeug.security import generate_password_hash
        updates = {}
        if 'full_name' in data:
            updates['full_name'] = data['full_name']
        if 'email' in data:
            updates['email'] = data['email']
        if 'is_active' in data:
            updates['is_active'] = data['is_active']
        if 'class_id' in data:
            updates['class_id'] = data['class_id'] if data['class_id'] != '' else None
        if data.get('password'):
            updates['password_hash'] = generate_password_hash(data['password'])
        if updates:
            mongo.db.users.update_one({'_id': teacher.get('_id')}, {'$set': updates})
        newt = mongo.db.users.find_one({'_id': teacher.get('_id')})
        return jsonify({'message': 'Teacher updated', 'teacher': _mongo_user_to_dict(newt)}), 200
        if 'email' in data:
            teacher.email = data['email']
        if 'is_active' in data:
            teacher.is_active = data['is_active']
        if 'class_id' in data:
            teacher.class_id = data['class_id'] if data['class_id'] != '' else None
        if data.get('password'):
            from werkzeug.security import generate_password_hash
            teacher.password_hash = generate_password_hash(data['password'])
        db.session.commit()
        return jsonify({'message': 'Teacher updated', 'teacher': teacher.to_dict()}), 200

try:
    # Import and create all tables
    with app.app_context():
        if db is not None:
            db.create_all()
            _migrate_sqlite_roll_index()
    print("OK Database tables created successfully")
    
    print("OK Successfully started Flask application")
except Exception as e:
    print(f"Warning: Database setup failed: {e}")
    print("Application will run with basic routes only")

if __name__ == '__main__':
    with app.app_context():
        if db is not None:
            db.create_all()
    # Use environment-provided PORT (Render/Fly provide this) and FLASK_ENV
    port = int(os.environ.get('PORT', os.environ.get('FLASK_RUN_PORT', 5000)))
    flask_env = os.environ.get('FLASK_ENV', os.environ.get('ENV', 'production'))
    debug_mode = False if str(flask_env).lower() == 'production' else True
    print(f"Starting Flask app on port={port} FLASK_ENV={flask_env} debug={debug_mode}")
    app.run(debug=debug_mode, host='0.0.0.0', port=port)