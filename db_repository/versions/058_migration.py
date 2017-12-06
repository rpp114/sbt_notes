from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
company_meeting = Table('company_meeting', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('company_id', INTEGER),
    Column('start_datetime', DATETIME),
    Column('end_datetime', DATETIME),
    Column('description', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company_meeting'].columns['company_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company_meeting'].columns['company_id'].drop()