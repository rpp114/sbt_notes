from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
company = Table('company', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('address', VARCHAR(length=255)),
    Column('city', VARCHAR(length=55)),
    Column('state', VARCHAR(length=10), default=ColumnDefault('CA')),
    Column('zipcode', VARCHAR(length=15)),
    Column('vendor_id', VARCHAR(length=55)),
    Column('doc_password', VARCHAR(length=55)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company'].columns['doc_password'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['company'].columns['doc_password'].drop()
