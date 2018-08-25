from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
billingXML = Table('billingXML', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('regional_center_id', INTEGER()),
    Column('billing_month', DATETIME),
    Column('file_link', VARCHAR(length=255)),
    Column('created_date', TIMESTAMP, nullable=False),
)

billing_xml = Table('billing_xml', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('regional_center_id', INTEGER),
    Column('billing_month', DATETIME),
    Column('file_link', VARCHAR(length=255)),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['billingXML'].drop()
    post_meta.tables['billing_xml'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['billingXML'].create()
    post_meta.tables['billing_xml'].drop()
