from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_eval_report_section = Table('client_eval_report_section', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('report_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('section_order_id', INTEGER),
    Column('name', VARCHAR(length=50)),
    Column('section_title', VARCHAR(length=50)),
    Column('text', TEXT),
    Column('before_assessment', SMALLINT),
)

client_eval_report_section = Table('client_eval_report_section', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('report_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('section_template_id', INTEGER),
    Column('section_title', VARCHAR(length=50)),
    Column('text', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_eval_report_section'].columns['before_assessment'].drop()
    pre_meta.tables['client_eval_report_section'].columns['name'].drop()
    pre_meta.tables['client_eval_report_section'].columns['section_order_id'].drop()
    post_meta.tables['client_eval_report_section'].columns['section_template_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_eval_report_section'].columns['before_assessment'].create()
    pre_meta.tables['client_eval_report_section'].columns['name'].create()
    pre_meta.tables['client_eval_report_section'].columns['section_order_id'].create()
    post_meta.tables['client_eval_report_section'].columns['section_template_id'].drop()
