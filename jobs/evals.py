import sys, os, datetime, calendar, json

from sqlalchemy import and_, func, between

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def create_report(client_eval):

    client = client_eval.client

    last_eval = client.evals.order_by(models.ClientEval.created_date.desc()).first()

    eval_report = models.EvalReport()

    # Generate Client Background

    background = create_background(client)

    eval_report.sections.append(models.ReportSection(name='background', text=background, section_title='Background'))

    # Generate Social History

    eval_report.sections.append(models.ReportSection(name='social_history',  section_title='Social History'))

    # Generate Care Givers Concerns

    eval_report.sections.append(models.ReportSection(name='care_giver_concerns',  section_title='Concerns'))

    # Generate Evalution Tools

    eval_report.sections.append(models.ReportSection(name='eval_tools',  section_title='Evaluation Tools'))

    # Generate Testing Environment

    eval_report.sections.append(models.ReportSection(name='test_environment',  section_title='Testing Environment'))

    # Generate Validity of Findings

    eval_report.sections.append(models.ReportSection(name='findings_validity',  section_title='Validity of Findings'))

    # Generate Clinical Observations

    eval_report.sections.append(models.ReportSection(name='clinical_observations',  section_title='Clinical Observations'))

    # Bayley Summary Text

    # Bayley subtests - Order of Administration

    # Day-C Summary Text

    # Day-c subtests - Order of Administration

    subtest_info = get_subtest_info(client_eval)

    eval_report.sections = eval_report.sections.all() +  [models.ReportSection(name=a['subtest_name'].lower(), eval_subtest_id=a['subtest_id'], text=a['write_up'], section_title=a['subtest_name']) for a in subtest_info]

    # Generate Eval Summary

    test_results = create_eval_summary(subtest_info, client, client_eval)

    eval_report.sections.append(models.ReportSection(name='test_results',  section_title='Summary of Evaluation', text=test_results))

    # Generate Recommendations

    eval_report.sections.append(models.ReportSection(name='recommendations',  section_title='Recommendations', text='\nRegional center to make the final determination of eligibility and services.'))

    # Generate old goals if exist

    if last_eval:
        eval_report.sections.append(models.ReportSection(name='old_goals',  section_title='Previous Goals'))

    # Generate new Goals

    eval_report.sections.append(models.ReportSection(name='new_goals',  section_title='Goals'))

    # Generate Closing & Signature

    therapist_name = ' '.join([client.therapist.user.first_name, client.therapist.user.last_name])

    eval_report.sections.append(models.ReportSection(name='closing',  section_title='Closing', text='__________________MA, OTR/L\n%s, MA, OTR/L\nPediatric Occupational Therapist\nFounder/Clinical Director\nSarah Bryan Therapy' % therapist_name))

    client_eval.report = eval_report
    db.session.add(client_eval)
    db.session.commit()

    return True

def create_eval_summary(subtests, client, eval):

    client_info = {}

    age = get_client_age(client.birthdate, eval.created_date)
    age = age[:age.find('M')].strip()

    client_info['first_name'] = client.first_name
    client_info['age_in_months'] = age
    client_info['pronoun'] = 'he' if client.gender == 'M' else 'she'
    client_info['child'] = 'boy' if client.gender == 'M' else 'girl'
    client_info['possessive_pronoun'] = 'his' if client.gender == 'M' else 'her'

    subtest_order = [[],[],[]]
    test_names = [[],[],[]]

    for subtest in subtests:
        if subtest['scaled_score'] >= 8:
            subtest_list = 0
        elif subtest['scaled_score'] == 7:
            subtest_list = 1
        else:
            subtest_list = 2

        subtest_order[subtest_list].append(subtest)
        test_names[subtest_list].append(subtest['subtest_name'].lower())

    summary_text = []

    first_paragraph = True

    for i, tests in enumerate(subtest_order):
        tests_length = len(tests)

        if tests_length == 0:
            continue

        paragraph = []

        if i == 0:
            skill_level = 'average'
        elif i == 1:
            skill_level = 'borderline'
        else:
            skill_level = 'delayed'

        if tests_length == 1:
            tests_text = test_names[i][0]
        elif tests_length == 2:
            tests_text = ' and '.join(test_names[i])
        else:
            tests_text = ', '.join(test_names[i][:tests_length-1]) + ' and ' + test_names[i][tests_length-1]

        if first_paragraph:
            s1 = '%(first_name)s is a happy, %(age_in_months)s month old %(child)s who presented with ' % client_info
            first_paragraph = False
        else:
            s1 = '%s presented with ' % client_info['pronoun'].capitalize()

        s1 += '%s skills for %s %s.' %(skill_level, client_info['possessive_pronoun'], tests_text)

        paragraph.append(s1)

        sentence_structure = True

        for test in tests:

            if sentence_structure:
                s2 = '%s scored within the %s month range for %s %s.' % (client_info['first_name'], test['age_equivalent']//12, client_info['possessive_pronoun'], test['subtest_name'].lower())
                s3_start = '%s ' % client_info['pronoun'].capitalize()
                s3_able = 'was able to'
                s3_unable = 'was unable to'
            else:
                s2 = 'Results indicated that %s\'s %s is in the %s month age range.' % (client_info['first_name'],test['subtest_name'].lower(), test['age_equivalent']//12)
                s3_start = 'It was reported that %s ' % client_info['pronoun']
                s3_able = 'can'
                s3_unable = 'can not'

            sentence_structure = not sentence_structure

            paragraph.append(s2)

            if i == 0:
                s3 =  '%s %s, %s, and %s.' % (s3_able, test['able'][0], test['able'][1], test['able'][2])
            elif i == 1:
                s3 = '%s %s and %s, but %s %s or %s.' % (s3_able, test['able'][0], test['able'][1], s3_unable, test['unable'][0], test['unable'][1])
            else:
                s3 = '%s %s, %s, or %s.' % (s3_unable, test['unable'][0], test['unable'][1], test['unable'][2])

            s3 = s3_start + s3

            paragraph.append(s3)

        summary_text.append('  '.join(paragraph))

    report_summary = '\n\n'.join(summary_text)

    return report_summary


def get_subtest_info(eval):

    subtest_info = []

    for subtest in eval.subtests:

        eval_subtest = models.ClientEvalSubtestLookup.query.filter_by(client_eval_id=eval.id, subtest_id=subtest.id).first()

        subtest_obj = {'scaled_score': eval_subtest.scaled_score,
                       'age_equivalent': eval_subtest.age_equivalent,
                       'test_name': subtest.eval.name,
                       'subtest_name': subtest.name,
                       'subtest_id': subtest.id
                       }

        able = eval.answers.filter(models.ClientEvalAnswer.answer == 1, models.EvalQuestion.subtest_id == subtest.id).order_by(models.EvalQuestion.question_num.desc()).limit(5)

        unable = eval.answers.filter(models.ClientEvalAnswer.answer == 0, models.EvalQuestion.subtest_id == subtest.id).order_by(models.EvalQuestion.question_num).limit(5)

        subtest_obj['able'] = [a.question.report_text for a in able]
        subtest_obj['unable'] = [a.question.report_text for a in unable]

        write_up_sentence_1 = 'Results indicated that %s\'s %s is in the %s month age range.' % (eval.client.first_name, subtest.name.lower(), int(subtest_obj['age_equivalent']/12))

        pronoun = 'he' if eval.client.gender == 'M' else 'she'

        able_1, able_2, able_3 = subtest_obj['able'][:3]
        unable_1, unable_2, unable_3 = subtest_obj['unable'][:3]

        if subtest.eval.id == 1:
            write_up_sentence_2 = '%s was able to %s, %s and %s.' % (pronoun.capitalize(), able_1, able_2, able_3)
        else:
            write_up_sentence_2 = 'It was reported that %s can %s, %s and %s.' %(pronoun, able_1, able_2, able_3)

        if subtest.eval.id == 1:
            write_up_sentence_3 = '%s was not able to %s, %s or %s.' % (pronoun.capitalize(), unable_1, unable_2, unable_3)
        else:
            write_up_sentence_3 = 'It was reported that %s cannot %s, %s or %s.' %(pronoun,  unable_1, unable_2, unable_3)

        subtest_obj['write_up'] = '  '.join([write_up_sentence_1, write_up_sentence_2, write_up_sentence_3])

        subtest_info.append(subtest_obj)

    return subtest_info



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


def create_background(client):

    client_info = {}
    client_info['first_name'] = client.first_name
    client_info['pronoun'] = 'he' if client.gender == 'M' else 'her'
    client_info['possessive_pronoun'] = 'his' if client.gender == 'M' else 'hers'
    background_info = client.background

    background_list = []

    # Start Paragraph 1

    paragraph_one = []

    birth = """%s was born at %s at %s weeks gestation via %s delivery.""" % (client_info['first_name'], background_info.born_hospital, background_info.gestation, background_info.delivery)

    paragraph_one.append(birth)

    weight = """%s weighed %s and measured %s at birth.""" % (client_info['pronoun'], background_info.birth_weight, background_info.birth_length)

    paragraph_one.append(weight.capitalize())

    delivery_birth = 'It was reported that there were no complications during pregnancy.' if background_info.pregnancy_complications == 'False' else background_info.pregnancy_complications_detail

    if background_info.pregnancy_complications == 'False' and background_info.delivery_complications == 'False':
        delivery_birth = delivery_birth[:-1] + " or during %s birth." % client_info['possessive_pronoun']
    elif background_info.delivery_complications == 'False':
        delivery_birth += '  ' + 'It was reported there were no complications during birth.'
    else:
        delivery_birth += '  ' + background_info.delivery_complications_detail

    paragraph_one.append(delivery_birth)

    hearing = "It was reported that %s passed %s newborn hearing screen." % (client_info['pronoun'], client_info['possessive_pronoun']) if background_info.newborn_hearing_test == 'False' else background_info.newborn_hearing_test_detail

    paragraph_one.append(hearing)

    vision = "It was reported that %s passed %s vision screen." % (client_info['pronoun'], client_info['possessive_pronoun']) if background_info.vision_test == 'False' else background_info.vision_test_detail

    paragraph_one.append(vision)

    background_list.append(paragraph_one)

    # Start Paragraph 2

    paragraph_two = []

    p2_sentence_one = '%s has had no ' % client_info['first_name']

    p2_sentence_one_list = []

    p2_sentence_one_details = []

    if background_info.hospitalizations == 'False':
        p2_sentence_one_list.append('significant hospitalizations')
    else:
        p2_sentence_one_details.append(background_info.hospitalizations_detail)

    if background_info.medical_concerns == 'False':
        p2_sentence_one_list.append('ongoing medical concerns')
    else:
        p2_sentence_one_details.append(background_info.medical_concerns_detail)

    if background_info.illnesses == 'False':
        p2_sentence_one_list.append('major illnesses')
    else:
        p2_sentence_one_details.append(background_info.illnesses_detail)

    if background_info.surgeries == 'False':
        p2_sentence_one_list.append('surgeries')
    else:
        p2_sentence_one_details.append(background_info.surgeries_detail)

    if len(p2_sentence_one_list) == 1:
        p2_sentence_one += p2_sentence_one_list[0]

        paragraph_two.append(p2_sentence_one + ' since %s birth.' % client_info['possessive_pronoun'])
    elif len(p2_sentence_one_list) > 1:
        for i, x in enumerate(p2_sentence_one_list):
            if i == len(p2_sentence_one_list) - 1:
                p2_sentence_one = p2_sentence_one[:-2] + ' or ' + x
            else:
                p2_sentence_one += x + ', '

        paragraph_two.append(p2_sentence_one + ' since %s birth.' % client_info['possessive_pronoun'])

    if len(p2_sentence_one_details) > 0:
        paragraph_two.append('  '.join(p2_sentence_one_details))



    p2_sentence_two = 'It was reported that %s ' %client_info['first_name']
    p2_sentence_two_list = []
    p2_sentence_two_details = []

    if background_info.medications == 'False':
        p2_sentence_two_list.append('does not take any medications')
    else:
        p2_sentence_two_details.append(background_info.medications_detail)

    if background_info.allergies == 'False':
        p2_sentence_two_list.append('has no known allergies')
    else:
        p2_sentence_two_details.append(background_info.allergies_detail)

    if background_info.immunizations == 'False':
        p2_sentence_two_list.append('has up-to-date immunizations')
    else:
        p2_sentence_two_details.append(background_info.immunizations_detail)

    if len(p2_sentence_two_list) == 1:
        p2_sentence_two += p2_sentence_two_list[0]
        paragraph_two.append(p2_sentence_two + '.')
    elif len(p2_sentence_two_list) > 1:
        for i, x in enumerate(p2_sentence_two_list):
            if i == len(p2_sentence_two_list) - 1:
                p2_sentence_two = p2_sentence_two[:-2] + ' and ' + x
            else:
                p2_sentence_two += x + ', '

        paragraph_two.append(p2_sentence_two + '.')


    if len(p2_sentence_two_details) > 0 and p2_sentence_two_details[0] != None:
        paragraph_two.append('  '.join(p2_sentence_two_details))

    if background_info.pediatrician:
        p2_sentence_three = 'It was reported that %s is being followed by %s pediatrician, %s.' % (client_info['first_name'], client_info['possessive_pronoun'], background_info.pediatrician)

        if background_info.last_seen_appt:
            p2_sentence_three += '  %s was last seen %s.' % (client_info['first_name'].capitalize(), background_info.last_seen_appt)

        if background_info.last_seen_appt and background_info.follow_up_appt:
            p2_sentence_three = p2_sentence_three[:-1] + ' and is scheduled to be seen %s.' % (background_info.follow_up_appt)
        elif background_info.follow_up_appt:
            p2_sentence_three += '  %s is scheduled to be seen %s.' % (client_info['pronoun'].capitalize(), background_info.follow_up_appt)

        if background_info.specialist == 'True':
            p2_sentence_three += '  It was reported that %s is also being seen by: %s' %(client_info['first_name'], background_info.specialist_detail)

        paragraph_two.append(p2_sentence_three)

    background_list.append(paragraph_two)

    # Paragraph 3

    paragraph_three = []


    p3_sentence_1 = "It was reported that %s met %s developmental milestones as follows: " % (client_info['first_name'], client_info['possessive_pronoun'])

    p3_sentence_1_list = []

    if background_info.roll:
        p3_sentence_1_list.append('rolled at %s' % background_info.roll)
    if background_info.sit:
        p3_sentence_1_list.append('sat unsupported at %s' % background_info.sit)
    if background_info.crawl:
        p3_sentence_1_list.append('crawled at %s' % background_info.crawl)
    if background_info.walk:
        p3_sentence_1_list.append('walked at %s' % background_info.walk)
    if background_info.first_speak:
        p3_sentence_1_list.append('first spoke at %s' % background_info.first_speak)
    if background_info.combine_speak:
        p3_sentence_1_list.append('combined words at %s' % background_info.combine_speak)

    if len(p3_sentence_1_list) > 0:
        p3_sentence_1 += ', '.join(p3_sentence_1_list)
        paragraph_three.append(p3_sentence_1)


    p3_sentence_2 = "It was reported that %s goes to bed at %s and wakes up at %s" % (client_info['first_name'], background_info.bed_time, background_info.wake_time)

    if background_info.sleep_thru_night == 'False':
        p3_sentence_2 += ' sleeping through the night.'
    else:
        p3_sentence_2 += '.  %s' % background_info.sleep_thru_night_detail

    paragraph_three.append(p3_sentence_2)


    p3_sentence_3 = 'It was reported that %s takes naps at %s.' % (client_info['pronoun'], background_info.nap_time)

    paragraph_three.append(p3_sentence_3)


    p3_sentence_4 = 'It was reported that %s ' % client_info['pronoun']

    if background_info.picky_eater == 'good':
        p3_sentence_4 += 'eats well.'
    elif background_info.picky_eater == 'kind_of':
        p3_sentence_4 += 'sometimes eats well and is sometimes picky.'
    else:
        p3_sentence_4 += 'is a picky eater.'

    if background_info.feeding_concerns:
        p3_sentence_4 += '  %s' % background_info.feeding_concerns

    paragraph_three.append(p3_sentence_4)

    p3_sentence_5 = 'It was reported that %s drinks %s of %s per day.' % (client_info['pronoun'], background_info.milk_amount, background_info.milk)

    paragraph_three.append(p3_sentence_5)

    feeding_skills = background_info.feeding_skills

    p3_sentence_6 = 'It was reported that %s will ' % client_info['first_name']

    p3_sentence_6_list = []

    if 'finger_feed' in feeding_skills:
        p3_sentence_6_list.append('finger feed')
    if 'use_spoon' in feeding_skills:
        p3_sentence_6_list.append('use a spoon or fork')
    if 'sippy_cup' in feeding_skills:
        p3_sentence_6_list.append('drink from a sippy cup')
    if 'open_cup' in feeding_skills:
        p3_sentence_6_list.append('drink from an open cup')
    if 'straw' in feeding_skills:
        p3_sentence_6_list.append('use a straw')

    if len(p3_sentence_6_list) == 1:
        p3_sentence_6 += feeding_skills[0] + '.'
        paragraph_three.append(p3_sentence_6)

    elif len(p3_sentence_6_list) > 1:
        for i, x in enumerate(p3_sentence_6_list):
            if i == len(p3_sentence_6_list) - 1:
                p3_sentence_6 = p3_sentence_6[:-2] + ' and ' + x
            else:
                p3_sentence_6 += x + ', '

        paragraph_three.append(p3_sentence_6 + '.')

    background_list.append(paragraph_three)

    paragraph_four = []

    if background_info.interaction_ops != '':
        p4_sentence_1 = 'It was reported that %s has opportunities to interact with other children at %s' %(client_info['first_name'], background_info.interaction_ops)
    else:
        p4_sentence_1 = 'It was reported that %s does not have opportunities to interact with other childern.' % client_info['first_name']

    paragraph_four.append(p4_sentence_1)

    if background_info.how_interact_children != '':
        p4_sentence_2 = background_info.how_interact_children
        paragraph_four.append(p4_sentence_2)

    if background_info.how_interact_adults != '':
        p4_sentence_3 = background_info.how_interact_adults
        paragraph_four.append(p4_sentence_3)

    if background_info.negative_behavior != '':
        p4_sentence_4 = background_info.negative_behavior
    else:
        p4_sentence_4 = 'It was reported that %s has no negative behaviors.' % client['first_name']

    paragraph_four.append(p4_sentence_4)

    # Toy dislikes???

    background_list.append(paragraph_four)



    # Feeding Skills details

    # Paragraph 4

    # "it was reported that client has opportunities to interact with other children at "  details
    # does not have opportunities

    # reported that pronoun interacts with other children"  details

    # Add to line above " and interacts with adults " details

    # "reported that client has no negative behaviors " else details

    # Toy likes & dislikes - details text box unique characteritics on form

    # new section & Paragraph
    # Social history

    # "client lives at home with :  "  people details "In " location_details

    # "It was reported that in the home client is exposed to " language details

    # family schedule, employment and details

    # "It was reported there is no family history of delays or disabilities" else family history details.

    # new Section & paragraph
    # concerns

    # Open Text box - Concerns & hopes and dreams & Goals

    # New section
    # Testing environment

    # "Evaluation was performed at appt_location. eval_attendees were present during the evaluation."

    # New sections
    # validity of findings
    # Radio button, go well or not.
    # if goes well: "Evaluation was performed with minimal distractions and %(first_name)s demonstrated adequate engagement with therapist. He attempted to complete all presented tasks, requiring minimal redirections.  Results accurately reflect %(possessive_pronoun)s current level of functioning." else details

    # new section
    # Clinical Observations
    # Open ended text box

    # Results of eval subtests ...

    # yes/able to perform ordered by id desc limit 5

    # no/unable to perform ordered by id asc limit 5

    # Summary

    # Age needs to be adjusted to proper age Needs input to


    # order subtests by scaled scores grouping desc
    # for every subtest performed in eval
    # If client has all >8 scaled scores
    # scaled score of 7 is borderline
    # < 6 is delayed
    # Sentence for cognition: "Client scored with the age equivalency for subtest"
    # if average:
    # 3 yeses desc by id
    # if borderline: 2 yeses desc by id & 2 nos asc by id
    # if delayed: 3 nos asc by id

    # New Section:
    # Recommendations
    # Blank text field with last sentnece prepopped: 'Regional center to make the final determination of eligibility and services.'

    # new Section Goals:
    # pre populate text box with: bullet "client_first_name will "


    # new section
    # Conclusion:

    # "It was a pleasure working with %(first_name)s and %(possessive_pronoun)s family. Please feel free to contact me with any questions in regards to this case.

    # __________________MA, OTR/L
    # Sarah Putt, MA, OTR/L
    # Pediatric Occupational Therapist
    # Founder/Clinical Director
    # Sarah Bryan Therapy"
    #



    # paragraph_one.append(hospitalizations)

    for x, paragraph in enumerate(background_list):
        background_list[x] = '  '.join(paragraph)

    background =  '\n\n'.join(background_list)

    # print(background)

    return background

# client = models.Client.query.get(12)
#
# create_background(client)


# create_report(models.ClientEval.query.get(8))
