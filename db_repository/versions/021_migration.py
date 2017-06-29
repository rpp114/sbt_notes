from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
note = Table('note', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('appt_id', INTEGER()),
    Column('client_id', INTEGER()),
    Column('therapist_id', INTEGER()),
    Column('note', TEXT),
    Column('created_date', DATETIME),
)

client_appt = Table('client_appt', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('start_datetime', DATETIME),
    Column('end_datetime', DATETIME),
)

client_appt_note = Table('client_appt_note', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_appt_id', INTEGER),
    Column('note', Text),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['note'].drop()
    post_meta.tables['client_appt'].create()
    post_meta.tables['client_appt_note'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['note'].create()
    post_meta.tables['client_appt'].drop()
    post_meta.tables['client_appt_note'].drop()
