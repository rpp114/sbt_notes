from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
report_section = Table('report_section', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_report_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('name', VARCHAR(length=50)),
    Column('text', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['report_section'].columns['eval_subtest_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['report_section'].columns['eval_subtest_id'].drop()
