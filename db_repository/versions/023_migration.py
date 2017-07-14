from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
user = Table('user', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('nickname', VARCHAR(length=256)),
    Column('email', VARCHAR(length=256)),
    Column('active', INTEGER()),
    Column('confirmed_at', DATETIME),
    Column('password', VARCHAR(length=55)),
    Column('calendar_credentials', TEXT),
    Column('first_name', VARCHAR(length=256)),
    Column('last_name', VARCHAR(length=256)),
    Column('status', VARCHAR(length=15)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['user'].columns['active'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['user'].columns['active'].create()
