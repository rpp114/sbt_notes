from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_eval_report_section = Table('client_eval_report_section', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('report_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('section_order_id', INTEGER),
    Column('name', VARCHAR(length=50)),
    Column('section_title', VARCHAR(length=50)),
    Column('text', TEXT),
)

client_evaluation = Table('client_evaluation', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('client_appt_id', INTEGER),
    Column('created_date', DATETIME),
)

client_evaluation_answer = Table('client_evaluation_answer', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('question_id', INTEGER),
    Column('evaluation_id', INTEGER),
    Column('caregiver_response', SMALLINT, default=ColumnDefault(0)),
    Column('score', INTEGER),
)

client_evaluation_report = Table('client_evaluation_report', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('evaluation_id', INTEGER),
    Column('filename', VARCHAR(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_eval_report_section'].create()
    post_meta.tables['client_evaluation'].create()
    post_meta.tables['client_evaluation_answer'].create()
    post_meta.tables['client_evaluation_report'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_eval_report_section'].drop()
    post_meta.tables['client_evaluation'].drop()
    post_meta.tables['client_evaluation_answer'].drop()
    post_meta.tables['client_evaluation_report'].drop()
