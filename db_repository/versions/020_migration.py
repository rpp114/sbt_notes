from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
company = Table('company', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('city', VARCHAR(length=55)),
    Column('state', VARCHAR(length=10), default=ColumnDefault('CA')),
    Column('zipcode', VARCHAR(length=15)),
)

note = Table('note', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('appt_id', INTEGER),
    Column('client_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('note', Text),
    Column('created_date', DATETIME),
)

client_eval = Table('client_eval', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('client_id', INTEGER()),
    Column('eval_type_id', INTEGER()),
    Column('therapist_id', INTEGER()),
    Column('created_date', TIMESTAMP, nullable=False),
)

client_auth = Table('client_auth', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('client_id', INTEGER()),
    Column('auth_start', DATETIME),
    Column('auth_end', DATETIME),
    Column('auth_id', INTEGER()),
    Column('monthly_visits', INTEGER()),
)

client_auth = Table('client_auth', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('auth_start_date', DATETIME),
    Column('auth_end_date', DATETIME),
    Column('auth_id', INTEGER),
    Column('monthly_visits', INTEGER),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company'].create()
    post_meta.tables['note'].create()
    pre_meta.tables['client_eval'].columns['eval_type_id'].drop()
    pre_meta.tables['client_auth'].columns['auth_end'].drop()
    pre_meta.tables['client_auth'].columns['auth_start'].drop()
    post_meta.tables['client_auth'].columns['auth_end_date'].create()
    post_meta.tables['client_auth'].columns['auth_start_date'].create()
    post_meta.tables['client_auth'].columns['created_date'].create()
    post_meta.tables['client_auth'].columns['therapist_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company'].drop()
    post_meta.tables['note'].drop()
    pre_meta.tables['client_eval'].columns['eval_type_id'].create()
    pre_meta.tables['client_auth'].columns['auth_end'].create()
    pre_meta.tables['client_auth'].columns['auth_start'].create()
    post_meta.tables['client_auth'].columns['auth_end_date'].drop()
    post_meta.tables['client_auth'].columns['auth_start_date'].drop()
    post_meta.tables['client_auth'].columns['created_date'].drop()
    post_meta.tables['client_auth'].columns['therapist_id'].drop()
