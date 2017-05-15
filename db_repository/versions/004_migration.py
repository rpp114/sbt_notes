from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client = Table('client', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('first_name', VARCHAR(length=255)),
    Column('last_name', VARCHAR(length=255)),
    Column('birthdate', DATETIME),
    Column('uci_id', INTEGER),
    Column('regional_center_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('status', VARCHAR(length=15)),
    Column('created_date', DATETIME),
)

client_auths = Table('client_auths', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('auth_start', DATETIME),
    Column('auth_end', DATETIME),
    Column('auth_id', INTEGER),
    Column('monthly_visits', INTEGER),
)

eval_questions = Table('eval_questions', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('evaluation', VARCHAR(length=256)),
    Column('subtest', VARCHAR(length=256)),
    Column('question_cat', VARCHAR(length=256)),
    Column('question_num', INTEGER),
    Column('question', VARCHAR(length=256)),
)

evaluations = Table('evaluations', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type', VARCHAR(length=55)),
    Column('therapist_id', INTEGER),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client'].create()
    post_meta.tables['client_auths'].create()
    post_meta.tables['eval_questions'].create()
    post_meta.tables['evaluations'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client'].drop()
    post_meta.tables['client_auths'].drop()
    post_meta.tables['eval_questions'].drop()
    post_meta.tables['evaluations'].drop()
