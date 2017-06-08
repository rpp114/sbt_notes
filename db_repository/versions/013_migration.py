from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval_questions = Table('eval_questions', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER()),
    Column('question', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
    Column('eval_type_id', INTEGER()),
    Column('subtest_id', INTEGER()),
    Column('evaluation', VARCHAR(length=256)),
    Column('subtest', VARCHAR(length=256)),
)

eval_subtests = Table('eval_subtests', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_id', INTEGER),
    Column('page_no', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('name', VARCHAR(length=50)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eval_questions'].columns['eval_type_id'].drop()
    pre_meta.tables['eval_questions'].columns['evaluation'].drop()
    pre_meta.tables['eval_questions'].columns['subtest'].drop()
    post_meta.tables['eval_subtests'].columns['eval_subtest_id'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['eval_questions'].columns['eval_type_id'].create()
    pre_meta.tables['eval_questions'].columns['evaluation'].create()
    pre_meta.tables['eval_questions'].columns['subtest'].create()
    post_meta.tables['eval_subtests'].columns['eval_subtest_id'].drop()
