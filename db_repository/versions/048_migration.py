from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval_subtest_start = Table('eval_subtest_start', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('age', INTEGER),
    Column('subtest_id', INTEGER),
    Column('start_point', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval_subtest_start'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval_subtest_start'].drop()
