from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
role = Table('role', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('name', VARCHAR(length=55)),
    Column('description', VARCHAR(length=256)),
)

roles_users = Table('roles_users', post_meta,
    Column('user_id', INTEGER),
    Column('role_id', INTEGER),
)

user = Table('user', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('nickname', VARCHAR(length=256)),
    Column('email', VARCHAR(length=256)),
    Column('password', VARCHAR(length=55)),
    Column('active', BOOLEAN),
    Column('confirmed_at', DATETIME),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['role'].create()
    post_meta.tables['roles_users'].create()
    post_meta.tables['user'].columns['active'].create()
    post_meta.tables['user'].columns['confirmed_at'].create()
    post_meta.tables['user'].columns['password'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['role'].drop()
    post_meta.tables['roles_users'].drop()
    post_meta.tables['user'].columns['active'].drop()
    post_meta.tables['user'].columns['confirmed_at'].drop()
    post_meta.tables['user'].columns['password'].drop()
