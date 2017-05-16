from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_evals = Table('client_evals', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type', VARCHAR(length=55)),
    Column('therapist_id', INTEGER),
    Column('created_date', DATETIME),
)

evaluations = Table('evaluations', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type', VARCHAR(length=55)),
    Column('therapist_id', INTEGER),
    Column('created_date', DATETIME),
)

evaluations = Table('evaluations', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('test_seq', VARCHAR(length=255)),
    Column('created_date', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_evals'].create()
    pre_meta.tables['evaluations'].columns['client_id'].drop()
    pre_meta.tables['evaluations'].columns['eval_type'].drop()
    pre_meta.tables['evaluations'].columns['therapist_id'].drop()
    post_meta.tables['evaluations'].columns['name'].create()
    post_meta.tables['evaluations'].columns['test_seq'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_evals'].drop()
    pre_meta.tables['evaluations'].columns['client_id'].create()
    pre_meta.tables['evaluations'].columns['eval_type'].create()
    pre_meta.tables['evaluations'].columns['therapist_id'].create()
    post_meta.tables['evaluations'].columns['name'].drop()
    post_meta.tables['evaluations'].columns['test_seq'].drop()
