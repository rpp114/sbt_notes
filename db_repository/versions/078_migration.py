from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
evaluation_question = Table('evaluation_question', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('subtest_id', INTEGER),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER),
    Column('question', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
    Column('caregiver_response', SMALLINT, default=ColumnDefault(0)),
)

evaluation_question_response = Table('evaluation_question_response', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('question_id', INTEGER),
    Column('score', INTEGER),
    Column('response', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
)

evaluation_subtest = Table('evaluation_subtest', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_type_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('name', VARCHAR(length=50)),
    Column('description', TEXT),
)

evaluation_type = Table('evaluation_type', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('test_formal_name', VARCHAR(length=255)),
    Column('description', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['evaluation_question'].create()
    post_meta.tables['evaluation_question_response'].create()
    post_meta.tables['evaluation_subtest'].create()
    post_meta.tables['evaluation_type'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['evaluation_question'].drop()
    post_meta.tables['evaluation_question_response'].drop()
    post_meta.tables['evaluation_subtest'].drop()
    post_meta.tables['evaluation_type'].drop()
