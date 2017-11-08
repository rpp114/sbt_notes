from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
user = Table('user', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('first_name', VARCHAR(length=256)),
    Column('last_name', VARCHAR(length=256)),
    Column('email', VARCHAR(length=256)),
    Column('password', VARCHAR(length=256)),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
    Column('calendar_access', SMALLINT, default=ColumnDefault(0)),
    Column('session_token', VARCHAR(length=256)),
    Column('confirmed_at', DATETIME),
    Column('first_time_login', SMALLINT, default=ColumnDefault(1)),
    Column('company_id', INTEGER),
    Column('role_id', INTEGER, default=ColumnDefault(3)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['user'].columns['session_token'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['user'].columns['session_token'].drop()
