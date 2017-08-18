from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
therapist = Table('therapist', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('user_id', INTEGER),
    Column('company_id', INTEGER),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
    Column('calendar_credentials', Text),
)

user = Table('user', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('email', VARCHAR(length=256)),
    Column('confirmed_at', DATETIME),
    Column('calendar_credentials', TEXT),
    Column('first_name', VARCHAR(length=256)),
    Column('last_name', VARCHAR(length=256)),
    Column('status', VARCHAR(length=15)),
    Column('calendar_access', SMALLINT()),
    Column('password', VARCHAR(length=256)),
    Column('company_id', INTEGER()),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['therapist'].columns['calendar_credentials'].create()
    pre_meta.tables['user'].columns['calendar_credentials'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['therapist'].columns['calendar_credentials'].drop()
    pre_meta.tables['user'].columns['calendar_credentials'].create()
