import hashlib
from sqlalchemy import select
from datetime import datetime

# add system directory to pull in app & models

from sbt_notes.app import db, models
from flask_login import current_user

def get_last_hash():
    last_hash_query = select(models.UserActivityLog.current_hash).order_by(models.UserActivityLog.created_at.desc()).limit(1)
    
    last_hash = db.session.execute(last_hash_query).scalar_one_or_none()
    
    return '0' * 64 if last_hash == None else last_hash


def write_activity_log(action, resource_type, resource_id, request):

    previous_hash = get_last_hash()

    timestamp = datetime.utcnow().isoformat()

    data = f"{current_user.id}{action}{resource_type}{resource_id}{request.remote_addr}{request.headers.get("User-Agent")}{timestamp}{previous_hash}"

    current_hash = hashlib.sha256(data.encode()).hexdigest()

    activity_log_record = models.UserActivityLog(user_id=current_user.id,
                                 action=action,
                                 resource_type=resource_type,
                                 resource_id=resource_id,
                                 ip_address=request.remote_addr,
                                 user_agent=request.headers.get("User-Agent"),
                                 created_at=timestamp,
                                 previous_hash=previous_hash,
                                 current_hash=current_hash)

    db.session.add(activity_log_record)
    db.session.commit()

