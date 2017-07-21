from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_auth = Table('client_auth', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('client_id', INTEGER()),
    Column('auth_id', INTEGER()),
    Column('monthly_visits', INTEGER()),
    Column('auth_end_date', DATETIME),
    Column('auth_start_date', DATETIME),
    Column('created_date', DATETIME),
    Column('therapist_id', INTEGER()),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_auth'].columns['therapist_id'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_auth'].columns['therapist_id'].create()
