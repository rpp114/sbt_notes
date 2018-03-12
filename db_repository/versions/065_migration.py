from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
evaluation = Table('evaluation', pre_meta,
    Column('id', INTEGER(), primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('test_seq', VARCHAR(length=255)),
)

evaluation = Table('evaluation', post_meta,
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
    pre_meta.tables['evaluation'].columns['test_seq'].drop()
    post_meta.tables['evaluation'].columns['description'].create()
    post_meta.tables['evaluation'].columns['test_formal_name'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    pre_meta.tables['evaluation'].columns['test_seq'].create()
    post_meta.tables['evaluation'].columns['description'].drop()
    post_meta.tables['evaluation'].columns['test_formal_name'].drop()
