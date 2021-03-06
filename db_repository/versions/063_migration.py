from sqlalchemy import *
from migrate import *


from migrate.changeset import schema
pre_meta = MetaData()
post_meta = MetaData()
report_section = Table('report_section', post_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('eval_report_id', INTEGER),
    Column('eval_subtest_id', INTEGER),
    Column('name', VARCHAR(length=50)),
    Column('section_title', VARCHAR(length=50)),
    Column('text', TEXT),
)

client_background = Table('client_background', pre_meta,
    Column('id', INTEGER, primary_key=True, nullable=False),
    Column('client_id', INTEGER),
    Column('newborn_hearing_test', VARCHAR(length=255)),
    Column('birth_weight', VARCHAR(length=255)),
    Column('milk_amount', VARCHAR(length=255)),
    Column('history_of_delays_detail', VARCHAR(length=255)),
    Column('medications_detail', VARCHAR(length=255)),
    Column('pregnancy_complications', VARCHAR(length=255)),
    Column('current_length', VARCHAR(length=255)),
    Column('sleep_thru_night_detail', VARCHAR(length=255)),
    Column('hospitalizations', VARCHAR(length=255)),
    Column('family_schedule', VARCHAR(length=255)),
    Column('wake_time', VARCHAR(length=255)),
    Column('sit', VARCHAR(length=255)),
    Column('languages', VARCHAR(length=255)),
    Column('combine_speak', VARCHAR(length=255)),
    Column('delivery_complications_detail', VARCHAR(length=255)),
    Column('immunizations_detail', VARCHAR(length=255)),
    Column('current_weight', VARCHAR(length=255)),
    Column('dreams', VARCHAR(length=255)),
    Column('allergies', VARCHAR(length=255)),
    Column('additional_hearing_test_detail', VARCHAR(length=255)),
    Column('medical_concerns_detail', VARCHAR(length=255)),
    Column('newborn_hearing_test_detail', VARCHAR(length=255)),
    Column('gestation', VARCHAR(length=255)),
    Column('feeding_skills', VARCHAR(length=255)),
    Column('born_state', VARCHAR(length=255)),
    Column('how_interact_children', VARCHAR(length=255)),
    Column('delivery_complications', VARCHAR(length=255)),
    Column('nap_time', VARCHAR(length=255)),
    Column('daycare', VARCHAR(length=255)),
    Column('medical_concerns', VARCHAR(length=255)),
    Column('bed_time', VARCHAR(length=255)),
    Column('sleep_thru_night', VARCHAR(length=255)),
    Column('born_hospital', VARCHAR(length=255)),
    Column('current_food', VARCHAR(length=255)),
    Column('crawl', VARCHAR(length=255)),
    Column('illnesses', VARCHAR(length=255)),
    Column('history_of_delays', VARCHAR(length=255)),
    Column('goals', VARCHAR(length=255)),
    Column('drug_exposure', VARCHAR(length=255)),
    Column('birth_length', VARCHAR(length=255)),
    Column('follow_up_appt', VARCHAR(length=255)),
    Column('negative_behavior', VARCHAR(length=255)),
    Column('concerns', VARCHAR(length=255)),
    Column('ear_infections', VARCHAR(length=255)),
    Column('born_city', VARCHAR(length=255)),
    Column('walk', VARCHAR(length=255)),
    Column('delivery', VARCHAR(length=255)),
    Column('specialist_detail', VARCHAR(length=255)),
    Column('feeding_concerns', VARCHAR(length=255)),
    Column('how_interact_adults', VARCHAR(length=255)),
    Column('allergies_detail', VARCHAR(length=255)),
    Column('interaction_ops', VARCHAR(length=255)),
    Column('medications', VARCHAR(length=255)),
    Column('hospitalizations_detail', VARCHAR(length=255)),
    Column('roll', VARCHAR(length=255)),
    Column('surgeries', VARCHAR(length=255)),
    Column('pediatrician', VARCHAR(length=255)),
    Column('milk', VARCHAR(length=255)),
    Column('pregnancy_complications_detail', VARCHAR(length=255)),
    Column('strengths', VARCHAR(length=255)),
    Column('additional_hearing_test', VARCHAR(length=255)),
    Column('surgeries_detail', VARCHAR(length=255)),
    Column('vision_test_detail', VARCHAR(length=255)),
    Column('specialist', VARCHAR(length=255)),
    Column('immunizations', VARCHAR(length=255)),
    Column('vision_test', VARCHAR(length=255)),
    Column('illnesses_detail', VARCHAR(length=255)),
    Column('first_speak', VARCHAR(length=255)),
    Column('family', VARCHAR(length=255)),
    Column('last_seen_appt', VARCHAR(length=255)),
    Column('picky_eater', VARCHAR(length=255)),
)


def upgrade(migrate_engine):
    # Upgrade operations go here. Don't create your own engine; bind
    # migrate_engine to your metadata
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['report_section'].columns['section_title'].create()
    pre_meta.tables['client_background'].columns['additional_hearing_test'].drop()


def downgrade(migrate_engine):
    # Operations to reverse the above upgrade go here.
    pre_meta.bind = migrate_engine
    post_meta.bind = migrate_engine
    post_meta.tables['report_section'].columns['section_title'].drop()
    pre_meta.tables['client_background'].columns['additional_hearing_test'].create()
