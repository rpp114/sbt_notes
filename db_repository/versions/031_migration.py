from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_appt_type = Table('client_appt_type', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('name', VARCHAR(length=20)),
    Column('service_code', INTEGER()),
    Column('service_type_code', VARCHAR(length=15)),
)

appt_type = Table('appt_type', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=20)),
    Column('service_code', INTEGER),
    Column('service_type_code', VARCHAR(length=15)),
    Column('regional_center_id', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_appt_type'].drop()
    post_meta.tables['appt_type'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_appt_type'].create()
    post_meta.tables['appt_type'].drop()
