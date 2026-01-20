import sys, os
from sqlalchemy import text
from datetime import datetime
from zoneinfo import ZoneInfo

# add system directory to pull in app & models


from sbt_notes.app import db
from sbt_notes.app import  models

def need_new_appts():
    '''
        Resets Clients that are only approved for one appt per month.
        Puts them into the to do list for scheduling.
    '''

    pdt = ZoneInfo('America/Los_Angeles')

    today = datetime.now(pdt))

    auths_need_appts = models.ClientAuth.query.filter(models.ClientAuth.status == 'active',
                                                      models.ClientAuth.monthly_visits <= 2,
                                                      models.ClientAuth.is_eval_only == 0,
                                                      models.ClientAuth.auth_start_date <= today,
                                                      models.ClientAuth.auth_end_date >= today,
                                                      models.ClientAuth.client.has(status = 'active')).all()

    for auth in auths_need_appts:
        client = auth.client
        client.needs_appt_scheduled = 1
        db.session.add(client)

    db.session.commit()

#    print('need appts for {} clients'.format(len(auths_need_appts)))

def archive_eval_clients():
    '''
        Archives clients with only authorization for evals.
        Archives after evaluation report is completed.
    '''

    clients_query = text('''
        SELECT DISTINCT
        eval_only_clients.client_id
        FROM
            (
                SELECT
                    client_id
                FROM
                    client_auth ca
                INNER JOIN
                    client c
                ON
                    c.id = ca.client_id
                AND c.status = 'active'
                WHERE
                    client_id NOT IN
                    (
                        SELECT
                            client_id
                        FROM
                            client_auth
                        WHERE
                            is_eval_only = 0)
                AND is_eval_only = 1) AS eval_only_clients
            INNER JOIN
            (
                select appt.client_id

                from client_appt appt
                inner join appt_type at on at.id = appt.appt_type_id
                    and at.name = 'evaluation'
                    and appt.cancelled = 0
                left join client_eval ce on ce.client_appt_id = appt.id
                left join eval_report er on er.client_eval_id = ce.id

                where er.id is not null) reports
            ON
                reports.client_id = eval_only_clients.client_id
    ''')

    client_ids = db.session.execute(clients_query)

    for client_id in client_ids:
        client = models.Client.query.get(client_id)
        client.status = 'inactive'

    db.session.commit()
