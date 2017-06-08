from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_auths = Table('client_auths', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('client_id', INTEGER()),
    Column('auth_start', DATETIME),
    Column('auth_end', DATETIME),
    Column('auth_id', INTEGER()),
    Column('monthly_visits', INTEGER()),
)

client_eval_answers = Table('client_eval_answers', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('client_eval_id', INTEGER()),
    Column('eval_questions_id', INTEGER()),
    Column('answer', SMALLINT()),
)

client_evals = Table('client_evals', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('client_id', INTEGER()),
    Column('therapist_id', INTEGER()),
    Column('eval_type_id', INTEGER()),
    Column('created_date', TIMESTAMP, nullable=False),
)

eval_question_tmp = Table('eval_question_tmp', pre_meta,
    Column('id', INTEGER(), nullable=False),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER()),
    Column('question', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
    Column('subtest_id', INTEGER()),
)

eval_questions = Table('eval_questions', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER()),
    Column('question', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
    Column('subtest_id', INTEGER()),
)

eval_subtests = Table('eval_subtests', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('eval_id', INTEGER()),
    Column('name', VARCHAR(length=50)),
    Column('eval_subtest_id', INTEGER()),
)

evaluations = Table('evaluations', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('test_seq', VARCHAR(length=255)),
)

client_auth = Table('client_auth', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('auth_start', DATETIME),
    Column('auth_end', DATETIME),
    Column('auth_id', INTEGER),
    Column('monthly_visits', INTEGER),
)

client_eval = Table('client_eval', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('created_date', DATETIME),
)

client_eval_answer = Table('client_eval_answer', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_eval_id', INTEGER),
    Column('eval_question_id', INTEGER),
    Column('answer', SMALLINT),
)

eval_question = Table('eval_question', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('subtest_id', INTEGER),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER),
    Column('question', VARCHAR(length=256)),
    Column('report_text', VARCHAR(length=256)),
)

eval_subtest = Table('eval_subtest', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('name', VARCHAR(length=50)),
)

evaluation = Table('evaluation', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('test_seq', VARCHAR(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_auths'].drop()
    pre_meta.tables['client_eval_answers'].drop()
    pre_meta.tables['client_evals'].drop()
    pre_meta.tables['eval_question_tmp'].drop()
    pre_meta.tables['eval_questions'].drop()
    pre_meta.tables['eval_subtests'].drop()
    pre_meta.tables['evaluations'].drop()
    post_meta.tables['client_auth'].create()
    post_meta.tables['client_eval'].create()
    post_meta.tables['client_eval_answer'].create()
    post_meta.tables['eval_question'].create()
    post_meta.tables['eval_subtest'].create()
    post_meta.tables['evaluation'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_auths'].create()
    pre_meta.tables['client_eval_answers'].create()
    pre_meta.tables['client_evals'].create()
    pre_meta.tables['eval_question_tmp'].create()
    pre_meta.tables['eval_questions'].create()
    pre_meta.tables['eval_subtests'].create()
    pre_meta.tables['evaluations'].create()
    post_meta.tables['client_auth'].drop()
    post_meta.tables['client_eval'].drop()
    post_meta.tables['client_eval_answer'].drop()
    post_meta.tables['eval_question'].drop()
    post_meta.tables['eval_subtest'].drop()
    post_meta.tables['evaluation'].drop()
