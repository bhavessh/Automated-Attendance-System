from datetime import datetime, date, time
from app import mongo
from bson.objectid import ObjectId
import logging

class AttendanceService:
    """Service for handling attendance operations with MongoDB support and SQL fallback."""

    def __init__(self):
        self.attendance_window_minutes = 15

    def mark_attendance(self, student_id, confidence_score, marked_by='system', notes=None):
        try:
            today = date.today()
            current_time = datetime.now().time()

            if not mongo:
                return False, 'MongoDB not configured'

            try:
                try:
                    sid = ObjectId(student_id) if ObjectId.is_valid(student_id) else student_id
                except Exception:
                    sid = student_id
                sdoc = mongo.db.students.find_one({'_id': sid}) if isinstance(sid, ObjectId) else mongo.db.students.find_one({'_id': sid})
                if not sdoc:
                    return False, 'Student not found'

                sid_str = str(sdoc.get('_id'))
                existing = mongo.db.attendance_records.find_one({'student_id': sid_str, 'date': today.isoformat()})
                if existing:
                    if existing.get('time_in') and current_time.strftime('%H:%M:%S') > existing.get('time_in'):
                        mongo.db.attendance_records.update_one({'_id': existing.get('_id')}, {'$set': {'time_out': current_time.strftime('%H:%M:%S'), 'updated_at': datetime.utcnow().isoformat()}})
                        return True, f"Updated time out for {sdoc.get('full_name')}"
                    return False, f"Attendance already marked for {sdoc.get('full_name')} today"

                doc = {
                    'student_id': sid_str,
                    'date': today.isoformat(),
                    'time_in': current_time.strftime('%H:%M:%S'),
                    'status': 'present',
                    'confidence_score': confidence_score,
                    'marked_by': marked_by,
                    'notes': notes,
                    'created_at': datetime.utcnow().isoformat()
                }
                mongo.db.attendance_records.insert_one(doc)
                return True, f"Attendance marked for {sdoc.get('full_name')}"
            except Exception as e:
                logging.error(f"Error marking attendance (Mongo): {e}")
                return False, f"Error: {e}"

        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            logging.error(f"Error marking attendance: {e}")
            return False, f"Error: {e}"

    def mark_manual_attendance(self, student_id, attendance_date, status, user_id, notes=None):
        try:
            if not mongo:
                return False, 'MongoDB not configured'
            try:
                try:
                    sid = ObjectId(student_id) if ObjectId.is_valid(student_id) else student_id
                except Exception:
                    sid = student_id
                sdoc = mongo.db.students.find_one({'_id': sid}) if isinstance(sid, ObjectId) else mongo.db.students.find_one({'_id': sid})
                if not sdoc:
                    return False, 'Student not found'

                sid_str = str(sdoc.get('_id'))
                date_str = attendance_date.isoformat() if isinstance(attendance_date, date) else attendance_date
                existing = mongo.db.attendance_records.find_one({'student_id': sid_str, 'date': date_str})
                if existing:
                    mongo.db.attendance_records.update_one({'_id': existing.get('_id')}, {'$set': {'status': status, 'notes': notes, 'marked_by': f'user_{user_id}', 'updated_at': datetime.utcnow().isoformat()}})
                else:
                    doc = {'student_id': sid_str, 'date': date_str, 'status': status, 'marked_by': f'user_{user_id}', 'notes': notes, 'created_at': datetime.utcnow().isoformat()}
                    mongo.db.attendance_records.insert_one(doc)
                return True, f"Manual attendance updated for {sdoc.get('full_name')}"
            except Exception as e:
                logging.error(f"Error marking manual attendance (Mongo): {e}")
                return False, f"Error: {e}"

        except Exception as e:
            try:
                db.session.rollback()
            except Exception:
                pass
            logging.error(f"Error marking manual attendance: {e}")
            return False, f"Error: {e}"

    def get_attendance_by_date(self, attendance_date, class_name=None, section=None):
        try:
            if not mongo:
                return False, 'MongoDB not configured'
            try:
                q = {'date': attendance_date.isoformat() if isinstance(attendance_date, date) else attendance_date}
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
                        return True, []

                records = list(mongo.db.attendance_records.find(q))
                attendance_list = []
                for rec in records:
                    sid = rec.get('student_id')
                    student_doc = None
                    try:
                        student_doc = mongo.db.students.find_one({'_id': ObjectId(sid)}) if ObjectId.is_valid(sid) else mongo.db.students.find_one({'_id': sid})
                    except Exception:
                        student_doc = None
                    attendance_list.append({
                        'id': str(rec.get('_id')),
                        'student_id': rec.get('student_id'),
                        'student_info': {'full_name': student_doc.get('full_name') if student_doc else None, 'roll_number': student_doc.get('roll_number') if student_doc else None, 'class_name': student_doc.get('class_name') if student_doc else None, 'section': student_doc.get('section') if student_doc else None},
                        'date': rec.get('date'),
                        'time_in': rec.get('time_in'),
                        'time_out': rec.get('time_out'),
                        'status': rec.get('status'),
                        'confidence_score': rec.get('confidence_score'),
                        'marked_by': rec.get('marked_by'),
                        'notes': rec.get('notes')
                    })
                return True, attendance_list
            except Exception as e:
                logging.error(f"Error getting attendance by date (Mongo): {e}")
                return False, f"Error: {e}"

        except Exception as e:
            logging.error(f"Error getting attendance by date: {e}")
            return False, f"Error: {e}"

    def get_student_attendance_history(self, student_id, start_date=None, end_date=None):
        try:
            if not mongo:
                return False, 'MongoDB not configured'
            try:
                try:
                    sid = ObjectId(student_id) if ObjectId.is_valid(student_id) else student_id
                except Exception:
                    sid = student_id
                sdoc = mongo.db.students.find_one({'_id': sid}) if isinstance(sid, ObjectId) else mongo.db.students.find_one({'_id': sid})
                if not sdoc:
                    return False, 'Student not found'
                q = {'student_id': str(sdoc.get('_id'))}
                if start_date:
                    q['date'] = q.get('date', {})
                    q['date']['$gte'] = start_date.isoformat()
                if end_date:
                    q['date'] = q.get('date', {})
                    q['date']['$lte'] = end_date.isoformat()
                records = list(mongo.db.attendance_records.find(q).sort('date', -1))
                history = []
                for r in records:
                    history.append({'id': str(r.get('_id')), 'student_id': r.get('student_id'), 'date': r.get('date'), 'time_in': r.get('time_in'), 'time_out': r.get('time_out'), 'status': r.get('status'), 'confidence_score': r.get('confidence_score'), 'marked_by': r.get('marked_by'), 'notes': r.get('notes')})
                return True, history
            except Exception as e:
                logging.error(f"Error getting student attendance history (Mongo): {e}")
                return False, f"Error: {e}"

        except Exception as e:
            logging.error(f"Error getting student attendance history: {e}")
            return False, f"Error: {e}"

    def get_attendance_statistics(self, class_name=None, section=None, start_date=None, end_date=None):
        try:
            if not mongo:
                return False, 'MongoDB not configured'
            try:
                student_q = {'is_active': True}
                if class_name:
                    student_q['class_name'] = class_name
                if section:
                    student_q['section'] = section
                total_students = mongo.db.students.count_documents(student_q)
                att_q = {}
                if class_name or section:
                    sdocs = list(mongo.db.students.find(student_q, {'_id': 1}))
                    sids = [str(s['_id']) for s in sdocs]
                    if sids:
                        att_q['student_id'] = {'$in': sids}
                    else:
                        return True, {'total_students': 0, 'total_records': 0, 'present_records': 0, 'absent_records': 0, 'attendance_percentage': 0, 'daily_statistics': []}
                if start_date:
                    att_q['date'] = att_q.get('date', {})
                    att_q['date']['$gte'] = start_date.isoformat()
                if end_date:
                    att_q['date'] = att_q.get('date', {})
                    att_q['date']['$lte'] = end_date.isoformat()
                total_records = mongo.db.attendance_records.count_documents(att_q)
                present_q = att_q.copy(); present_q['status'] = 'present'
                present_records = mongo.db.attendance_records.count_documents(present_q)
                absent_q = att_q.copy(); absent_q['status'] = 'absent'
                absent_records = mongo.db.attendance_records.count_documents(absent_q)
                attendance_percentage = (present_records / total_records * 100) if total_records > 0 else 0
                pipeline = []
                if att_q:
                    pipeline.append({'$match': att_q})
                pipeline.extend([{'$group': {'_id': '$date', 'total': {'$sum': 1}, 'present': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}}}}, {'$sort': {'_id': 1}}])
                daily_agg = list(mongo.db.attendance_records.aggregate(pipeline))
                daily_stats = [{'date': d.get('_id'), 'total': d.get('total'), 'present': d.get('present'), 'percentage': (d.get('present') / d.get('total') * 100) if d.get('total') else 0} for d in daily_agg]
                return True, {'total_students': total_students, 'total_records': total_records, 'present_records': present_records, 'absent_records': absent_records, 'attendance_percentage': round(attendance_percentage,2), 'daily_statistics': daily_stats}
            except Exception as e:
                logging.error(f"Error getting attendance statistics (Mongo): {e}")
                return False, f"Error: {e}"

        except Exception as e:
            logging.error(f"Error getting attendance statistics: {e}")
            return False, f"Error: {e}"

    def get_irregular_attendance_alerts(self, days_threshold=3):
        try:
            from datetime import timedelta
            end_date = date.today()
            start_date = end_date - timedelta(days=days_threshold)
            irregular_students = []
            if not mongo:
                return False, 'MongoDB not configured'
                students = list(mongo.db.students.find({'is_active': True}))
                for s in students:
                    sid = str(s.get('_id'))
                    q = {'student_id': sid, 'date': {'$gte': start_date.isoformat(), '$lte': end_date.isoformat()}}
                    recent = list(mongo.db.attendance_records.find(q))
                    absent_days = len([r for r in recent if r.get('status') == 'absent'])
                    total_days = len(recent)
                    if absent_days >= days_threshold or (total_days > 0 and absent_days / total_days > 0.5):
                        irregular_students.append({'student': {'id': sid, 'full_name': s.get('full_name')}, 'absent_days': absent_days, 'total_days': total_days, 'absence_rate': (absent_days / total_days * 100) if total_days > 0 else 0})
                return True, irregular_students


        except Exception as e:
            logging.error(f"Error getting irregular attendance alerts: {e}")
            return False, f"Error: {e}"