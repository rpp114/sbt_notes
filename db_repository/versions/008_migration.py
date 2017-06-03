from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_eval_answers = Table('client_eval_answers', post_meta,
    Column('client_eval_id', INTEGER),
    Column('eval_questions_id', INTEGER),
    Column('answer', SMALLINT),
)

eval_questions = Table('eval_questions', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_type_id', INTEGER),
    Column('evaluation', VARCHAR(length=256)),
    Column('subtest', VARCHAR(length=256)),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER),
    Column('question', VARCHAR(length=256)),
)

client_evals = Table('client_evals', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_eval_answers'].create()
    post_meta.tables['eval_questions'].columns['eval_type_id'].create()
    post_meta.tables['client_evals'].columns['created_date'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_eval_answers'].drop()
    post_meta.tables['eval_questions'].columns['eval_type_id'].drop()
    post_meta.tables['client_evals'].columns['created_date'].drop()
