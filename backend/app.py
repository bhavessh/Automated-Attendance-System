import json
import os
from datetime import datetime, timedelta

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager, create_access_token
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

# Load environment variables
load_dotenv()

# Initialize Flask app
base_dir = os.path.dirname(os.path.abspath(__file__))
instance_dir = os.path.join(base_dir, 'instance')
app = Flask(__name__, instance_path=instance_dir, instance_relative_config=True)
CORS(
    app,
    origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3001"
    ],
    supports_credentials=True
)


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
db = SQLAlchemy(app)
#cors = CORS(app)
jwt = JWTManager(app)

# Create upload directories if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Import models and routes after app initialization
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Create basic test route for now
@app.route('/api/health')
def health_check():
    return {'status': 'ok', 'message': 'Attendance System API is running'}

@app.route('/api/test')
def test_route():
    return {'message': 'Test endpoint working', 'database_uri': app.config['SQLALCHEMY_DATABASE_URI']}

# School Class model
class SchoolClass(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    section = db.Column(db.String(10), nullable=False)
    academic_year = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    
    def to_dict(self):
        # Find teacher assigned to this class
        teacher = User.query.filter_by(class_id=self.id).first()
        return {
            'id': self.id,
            'name': self.name,
            'section': self.section,
            'academic_year': self.academic_year,
            'teacher_name': teacher.full_name if teacher else None
        }

# Simple User model for authentication
class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default='teacher')
    full_name = db.Column(db.String(200), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())
    
    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'full_name': self.full_name,
            'is_active': self.is_active,
            'class_id': self.class_id
        }

# System settings stored as JSON
class SystemSetting(db.Model):
    __tablename__ = 'system_settings'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(120), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.utcnow())

    def to_dict(self):
        return {
            'key': self.key,
            'value': self.value,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

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
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            access_token = create_access_token(identity=user.id)
            return jsonify({
                'access_token': access_token,
                'user': user.to_dict(),
                'message': 'Login successful'
            }), 200
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
    
    except Exception as e:
        print(f"Login error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

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
        
        query = Student.query.filter_by(is_active=True)
        
        if class_name:
            query = query.filter(Student.class_name == class_name)
        
        if section:
            query = query.filter(Student.section == section)
        
        if search:
            query = query.filter(
                db.or_(
                    Student.full_name.contains(search),
                    Student.roll_number.contains(search),
                    Student.admission_number.contains(search)
                )
            )
        
        students = query.all()
        students_data = [student.to_dict() for student in students]
        
        return jsonify({'students': students_data, 'count': len(students_data)}), 200
    
    except Exception as e:
        print(f"Get students error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/settings', methods=['GET'])
def get_system_settings():
    """Get system settings"""
    try:
        settings = _get_or_create_settings()
        return jsonify({'settings': json.loads(settings.value)}), 200
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

        settings = _get_or_create_settings()
        settings.value = json.dumps(data)
        settings.updated_at = datetime.utcnow()
        db.session.commit()

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

        query = db.session.query(
            AttendanceRecord.date.label('date'),
            db.func.count(AttendanceRecord.id).label('total'),
            db.func.sum(db.case((AttendanceRecord.status == 'present', 1), else_=0)).label('present'),
            db.func.sum(db.case((AttendanceRecord.status == 'absent', 1), else_=0)).label('absent'),
            db.func.sum(db.case((AttendanceRecord.status == 'late', 1), else_=0)).label('late')
        ).join(Student)

        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        if section:
            query = query.filter(Student.section == section)

        summary = []
        for row in query.group_by(AttendanceRecord.date).order_by(AttendanceRecord.date.desc()).all():
            rate = round((row.present / row.total) * 100, 2) if row.total else 0.0
            summary.append({
                'date': row.date.isoformat(),
                'total': row.total,
                'present': row.present,
                'absent': row.absent,
                'late': row.late,
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

        query = db.session.query(
            Student.id.label('student_id'),
            Student.full_name.label('student_name'),
            Student.class_name.label('class_name'),
            Student.section.label('section'),
            db.func.count(AttendanceRecord.id).label('total'),
            db.func.sum(db.case((AttendanceRecord.status == 'present', 1), else_=0)).label('present'),
            db.func.sum(db.case((AttendanceRecord.status == 'absent', 1), else_=0)).label('absent'),
            db.func.sum(db.case((AttendanceRecord.status == 'late', 1), else_=0)).label('late')
        ).join(AttendanceRecord, AttendanceRecord.student_id == Student.id)

        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)
        if class_name:
            query = query.filter(Student.class_name == class_name)
        if section:
            query = query.filter(Student.section == section)

        analytics = []
        for row in query.group_by(Student.id).order_by(Student.full_name).all():
            rate = round((row.present / row.total) * 100, 2) if row.total else 0.0
            analytics.append({
                'student_id': row.student_id,
                'student_name': row.student_name,
                'class_name': row.class_name,
                'section': row.section,
                'total': row.total,
                'present': row.present,
                'absent': row.absent,
                'late': row.late,
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

        query = db.session.query(
            Student.class_name.label('class_name'),
            Student.section.label('section'),
            db.func.count(AttendanceRecord.id).label('total'),
            db.func.sum(db.case((AttendanceRecord.status == 'present', 1), else_=0)).label('present'),
            db.func.sum(db.case((AttendanceRecord.status == 'absent', 1), else_=0)).label('absent'),
            db.func.sum(db.case((AttendanceRecord.status == 'late', 1), else_=0)).label('late')
        ).join(AttendanceRecord, AttendanceRecord.student_id == Student.id)

        if start_date:
            query = query.filter(AttendanceRecord.date >= start_date)
        if end_date:
            query = query.filter(AttendanceRecord.date <= end_date)

        analytics = []
        for row in query.group_by(Student.class_name, Student.section).order_by(Student.class_name, Student.section).all():
            rate = round((row.present / row.total) * 100, 2) if row.total else 0.0
            analytics.append({
                'class_name': row.class_name,
                'section': row.section,
                'total': row.total,
                'present': row.present,
                'absent': row.absent,
                'late': row.late,
                'attendance_rate': rate
            })

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

        records = _attendance_query(start_date, end_date, class_name, section).all()
        export_rows = []
        for record in records:
            export_rows.append({
                'date': record.date.isoformat() if record.date else None,
                'student_id': record.student_id,
                'student_name': record.student.full_name if record.student else None,
                'roll_number': record.student.roll_number if record.student else None,
                'class': record.student.class_name if record.student else None,
                'section': record.student.section if record.student else None,
                'status': record.status,
                'time_in': record.time_in.strftime('%H:%M:%S') if record.time_in else None,
                'time_out': record.time_out.strftime('%H:%M:%S') if record.time_out else None,
                'marked_by': record.marked_by
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

        existing_adm = Student.query.filter(Student.admission_number == admission_number).first()
        if existing_adm:
            return jsonify({'error': 'A student with this admission number already exists'}), 400

        existing_roll = Student.query.filter(
            db.and_(
                Student.roll_number == roll_number,
                Student.class_name == class_name,
                Student.section == section
            )
        ).first()
        if existing_roll:
            return jsonify({'error': 'A student with this roll number already exists in this class and section'}), 400
        
        # Parse date if provided
        date_of_birth = None
        if data.get('date_of_birth'):
            try:
                date_of_birth = datetime.strptime(data.get('date_of_birth'), '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
        
        # Create new student
        student = Student(
            roll_number=data.get('roll_number'),
            admission_number=data.get('admission_number'),
            full_name=data.get('full_name'),
            class_name=data.get('class_name'),
            section=data.get('section'),
            date_of_birth=date_of_birth,
            parent_contact=data.get('parent_contact'),
            parent_email=data.get('parent_email'),
            address=data.get('address')
        )
        
        db.session.add(student)
        db.session.commit()
        
        return jsonify({
            'message': 'Student created successfully',
            'student': student.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        print(f"Create student error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/students/<int:student_id>', methods=['PUT'])
def update_student(student_id):
    """Update student details with uniqueness validation"""
    try:
        data = request.get_json(force=True)
        if not data or not isinstance(data, dict):
            return jsonify({'error': 'Invalid JSON data'}), 400

        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        full_name = data.get('full_name', student.full_name)
        class_name = data.get('class_name', student.class_name)
        section = data.get('section', student.section)
        roll_number = data.get('roll_number', student.roll_number)
        admission_number = data.get('admission_number', student.admission_number)

        # Admission number global uniqueness (exclude self)
        exists_adm = Student.query.filter(
            db.and_(Student.admission_number == admission_number, Student.id != student_id)
        ).first()
        if exists_adm:
            return jsonify({'error': 'A student with this admission number already exists'}), 400

        # Roll number unique per class+section (exclude self)
        exists_roll = Student.query.filter(
            db.and_(
                Student.roll_number == roll_number,
                Student.class_name == class_name,
                Student.section == section,
                Student.id != student_id
            )
        ).first()
        if exists_roll:
            return jsonify({'error': 'A student with this roll number already exists in this class and section'}), 400

        # Apply updates
        student.full_name = full_name
        student.class_name = class_name
        student.section = section
        student.roll_number = roll_number
        student.admission_number = admission_number
        student.parent_contact = data.get('parent_contact', student.parent_contact)
        student.parent_email = data.get('parent_email', student.parent_email)
        student.address = data.get('address', student.address)

        if 'date_of_birth' in data:
            dob_value = data.get('date_of_birth')
            if dob_value:
                try:
                    student.date_of_birth = datetime.strptime(dob_value, '%Y-%m-%d').date()
                except ValueError:
                    return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
            else:
                student.date_of_birth = None

        db.session.commit()
        return jsonify({'message': 'Student updated successfully', 'student': student.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        print(f"Update student error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/students/<int:student_id>', methods=['DELETE'])
def delete_student(student_id):
    """Delete a student and their attendance records"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        AttendanceRecord.query.filter_by(student_id=student_id).delete()
        db.session.delete(student)
        db.session.commit()
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
        
        # Check if student exists
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        # Check if attendance already exists for this date
        existing_record = AttendanceRecord.query.filter_by(
            student_id=student_id,
            date=attendance_date
        ).first()
        
        if existing_record:
            return jsonify({'error': 'Attendance already marked for this date'}), 400
        
        # Create attendance record
        attendance = AttendanceRecord(
            student_id=student_id,
            date=attendance_date,
            time_in=time_in,
            status=status,
            marked_by='manual',
            notes=notes
        )
        
        db.session.add(attendance)
        db.session.commit()
        
        return jsonify({
            'message': 'Attendance marked successfully',
            'attendance': attendance.to_dict()
        }), 201
    
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
        
        # Build query
        query = db.session.query(AttendanceRecord).join(Student).filter(
            AttendanceRecord.date == attendance_date
        )
        
        if class_name:
            query = query.filter(Student.class_name == class_name)
        
        if section:
            query = query.filter(Student.section == section)
        
        attendance_records = query.all()
        attendance_data = [record.to_dict() for record in attendance_records]
        
        return jsonify({
            'date': date_str,
            'attendance': attendance_data,
            'count': len(attendance_data)
        }), 200
    
    except Exception as e:
        print(f"Get attendance by date error: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/attendance/<int:attendance_id>', methods=['DELETE'])
def delete_attendance_record(attendance_id):
    """Delete a specific attendance record"""
    try:
        record = AttendanceRecord.query.get(attendance_id)
        if not record:
            return jsonify({'error': 'Attendance record not found'}), 404

        # Serialize before deleting to avoid session issues
        record_dict = record.to_dict()
        db.session.delete(record)
        db.session.commit()

        return jsonify({
            'message': 'Attendance record deleted successfully',
            'attendance': record_dict
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Delete attendance record error: {str(e)}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/api/attendance/student/<int:student_id>', methods=['GET'])
def get_student_attendance_history(student_id):
    """Get attendance history for specific student"""
    try:
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        
        # Check if student exists
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404
        
        query = AttendanceRecord.query.filter_by(student_id=student_id)
        
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                query = query.filter(AttendanceRecord.date >= start_date)
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                query = query.filter(AttendanceRecord.date <= end_date)
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        attendance_records = query.order_by(AttendanceRecord.date.desc()).all()
        attendance_data = [record.to_dict() for record in attendance_records]
        
        return jsonify({
            'student': student.to_dict(),
            'attendance_history': attendance_data,
            'count': len(attendance_data)
        }), 200
    
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

        students_q = Student.query.filter_by(is_active=True)
        if class_name:
            students_q = students_q.filter(Student.class_name == class_name)
        if section:
            students_q = students_q.filter(Student.section == section)
        total_students = students_q.count()

        ar_q = db.session.query(AttendanceRecord).join(Student).filter(AttendanceRecord.date == today)
        if class_name:
            ar_q = ar_q.filter(Student.class_name == class_name)
        if section:
            ar_q = ar_q.filter(Student.section == section)
        present_today = ar_q.filter(AttendanceRecord.status == 'present').count()
        absent_today = ar_q.filter(AttendanceRecord.status == 'absent').count()

        rate = round((present_today / total_students) * 100, 2) if total_students else 0.0

        # Calculate trend for last 7 days
        trend_data = []
        for i in range(6, -1, -1):
            day = today - timedelta(days=i)
            day_q = db.session.query(AttendanceRecord).join(Student).filter(AttendanceRecord.date == day)
            if class_name:
                day_q = day_q.filter(Student.class_name == class_name)
            if section:
                day_q = day_q.filter(Student.section == section)
            
            p_count = day_q.filter(AttendanceRecord.status == 'present').count()
            a_count = day_q.filter(AttendanceRecord.status == 'absent').count()
            l_count = day_q.filter(AttendanceRecord.status == 'late').count()
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

import cv2
# Face Recognition Service
import face_recognition
import numpy as np
from flask import send_file
from PIL import Image
from werkzeug.utils import secure_filename


# Face Recognition Endpoints
@app.route('/api/students/<int:student_id>/upload-photo', methods=['POST'])
def upload_student_photo(student_id):
    """Upload or capture student photo (file or base64) and register face"""
    try:
        print(f"Upload photo request for student {student_id}")
        print(f"Request files: {list(request.files.keys())}")
        # Check if student exists first
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'error': 'Student not found'}), 404

        image_array = None
        saved_filepath = None

        # Path A: base64 image from webcam via 'image_data'
        if 'image_data' in request.form:
            try:
                image_data = request.form['image_data']
                if image_data.startswith('data:image'):
                    # Remove "data:image/png;base64," prefix
                    image_data = image_data.split(',', 1)[1]
                image_bytes = base64.b64decode(image_data)
                pil_image = Image.open(BytesIO(image_bytes)).convert('RGB')
                image_array = np.array(pil_image)

                # Save a copy as profile image
                os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
                filename = secure_filename(f"student_{student_id}_capture.png")
                saved_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                pil_image.save(saved_filepath)
            except Exception as e:
                print(f"Error processing base64 image for student upload: {e}")
                return jsonify({'error': f'Invalid image data: {str(e)}'}), 400

        # Path B: traditional file upload under key 'photo'
        elif 'photo' in request.files:
            file = request.files['photo']
            if not file or file.filename == '':
                return jsonify({'error': 'No photo selected'}), 400

            filename = secure_filename(f"student_{student_id}_{file.filename}")
            saved_filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            os.makedirs(os.path.dirname(saved_filepath), exist_ok=True)
            file.save(saved_filepath)

            # Load file to numpy array for encoding
            try:
                image_array = face_recognition.load_image_file(saved_filepath)
            except Exception as e:
                if saved_filepath and os.path.exists(saved_filepath):
                    os.remove(saved_filepath)
                return jsonify({'error': f'Failed to read uploaded image: {str(e)}'}), 400
        else:
            return jsonify({'error': 'No photo or image data provided'}), 400

        # Process face recognition using image_array
        try:
            face_encodings = face_recognition.face_encodings(image_array)

            if len(face_encodings) == 0:
                if saved_filepath and os.path.exists(saved_filepath):
                    os.remove(saved_filepath)
                return jsonify({'error': 'No face detected in the image. Please capture a clear photo with a single visible face.'}), 400

            if len(face_encodings) > 1:
                return jsonify({'error': 'Multiple faces detected. Please capture a photo with only one person.'}), 400

            # Store face encoding and profile image filename
            face_encoding = face_encodings[0].tolist()
            student.face_encodings = json.dumps([face_encoding])
            if saved_filepath:
                student.profile_image = os.path.basename(saved_filepath)

            db.session.commit()

            return jsonify({
                'message': 'Photo captured and face registered successfully!',
                'student': student.to_dict()
            }), 200

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
            students_with_faces = Student.query.filter(
                Student.face_encodings.isnot(None),
                Student.face_encodings != '',
                Student.is_active == True
            ).all()
            
            if not students_with_faces:
                if temp_filepath and os.path.exists(temp_filepath):
                    os.remove(temp_filepath)
                return jsonify({'error': 'No registered student faces found'}), 400
            
            recognized_students = []
            
            # Compare each detected face with known faces
            for face_encoding in face_encodings:
                best_match = None
                best_distance = float('inf')
                
                for student in students_with_faces:
                    try:
                        stored_encodings = json.loads(student.face_encodings)
                        for stored_encoding in stored_encodings:
                            # Calculate face distance
                            distance = face_recognition.face_distance([stored_encoding], face_encoding)[0]
                            
                            # Threshold for face recognition (lower = more strict)
                            if distance < 0.6 and distance < best_distance:
                                best_match = student
                                best_distance = distance
                    except (json.JSONDecodeError, TypeError):
                        continue
                
                if best_match:
                    confidence = max(0, 100 - (best_distance * 100))  # Convert to percentage
                    
                    # Check if attendance already marked today
                    today = datetime.now().date()
                    existing_attendance = AttendanceRecord.query.filter_by(
                        student_id=best_match.id,
                        date=today
                    ).first()
                    
                    if existing_attendance:
                        recognized_students.append({
                            'student_id': best_match.id,
                            'student_name': best_match.full_name,
                            'roll_number': best_match.roll_number,
                            'confidence': round(confidence, 2),
                            'already_marked': True,
                            'existing_status': existing_attendance.status,
                            'existing_time': existing_attendance.time_in.strftime('%H:%M:%S') if existing_attendance.time_in else None
                        })
                    else:
                        # Mark new attendance
                        attendance = AttendanceRecord(
                            student_id=best_match.id,
                            date=today,
                            time_in=datetime.now().time(),
                            status='present',
                            confidence_score=confidence,
                            marked_by='face_recognition',
                            notes='Automatically marked via face recognition'
                        )
                        
                        db.session.add(attendance)
                        db.session.commit()
                        
                        recognized_students.append({
                            'student_id': best_match.id,
                            'student_name': best_match.full_name,
                            'roll_number': best_match.roll_number,
                            'confidence': round(confidence, 2),
                            'already_marked': False,
                            'status': 'present',
                            'time_marked': attendance.time_in.strftime('%H:%M:%S')
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

@app.route('/api/students/<int:student_id>/photo', methods=['GET'])
def get_student_photo(student_id):
    """Get student profile photo"""
    try:
        student = Student.query.get(student_id)
        if not student or not student.profile_image:
            return jsonify({'error': 'Photo not found'}), 404
        
        photo_path = os.path.join(app.config['UPLOAD_FOLDER'], student.profile_image)
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

@app.route('/api/attendance/<int:attendance_id>/status', methods=['PUT'])
def update_attendance_status(attendance_id):
    try:
        data = request.get_json(force=True)
        new_status = data.get('status')
        if new_status not in ['present', 'absent', 'late']:
            return jsonify({'error': 'Invalid status'}), 400
        
        record = AttendanceRecord.query.get(attendance_id)
        if not record:
            return jsonify({'error': 'Attendance record not found'}), 404
            
        record.status = new_status
        record.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Status updated', 'attendance': record.to_dict()}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/classes', methods=['GET', 'POST'])
def handle_classes():
    if request.method == 'GET':
        classes = SchoolClass.query.all()
        return jsonify({'classes': [c.to_dict() for c in classes]}), 200
    elif request.method == 'POST':
        data = request.get_json(force=True)
        new_class = SchoolClass(
            name=data.get('name'),
            section=data.get('section'),
            academic_year=data.get('academic_year')
        )
        db.session.add(new_class)
        db.session.commit()
        return jsonify({'message': 'Class created', 'class': new_class.to_dict()}), 201

@app.route('/api/classes/<int:class_id>', methods=['PUT', 'DELETE'])
def manage_class(class_id):
    school_class = SchoolClass.query.get(class_id)
    if not school_class:
        return jsonify({'error': 'Class not found'}), 404
        
    if request.method == 'DELETE':
        # optionally update users
        User.query.filter_by(class_id=class_id).update({'class_id': None})
        db.session.delete(school_class)
        db.session.commit()
        return jsonify({'message': 'Class deleted'}), 200
    elif request.method == 'PUT':
        data = request.get_json(force=True)
        school_class.name = data.get('name', school_class.name)
        school_class.section = data.get('section', school_class.section)
        school_class.academic_year = data.get('academic_year', school_class.academic_year)
        db.session.commit()
        return jsonify({'message': 'Class updated', 'class': school_class.to_dict()}), 200

@app.route('/api/admin/teachers', methods=['GET', 'POST'])
def handle_teachers():
    if request.method == 'GET':
        teachers = User.query.filter_by(role='teacher').all()
        return jsonify({'teachers': [t.to_dict() for t in teachers]}), 200
    elif request.method == 'POST':
        data = request.get_json(force=True)
        from werkzeug.security import generate_password_hash
        new_teacher = User(
            username=data.get('username'),
            email=data.get('email'),
            full_name=data.get('full_name'),
            role='teacher',
            password_hash=generate_password_hash(data.get('password')),
            class_id=data.get('class_id')
        )
        db.session.add(new_teacher)
        db.session.commit()
        return jsonify({'message': 'Teacher created', 'teacher': new_teacher.to_dict()}), 201

@app.route('/api/admin/teachers/<int:teacher_id>', methods=['PUT', 'DELETE'])
def manage_teacher(teacher_id):
    teacher = User.query.filter_by(id=teacher_id, role='teacher').first()
    if not teacher:
        return jsonify({'error': 'Teacher not found'}), 404
        
    if request.method == 'DELETE':
        db.session.delete(teacher)
        db.session.commit()
        return jsonify({'message': 'Teacher deleted'}), 200
    elif request.method == 'PUT':
        data = request.get_json(force=True)
        if 'full_name' in data:
            teacher.full_name = data['full_name']
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
        db.create_all()
        _migrate_sqlite_roll_index()
    print("OK Database tables created successfully")
    
    print("OK Successfully started Flask application")
except Exception as e:
    print(f"Warning: Database setup failed: {e}")
    print("Application will run with basic routes only")

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, host='0.0.0.0', port=5000)