from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
company_meeting = Table('company_meeting', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('start_datetime', DATETIME),
    Column('end_datetime', DATETIME),
    Column('description', TEXT),
)

meeting_user_lookup = Table('meeting_user_lookup', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('meeting_id', INTEGER),
    Column('user_id', INTEGER),
    Column('attended', SMALLINT, default=ColumnDefault(1)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company_meeting'].create()
    post_meta.tables['meeting_user_lookup'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company_meeting'].drop()
    post_meta.tables['meeting_user_lookup'].drop()
