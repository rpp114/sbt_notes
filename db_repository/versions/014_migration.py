from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval_subtests = Table('eval_subtests', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('eval_id', INTEGER()),
    Column('page_no', INTEGER()),
    Column('name', VARCHAR(length=50)),
    Column('eval_subtest_id', INTEGER()),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eval_subtests'].columns['page_no'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eval_subtests'].columns['page_no'].create()
