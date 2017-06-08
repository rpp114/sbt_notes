from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval_subtests = Table('eval_subtests', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_id', INTEGER),
    Column('page_no', INTEGER),
    Column('name', VARCHAR(length=50)),
)

eval_questions = Table('eval_questions', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_type_id', INTEGER),
    Column('subtest_id', INTEGER),
    Column('evaluation', VARCHAR(length=256)),
    Column('subtest', VARCHAR(length=256)),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER),
    Column('question', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval_subtests'].create()
    post_meta.tables['eval_questions'].columns['subtest_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval_subtests'].drop()
    post_meta.tables['eval_questions'].columns['subtest_id'].drop()
