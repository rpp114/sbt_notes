from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
report_section_template = Table('report_section_template', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('subtest_id', INTEGER()),
    Column('section_detail', TEXT),
    Column('section_summary', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['report_section_template'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['report_section_template'].create()
