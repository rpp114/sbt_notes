import sys, os, datetime, calendar

from sqlalchemy import and_, func, between

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def score_eval(client_eval_id):

    eval = models.ClientEval.query.get(client_eval_id)

    answers = eval.answers.filter(models.ClientEvalAnswer.answer == 1).all()

    answers_by_subtest = {}

    for answer in answers:
        answers_by_subtest[answer.question.subtest.id] = answers_by_subtest.get(answer.question.subtest.id, [])
        answers_by_subtest[answer.question.subtest.id].append(answer.question.question_num)

    eval_scores = {}

    client_age = (eval.created_date - eval.client.birthdate).days

    for subtest in answers_by_subtest:
        raw_score = min(answers_by_subtest[subtest]) + len(answers_by_subtest[subtest])-1

        scaled_score = db.session.query(func.max(models.EvalSubtestScaledScore.scaled_score)).filter(models.EvalSubtestScaledScore.subtest_id == subtest,
                            models.EvalSubtestScaledScore.raw_score <= raw_score,
                            between(client_age, models.EvalSubtestScaledScore.from_age, models.EvalSubtestScaledScore.to_age)).first()[0]

        age_equivalent = db.session.query(func.max(models.EvalSubtestAgeEquivalent.age_equivalent))\
                            .filter(models.EvalSubtestAgeEquivalent.subtest_id == subtest,
                                    models.EvalSubtestAgeEquivalent.raw_score <= raw_score).first()[0]

        eval_subtest = models.ClientEvalSubtestLookup.query.filter_by(client_eval_id =  eval.id, subtest_id = subtest).first()

        eval_subtest.raw_score = raw_score
        eval_subtest.scaled_score = scaled_score
        eval_subtest.age_equivalent = age_equivalent

        db.session.add(eval_subtest)

    db.session.commit()

def get_client_age(birth_date, eval_date):
	birth_day = birth_date.day
	eval_day = eval_date.day

	birth_month = birth_date.month
	eval_month = eval_date.month

	birth_year = birth_date.year
	eval_year = eval_date.year

	if birth_day > eval_day:
		eval_month -= 1
		eval_day += 30

	if birth_month > eval_month:
		eval_month += 12
		eval_year -= 1

	return str((eval_year - birth_year) * 12 + (eval_month - birth_month)) + ' Months ' + str(eval_day - birth_day) + ' Days'


def create_background(eval, form_results = None):

    form_results['first_name'] = eval.client.first_name
    form_results['pronoun'] = 'he' if eval.client.gender == 'M' else 'her'
    form_results['possessive_pronoun'] = 'his' if eval.client.gender == 'M' else 'hers'

    background_list = []

    paragraph_one = []

    birth = """%(first_name)s was born at %(hospital)s at %(gestation)s gestation via %(delivery_method)s.""" % form_results

    paragraph_one.append(birth)

    weight = """%(pronoun)s weighed %(birth_weight)s at birth.""" % form_results

    paragraph_one.append(weight.capitalize())

    delivery_birth = 'It was reported that there were no complications during pregnancy.' if form_results['delivery_complications'] == 'False' else form_results['delivery_complications_detail']

    if form_results['birth_complications'] == 'False' and form_results['delivery_complications'] == 'False':
        delivery_birth = delivery_birth[:-1] + " or during %(possessive_pronoun)s birth." % form_results
    elif form_results['birth_complications'] == 'False':
        delivery_birth += '  ' + 'It was reported there were no complications during birth.'
    else:
        delivery_birth += '  ' + form_results['birth_complications_detail']

    paragraph_one.append(delivery_birth)

    hearing_vision = "It was reported that %(pronoun)s passed %(possessive_pronoun)s newborn hearing screen." % form_results if form_results['hearing_test'] == 'True' else form_results['hearing_test_detail']

    if form_results['vision_test'] == 'True' and form_results['hearing_test'] == 'True':
        hearing_vision = hearing_vision[:-7] + "and vision screen."
    elif form_results['vision_test'] == 'True':
        hearing_vision += '  ' + "It was reported that %(pronoun)s passed %(possessive_pronoun)s newborn hearing screen." % form_results
    else:
        hearing_vision += '  ' + form_results['vision_test_detail']

    paragraph_one.append(hearing_vision)

    hospitalizations = "%(pronoun)s has had no significant hospitalizations since %(possessive_pronoun)s birth." % form_results if form_results['hospitalizations'] == 'False' else form_results['hospitalizations_detail']

    paragraph_one.append(hospitalizations)

    background_list.append(paragraph_one)

    background =  '\n'.join(background_list)

    print(background)

    # %(hearing_test)s. %(vision_test)s. %(hospitalizations)s. It was reported that %(pronoun)s passed %(possessive_pronoun)s newborn hearing and vision screen and has had no significant hospitalizations since %(possessive_pronoun)s birth.
    #
    # %(possessive_pronoun)s current weight was reported to be %(current_weight)s and measures %(current_length)s in length.  %(immunizations)s It was reported that %(pronoun)s is up to date on all %(possessive_pronoun)s immunizations.  %(care_giver)s reported that %(pronoun)s currently takes %(medications)s no medications and %(allergies)s has no known allergies. It was reported that %(pronoun)s is being followed by %(possessive_pronoun)s pediatrician %(doctor_name)s.
    #
    # %(care_giver)s reported that %(first_name)s goes to bed at %(bed_time)s and wakes up at %(wake_time)s, %(sleep_thru_night)s sleeping through the night.  %(care_giver_pronoun)s noted that %(pronoun)s naps between %(nap_times)s. %(care_giver)s reported that %(first_name)s is %(picky_eater)s a picky eater with %(eating_details)s.  %(care_giver_pronoun)s reported that %(pronoun)s is eating solids and drinking %(milk)s.  %(care_giver_pronoun)s reported that %(pronoun)s loves french fries, chicken nuggets, tomatoes, avocados, grapes, watermelon and strawberries. It was reported that %(pronoun)s does not like veggies.  %(care_giver) reported that %(pronoun)s can finger feed, use a spoon and a fork, as well as drink from a sippy cup and from a straw.  %(care_giver) reported that %(pronoun)s will not sit down to eat and instead will walk around during mealtime.
    #
    # Care giver reported that %(first_name)s has limited opportunities to interact with other kids and tends to be shy with %(possessive_pronoun)s peers and adults.  She mentioned that %(pronoun)s will engage in some negative behaviors including biting, hitting, and screaming. Care giver reported that %(pronoun)s is able to say “Ma”, “Ba”, “Boo”, “Ga” (only twice) and “Mom”. She mentioned that most of %(possessive_pronoun)s language is random and spontaneous, but %(pronoun)s mostly will grunt to communicate %(possessive_pronoun)s wants and needs.  In addition, it was reported that %(first_name)s loves Paw Patrol, cars and legos, as well as cats.
    #
    # It was reported that %(first_name)s met %(possessive_pronoun)s developmental milestones as followed: rolled at 3 months, sat unsupported at 4-5 months, crawled at 8 months, walked at 10 months and spoke first word at 16 months."""



eval = models.ClientEval.query.get(12)

form_answers = {'hospital': 'hospital',
                'picky_eater': 'True',
                'wake_time': 'wake time',
                'hospitalizations': 'True',
                'nap_times': 'nap time',
                'birth_weight': 'birth weight',
                'doctor': 'DR so&so',
                'medications_detail': 'med details',
                'sleep_thru_night': 'thru the night',
                'delivery_complications': 'False',
                'vision_test': 'True',
                'milk': 'True',
                'care_giver':'mother',
                'surgeries': 'True',
                'illnesses': 'True',
                'hospitalizations_detail': 'hopst details',
                'bed_time': 'bed time',
                'hearing_test_detail': 'hearing details',
                'hearing_test': 'True',
                'gestation': 'gestation',
                'delivery_method': 'natural',
                'surgeries_detail': 'surguries details',
                'medications': 'True',
                'picky_eater_detail': 'picky eater',
                'allergies': 'True',
                'delivery_complications_detail': 'd copml',
                'birth_complications_detail': 'birth comp',
                'birth_complications': 'True',
                'vision_test_detail': 'vision Details',
                'birth_length': 'birth length',
                'allergies_detail': 'allergies',
                'illnesses_detail': 'illness details',
                'milk_detail': 'milk details',
                'birth_history': 'True'}

create_background(eval, form_answers)
