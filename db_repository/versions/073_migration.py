from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
regional_center_team = Table('regional_center_team', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('regional_center_id', INTEGER),
    Column('team_name', VARCHAR(length=55)),
    Column('first_name', VARCHAR(length=55)),
    Column('last_name', VARCHAR(length=55)),
    Column('email', VARCHAR(length=255), default=ColumnDefault('No Email')),
    Column('phone', VARCHAR(length=15), default=ColumnDefault('No Phone Number')),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
)

case_worker = Table('case_worker', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('regional_center_id', INTEGER),
    Column('regional_center_team_id', INTEGER),
    Column('first_name', VARCHAR(length=55)),
    Column('last_name', VARCHAR(length=55)),
    Column('email', VARCHAR(length=255), default=ColumnDefault('No Email')),
    Column('phone', VARCHAR(length=15), default=ColumnDefault('No Phone Number')),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['regional_center_team'].create()
    post_meta.tables['case_worker'].columns['regional_center_team_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['regional_center_team'].drop()
    post_meta.tables['case_worker'].columns['regional_center_team_id'].drop()
