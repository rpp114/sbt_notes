from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval_subtest_lookup = Table('eval_subtest_lookup', pre_meta,
    Column('client_eval_id', INTEGER(), primary_key=True, nullable=False),
    Column('subtest_id', INTEGER(), primary_key=True, nullable=False),
)

client_eval_subtest_lookup = Table('client_eval_subtest_lookup', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_eval_id', INTEGER),
    Column('subtest_id', INTEGER),
    Column('raw_score', INTEGER),
    Column('scaled_score', INTEGER),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eval_subtest_lookup'].drop()
    post_meta.tables['client_eval_subtest_lookup'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eval_subtest_lookup'].create()
    post_meta.tables['client_eval_subtest_lookup'].drop()
