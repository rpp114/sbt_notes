from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client = Table('client', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('first_name', VARCHAR(length=255)),
    Column('last_name', VARCHAR(length=255)),
    Column('birthdate', DATETIME),
    Column('uci_id', INTEGER),
    Column('address', VARCHAR(length=255)),
    Column('city', VARCHAR(length=55)),
    Column('state', VARCHAR(length=10)),
    Column('zipcode', VARCHAR(length=15)),
    Column('phone', VARCHAR(length=15)),
    Column('gender', VARCHAR(length=10)),
    Column('needs_appt_scheduled', SMALLINT, default=ColumnDefault(1)),
    Column('additional_info', Text),
    Column('regional_center_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
    Column('weeks_premature', Numeric(precision=10, scale=2), default=ColumnDefault(0)),
)

client_eval = Table('client_eval', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('client_appt_id', INTEGER),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client'].columns['weeks_premature'].create()
    post_meta.tables['client_eval'].columns['client_appt_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client'].columns['weeks_premature'].drop()
    post_meta.tables['client_eval'].columns['client_appt_id'].drop()
