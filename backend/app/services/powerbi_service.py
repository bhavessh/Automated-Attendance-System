import pandas as pd
import requests
import os
import logging
from datetime import datetime
from app import mongo
from bson.objectid import ObjectId


class PowerBIService:
    """Service for Power BI integration and data export (Mongo-only)."""

    def __init__(self):
        self.workspace_id = os.getenv('POWERBI_WORKSPACE_ID')
        self.dataset_id = os.getenv('POWERBI_DATASET_ID')
        self.client_id = os.getenv('POWERBI_CLIENT_ID')
        self.client_secret = os.getenv('POWERBI_CLIENT_SECRET')
        self.access_token = None

    def authenticate(self):
        try:
            url = "https://login.microsoftonline.com/common/oauth2/token"
            data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'resource': 'https://analysis.windows.net/powerbi/api'
            }
            response = requests.post(url, data=data)
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get('access_token')
                return True, "Authentication successful"
            return False, f"Authentication failed: {response.text}"
        except Exception as e:
            logging.error(f"Power BI authentication error: {e}")
            return False, str(e)

    def export_attendance_data(self, start_date=None, end_date=None):
        try:
            if not mongo:
                return False, 'MongoDB not configured'
            q = {}
            if start_date:
                q['date'] = q.get('date', {}); q['date']['$gte'] = start_date.isoformat()
            if end_date:
                q['date'] = q.get('date', {}); q['date']['$lte'] = end_date.isoformat()
            records = list(mongo.db.attendance_records.find(q))
            export_data = []
            for rec in records:
                sid = rec.get('student_id')
                sdoc = None
                try:
                    sdoc = mongo.db.students.find_one({'_id': ObjectId(sid)}) if ObjectId.is_valid(sid) else mongo.db.students.find_one({'_id': sid})
                except Exception:
                    sdoc = mongo.db.students.find_one({'_id': sid})
                export_data.append({
                    'date': rec.get('date'),
                    'student_id': sid,
                    'student_name': sdoc.get('full_name') if sdoc else None,
                    'roll_number': sdoc.get('roll_number') if sdoc else None,
                    'class': sdoc.get('class_name') if sdoc else None,
                    'section': sdoc.get('section') if sdoc else None,
                    'status': rec.get('status'),
                    'time_in': rec.get('time_in'),
                    'time_out': rec.get('time_out'),
                    'confidence_score': rec.get('confidence_score'),
                    'marked_by': rec.get('marked_by'),
                    'created_at': rec.get('created_at')
                })
            return True, export_data
        except Exception as e:
            logging.error(f"Error exporting attendance data: {e}")
            return False, str(e)

    def export_to_excel(self, data, filename=None):
        try:
            if not filename:
                filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df = pd.DataFrame(data)
            exports_dir = 'exports'
            os.makedirs(exports_dir, exist_ok=True)
            filepath = os.path.join(exports_dir, filename)
            df.to_excel(filepath, index=False)
            return True, filepath
        except Exception as e:
            logging.error(f"Error exporting to Excel: {e}")
            return False, str(e)

    def export_to_csv(self, data, filename=None):
        try:
            if not filename:
                filename = f"attendance_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df = pd.DataFrame(data)
            exports_dir = 'exports'
            os.makedirs(exports_dir, exist_ok=True)
            filepath = os.path.join(exports_dir, filename)
            df.to_csv(filepath, index=False)
            return True, filepath
        except Exception as e:
            logging.error(f"Error exporting to CSV: {e}")
            return False, str(e)

    def push_to_powerbi(self, data):
        try:
            if not self.access_token:
                ok, msg = self.authenticate()
                if not ok:
                    return False, msg
            url = f"https://api.powerbi.com/v1.0/myorg/groups/{self.workspace_id}/datasets/{self.dataset_id}/rows"
            headers = {'Authorization': f'Bearer {self.access_token}', 'Content-Type': 'application/json'}
            response = requests.post(url, headers=headers, json={'rows': data})
            if response.status_code == 200:
                return True, 'Pushed'
            return False, response.text
        except Exception as e:
            logging.error(f"Error pushing to Power BI: {e}")
            return False, str(e)

    def get_dashboard_url(self):
        if not self.workspace_id:
            return False, 'Power BI workspace not configured'
        return True, f"https://app.powerbi.com/groups/{self.workspace_id}/dashboards"

    def generate_attendance_summary(self, start_date=None, end_date=None):
        try:
            if not mongo:
                return False, 'MongoDB not configured'
            match = {}
            if start_date:
                match['date'] = match.get('date', {}); match['date']['$gte'] = start_date.isoformat()
            if end_date:
                match['date'] = match.get('date', {}); match['date']['$lte'] = end_date.isoformat()
            pipeline = []
            if match:
                pipeline.append({'$match': match})
            pipeline.extend([
                {'$group': {'_id': '$date', 'total_records': {'$sum': 1}, 'present_count': {'$sum': {'$cond': [{'$eq': ['$status', 'present']}, 1, 0]}}, 'absent_count': {'$sum': {'$cond': [{'$eq': ['$status', 'absent']}, 1, 0]}}, 'late_count': {'$sum': {'$cond': [{'$eq': ['$status', 'late']}, 1, 0]}}}},
                {'$sort': {'_id': 1}}
            ])
            agg = list(mongo.db.attendance_records.aggregate(pipeline))
            summary_data = []
            for rec in agg:
                total = rec.get('total_records', 0)
                present = rec.get('present_count', 0)
                attendance_rate = (present / total * 100) if total else 0
                summary_data.append({'date': rec.get('_id'), 'total_records': total, 'present_count': present, 'absent_count': rec.get('absent_count', 0), 'late_count': rec.get('late_count', 0), 'attendance_rate': round(attendance_rate, 2)})
            return True, summary_data
        except Exception as e:
            logging.error(f"Error generating attendance summary: {e}")
            return False, str(e)

    def sync_all_data(self):
        try:
            ok, data = self.export_attendance_data()
            if not ok:
                return False, data
            ok, msg = self.push_to_powerbi(data)
            if not ok:
                return False, msg
            ok, summary = self.generate_attendance_summary()
            return True, 'All synced'
        except Exception as e:
            logging.error(f"Error syncing all data: {e}")
            return False, str(e)
