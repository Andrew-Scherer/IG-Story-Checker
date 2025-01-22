from models import db
from models.batch_log import BatchLog
from sqlalchemy.orm import scoped_session
from flask import current_app

class BatchLogService:
    @staticmethod
    def create_log(batch_id, event_type, message, profile_id=None, proxy_id=None):
        with current_app.app_context():
            session = scoped_session(db.session)
            try:
                log = BatchLog(
                    batch_id=batch_id,
                    event_type=event_type,
                    message=message,
                    profile_id=profile_id,
                    proxy_id=proxy_id
                )
                session.add(log)
                session.commit()
                return log
            except Exception as e:
                session.rollback()
                raise e
            finally:
                session.remove()

    @staticmethod
    def get_logs(batch_id, start_time=None, end_time=None, limit=100, offset=0):
        with current_app.app_context():
            session = scoped_session(db.session)
            try:
                query = session.query(BatchLog).filter(BatchLog.batch_id == batch_id)
                
                if start_time:
                    query = query.filter(BatchLog.timestamp >= start_time)
                if end_time:
                    query = query.filter(BatchLog.timestamp <= end_time)
                
                query = query.order_by(BatchLog.timestamp.desc())
                
                total = query.count()
                logs = query.limit(limit).offset(offset).all()
                
                return logs, total
            finally:
                session.remove()
