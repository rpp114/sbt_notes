from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
regional_center = Table('regional_center', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('rc_id', INTEGER),
    Column('name', VARCHAR(length=55)),
    Column('address', VARCHAR(length=255)),
    Column('city', VARCHAR(length=55)),
    Column('state', VARCHAR(length=10), default=ColumnDefault('CA')),
    Column('zipcode', VARCHAR(length=15)),
    Column('primary_contact_name', VARCHAR(length=55)),
    Column('primary_contact_phone', VARCHAR(length=55)),
    Column('primary_contact_email', VARCHAR(length=55)),
)

company = Table('company', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('city', VARCHAR(length=55)),
    Column('state', VARCHAR(length=10), default=ColumnDefault('CA')),
    Column('zipcode', VARCHAR(length=15)),
    Column('vendor_id', VARCHAR(length=55)),
)

user = Table('user', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('first_name', VARCHAR(length=256)),
    Column('last_name', VARCHAR(length=256)),
    Column('email', VARCHAR(length=256)),
    Column('password', VARCHAR(length=256)),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
    Column('calendar_access', SMALLINT, default=ColumnDefault(0)),
    Column('confirmed_at', DATETIME),
    Column('calendar_credentials', Text),
    Column('company_id', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['regional_center'].columns['primary_contact_email'].create()
    post_meta.tables['regional_center'].columns['rc_id'].create()
    post_meta.tables['company'].columns['vendor_id'].create()
    post_meta.tables['user'].columns['company_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['regional_center'].columns['primary_contact_email'].drop()
    post_meta.tables['regional_center'].columns['rc_id'].drop()
    post_meta.tables['company'].columns['vendor_id'].drop()
    post_meta.tables['user'].columns['company_id'].drop()
