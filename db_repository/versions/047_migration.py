from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_appt_note = Table('client_appt_note', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_appt_id', INTEGER),
    Column('user_id', INTEGER),
    Column('approved', SMALLINT, default=ColumnDefault(0)),
    Column('note', Text),
    Column('intern_id', INTEGER),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_appt_note'].columns['intern_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_appt_note'].columns['intern_id'].drop()
