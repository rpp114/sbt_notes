from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_evals = Table('client_evals', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type', VARCHAR(length=55)),
    Column('therapist_id', INTEGER),
    Column('created_date', DATETIME),
)

client_evals = Table('client_evals', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('eval_type_id', INTEGER),
    Column('therapist_id', INTEGER),
)

client = Table('client', pre_meta,
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

client = Table('client', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('first_name', VARCHAR(length=255)),
    Column('last_name', VARCHAR(length=255)),
    Column('birthdate', DATETIME),
    Column('uci_id', INTEGER),
    Column('address', VARCHAR(length=255)),
    Column('city', VARCHAR(length=55)),
    Column('state', VARCHAR(length=10)),
    Column('zipcode', VARCHAR(length=15)),
    Column('phone', VARCHAR(length=15)),
    Column('regional_center_id', INTEGER),
    Column('therapist_id', INTEGER),
    Column('status', VARCHAR(length=15), default=ColumnDefault('active')),
)

evaluations = Table('evaluations', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('created_date', DATETIME),
    Column('name', VARCHAR(length=55)),
    Column('test_seq', VARCHAR(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_evals'].columns['created_date'].drop()
    pre_meta.tables['client_evals'].columns['eval_type'].drop()
    post_meta.tables['client_evals'].columns['eval_type_id'].create()
    pre_meta.tables['client'].columns['created_date'].drop()
    post_meta.tables['client'].columns['address'].create()
    post_meta.tables['client'].columns['city'].create()
    post_meta.tables['client'].columns['phone'].create()
    post_meta.tables['client'].columns['state'].create()
    post_meta.tables['client'].columns['zipcode'].create()
    pre_meta.tables['evaluations'].columns['created_date'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['client_evals'].columns['created_date'].create()
    pre_meta.tables['client_evals'].columns['eval_type'].create()
    post_meta.tables['client_evals'].columns['eval_type_id'].drop()
    pre_meta.tables['client'].columns['created_date'].create()
    post_meta.tables['client'].columns['address'].drop()
    post_meta.tables['client'].columns['city'].drop()
    post_meta.tables['client'].columns['phone'].drop()
    post_meta.tables['client'].columns['state'].drop()
    post_meta.tables['client'].columns['zipcode'].drop()
    pre_meta.tables['evaluations'].columns['created_date'].create()
