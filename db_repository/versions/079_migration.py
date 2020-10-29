from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
evaluation_report_template_section = Table('evaluation_report_template_section', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('section_rank', INTEGER),
    Column('title', VARCHAR(length=255)),
    Column('text', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['evaluation_report_template_section'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['evaluation_report_template_section'].drop()
