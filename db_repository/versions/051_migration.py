from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval_subtest_scaled_score = Table('eval_subtest_scaled_score', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('from_age', INTEGER),
    Column('to_age', INTEGER),
    Column('subtest_id', INTEGER),
    Column('raw_score', INTEGER),
    Column('scaled_score', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval_subtest_scaled_score'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval_subtest_scaled_score'].drop()
