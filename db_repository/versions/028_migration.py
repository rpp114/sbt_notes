from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
post = Table('post', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('body', VARCHAR(length=256)),
    Column('timestamp', DATETIME),
    Column('user_id', INTEGER()),
)

billingXML = Table('billingXML', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('regional_center_id', INTEGER),
    Column('billing_month', DATETIME),
    Column('file_link', VARCHAR(length=255)),
    Column('created_date', DATETIME),
)

billing_notes = Table('billing_notes', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('billing_xml_id', INTEGER),
    Column('client_appt_id', INTEGER),
    Column('note', Text),
    Column('created_date', DATETIME),
)

client_appt_type = Table('client_appt_type', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=20)),
    Column('service_code', INTEGER),
    Column('service_type_code', VARCHAR(length=15)),
)

client_appt = Table('client_appt', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('start_datetime', DATETIME),
    Column('end_datetime', DATETIME),
    Column('appointment_type', VARCHAR(length=15)),
    Column('appt_type_id', INTEGER),
    Column('cancelled', SMALLINT, default=ColumnDefault(0)),
    Column('billed', SMALLINT, default=ColumnDefault(0)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].drop()
    post_meta.tables['billingXML'].create()
    post_meta.tables['billing_notes'].create()
    post_meta.tables['client_appt_type'].create()
    post_meta.tables['client_appt'].columns['appt_type_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['post'].create()
    post_meta.tables['billingXML'].drop()
    post_meta.tables['billing_notes'].drop()
    post_meta.tables['client_appt_type'].drop()
    post_meta.tables['client_appt'].columns['appt_type_id'].drop()
