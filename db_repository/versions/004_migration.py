from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
eval__questions = Table('eval__questions', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('evaluation', VARCHAR(length=256)),
    Column('subtest', VARCHAR(length=256)),
    Column('question_num', INTEGER),
    Column('question', VARCHAR(length=256)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval__questions'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['eval__questions'].drop()
