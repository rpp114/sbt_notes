#!/home/ray/notes/notes/bin/python

import datetime as dt, sys, os
from sqlalchemy import String
from sqlalchemy.sql import func
from sqlalchemy.sql.expression import cast

# add system directory to pull in app & models

#sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from sbt_notes.app import db
from sbt_notes.app import models

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, PROJECT_ROOT)

from sbt_notes.app import create_app
app = create_app()


def create_new_year_auths():
    
    cur_date = dt.datetime.now().replace(day=1)
    
    cur_year = cur_date.strftime('%y')
    
    new_year = str(int(cur_year) + 1)
    
    auths_to_update = models.ClientAuth.query.filter(models.ClientAuth.auth_end_date >= cur_date,
                                                     models.ClientAuth.is_eval_only == 0,
                                                     models.ClientAuth.status == 'active',
                                                     func.left(cast(models.ClientAuth.auth_id, String),2) == cur_year,
                                                     ).all()
    
    for old_auth in auths_to_update:
        
        if old_auth.client.status == 'active':
            new_auth_no = int(new_year + str(old_auth.auth_id)[2:]) 
            
            new_auth = models.ClientAuth(auth_id = new_auth_no,
                                        status = 'active',
                                        auth_end_date = old_auth.auth_end_date,
                                        auth_start_date = old_auth.auth_start_date,
                                        client_id = old_auth.client_id,
                                        monthly_visits = old_auth.monthly_visits)
            
            old_auth.status =  'inactive'                
            
            db.session.add(old_auth)
            db.session.add(new_auth)
            print('Inactivated auth_no: {}. Added new auth_no: {}.'.format(old_auth.auth_id, new_auth.auth_id))
                    
    db.session.commit()



with app.app_context():
    create_new_year_auths()
