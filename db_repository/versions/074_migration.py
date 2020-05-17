from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
file_upload_type = Table('file_upload_type', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('file_type', VARCHAR(length=25)),
    Column('file_type_dir', VARCHAR(length=25)),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['file_upload_type'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['file_upload_type'].drop()
