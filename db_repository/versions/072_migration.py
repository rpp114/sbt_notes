from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
client_background = Table('client_background', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('additional_hearing_test', TEXT),
    Column('additional_hearing_test_detail', TEXT),
    Column('allergies', TEXT),
    Column('allergies_detail', TEXT),
    Column('bed_time', TEXT),
    Column('birth_length', TEXT),
    Column('birth_weight', TEXT),
    Column('born_city', TEXT),
    Column('born_hospital', TEXT),
    Column('born_state', TEXT),
    Column('combine_speak', TEXT),
    Column('concerns', TEXT),
    Column('crawl', TEXT),
    Column('current_food', TEXT),
    Column('current_length', TEXT),
    Column('current_weight', TEXT),
    Column('daycare', TEXT),
    Column('delivery', TEXT),
    Column('delivery_complications', TEXT),
    Column('delivery_complications_detail', TEXT),
    Column('dreams', TEXT),
    Column('drug_exposure', TEXT),
    Column('ear_infections', TEXT),
    Column('family', TEXT),
    Column('family_schedule', TEXT),
    Column('feeding_concerns', TEXT),
    Column('feeding_concerns_detail', TEXT),
    Column('feeding_skills', TEXT),
    Column('first_speak', TEXT),
    Column('follow_up_appt', TEXT),
    Column('gestation', TEXT),
    Column('goals', TEXT),
    Column('history_of_delays', TEXT),
    Column('history_of_delays_detail', TEXT),
    Column('hospitalizations', TEXT),
    Column('hospitalizations_detail', TEXT),
    Column('how_interact_adults', TEXT),
    Column('how_interact_children', TEXT),
    Column('illnesses', TEXT),
    Column('illnesses_detail', TEXT),
    Column('immunizations', TEXT),
    Column('immunizations_detail', TEXT),
    Column('interaction_ops', TEXT),
    Column('languages', TEXT),
    Column('last_seen_appt', TEXT),
    Column('medical_concerns', TEXT),
    Column('medical_concerns_detail', TEXT),
    Column('medications', TEXT),
    Column('medications_detail', TEXT),
    Column('milk', TEXT),
    Column('milk_amount', TEXT),
    Column('nap_time', TEXT),
    Column('negative_behavior', TEXT),
    Column('newborn_hearing_test', TEXT),
    Column('newborn_hearing_test_detail', TEXT),
    Column('pediatrician', TEXT),
    Column('picky_eater', TEXT),
    Column('pregnancy_complications', TEXT),
    Column('pregnancy_complications_detail', TEXT),
    Column('roll', TEXT),
    Column('sit', TEXT),
    Column('sleep_thru_night', TEXT),
    Column('sleep_thru_night_detail', TEXT),
    Column('specialist', TEXT),
    Column('specialist_detail', TEXT),
    Column('strengths', TEXT),
    Column('surgeries', TEXT),
    Column('surgeries_detail', TEXT),
    Column('vision_test', TEXT),
    Column('vision_test_detail', TEXT),
    Column('wake_time', TEXT),
    Column('walk', TEXT),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_background'].columns['feeding_concerns_detail'].create()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['client_background'].columns['feeding_concerns_detail'].drop()
