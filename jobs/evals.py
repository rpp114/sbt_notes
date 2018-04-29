import sys, os, shutil, datetime

from sqlalchemy import and_, func, between

from docxtpl import DocxTemplate, Listing

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from app import db, models


def create_eval_report_doc(eval):

    if not eval.report:
        print('no report')
        return False

    file_directory_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', 'docs',str(eval.client.regional_center.company_id),'reports/')

    if not os.path.exists(file_directory_path):
        os.makedirs(file_directory_path)
        shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)),'report_template.docx'), file_directory_path)

    report_tpl = DocxTemplate(os.path.join(file_directory_path, 'report_template.docx'))

    report_info = {}

    report_info['client'] = eval.client
    report_info['client'].age_string = get_client_age(eval.client.birthdate, eval.created_date)
    report_info['eval'] = eval
    report_info['eval'].report_date = datetime.datetime.now()

    report_info['sections'] = []

    report_info['eval_sections'] = {'background': [],
                                    'evaluations': [],
                                    'recommendations': []}

    section_order = ['background', 'evaluations', 'recommendations']

    section_index = 0
    eval_subtest = False


    for section in eval.report.sections:

        if eval_subtest != (section.eval_subtest_id != None):
            eval_subtest = not eval_subtest
            section_index += 1

        section_key = section_order[section_index]

        if section_key != 'evaluations':
            section.doc_text = Listing(section.text) if section.text else None
            report_info['eval_sections'][section_key].append(section)
        else:
            section.doc_text = Listing(section.text)
            tests = report_info['eval_sections'][section_key]
            test_info = None

            for test in tests:
                if test['eval'].id == section.subtest.eval.id:
                    test_info = test
                    break

            if test_info == None:
                test_info = {'eval': section.subtest.eval,
                              'subtests': []}
                tests.append(test_info)

            for lookup in eval.eval_subtests:
                if lookup.subtest_id == section.subtest.id:
                    subtest_scores = lookup

            test_info['subtests'].append({'scores': subtest_scores,
                                          'report_section': section})


    report_tpl.render(report_info)

    report_tpl.save(os.path.join(file_directory_path, 'eval_report_%s_%s_%s.docx' % (str(eval.client.id), str(eval.id), datetime.datetime.now().strftime('%Y_%m_%d'))))

    return 'eval_report_%s_%s_%s.docx' % (str(eval.client.id), str(eval.id), datetime.datetime.now().strftime('%Y_%m_%d'))


def create_report(client_eval):

    client = client_eval.client

    pronoun = 'he' if client.gender == 'M' else 'she'
    possessive_pronoun = 'his' if client.gender == 'M' else 'her'

    previous_evals = client.evals.order_by(models.ClientEval.created_date.desc()).all()

    last_eval = None

    if len(previous_evals) > 1:
        last_eval = previous_evals[1]

    eval_report = models.EvalReport()

    # Generate Client Background

    background = create_background(client)

    eval_report.sections.append(models.ReportSection(name='background', text=background, section_title='Background'))

    # Generate Social History
    #  From Background input

    eval_report.sections.append(models.ReportSection(name='social_history',  section_title='Social History'))

    # Generate Care Givers Concerns
    # From Background input

    eval_report.sections.append(models.ReportSection(name='care_giver_concerns',  section_title='Concerns'))

    # Generate Evalution Tools

    # Is this needed as it is built in the report with the evals?

    # eval_report.sections.append(models.ReportSection(name='eval_tools',  section_title='Evaluation Tools'))

    # Generate Testing Environment

    # Need to find appt location for eval?  - is there a tie to an appt for an eval?

    eval_report.sections.append(models.ReportSection(name='test_environment',  section_title='Testing Environment'))

    # Generate Validity of Findings

    findings = "Evaluation was performed with minimal distractions and %s demonstrated adequate engagement with therapist. %s attempted to complete all presented tasks, requiring minimal redirections.  Results accurately reflect %s current level of functioning." % (client.first_name, pronoun.capitalize(), possessive_pronoun)

    eval_report.sections.append(models.ReportSection(name='findings_validity', text=findings,  section_title='Validity of Findings'))

    # Generate Clinical Observations

    eval_report.sections.append(models.ReportSection(name='clinical_observations',  section_title='Clinical Observations'))

    # Generate summary and report for each subtest

    subtest_info = get_subtest_info(client_eval)

    eval_report.sections = eval_report.sections.all() +  [models.ReportSection(name=a['subtest_name'].lower(), eval_subtest_id=a['subtest_id'], text=a['write_up'], section_title=a['subtest_name']) for a in subtest_info]

    # Generate Eval Summary

    test_results = create_eval_summary(subtest_info, client, client_eval)

    eval_report.sections.append(models.ReportSection(name='test_results',  section_title='Summary of Evaluation', text=test_results))

    # Generate Recommendations

    eval_report.sections.append(models.ReportSection(name='recommendations',  section_title='Recommendations', text='\n\nRegional center to make the final determination of eligibility and services.'))

    # Generate old goals if exist

    if last_eval:

        eval_report.sections.append(models.ReportSection(name='old_goals',  section_title='Previous Goals'))

    # Generate new Goals

    eval_report.sections.append(models.ReportSection(name='new_goals',  section_title='Goals'))

    # Generate Closing & Signature

    therapist_name = ' '.join([client.therapist.user.first_name, client.therapist.user.last_name])

    # Need signature for Therapist User?  Add it to user profile for therapists?
    signature = '_' * 25 + 'MA, OTR/L\n%s, MA, OTR/L\nPediatric Occupational Therapist\nFounder/Clinical Director\n%s' % (therapist_name, client.therapist.company.name)

    closing = 'It was a pleasure working with %s and %s family. Please feel free to contact me with any questions in regards to this case.\n\n%s' % (client.first_name, possessive_pronoun, signature)

    eval_report.sections.append(models.ReportSection(name='closing', text=closing, section_title='Closing'))

    client_eval.report = eval_report
    db.session.add(client_eval)
    db.session.commit()

    return True


def create_social_history(eval):

    # new section & Paragraph
    # Social history

    # "client lives at home with :  "  people details "In " location_details

    # "It was reported that in the home client is exposed to " language details

    # family schedule, employment and details

    # "It was reported there is no family history of delays or disabilities" else family history details.

    social_history = 'hmmmm'

    return social_history

def create_concerns(eval):


    # new Section & paragraph
    # concerns

    # Open Text box - Concerns & hopes and dreams & Goals

    concerns = 'concerns'

    return concerns

def create_testing_environment(eval):

    # New section
    # Testing environment

    # "Evaluation was performed at appt_location. eval_attendees were present during the evaluation."

    testing_environment = 'appt?'

    return testing_environment

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
        else:
            tests_text = ', '.join(test_names[i][:-1]) + ' and ' + test_names[i][-1]

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
                s2 = '%s scored within the %s month range for %s %s.' % (client_info['first_name'], test['age_equivalent']//30, client_info['possessive_pronoun'], test['subtest_name'].lower())
                s3_start = '%s ' % client_info['pronoun'].capitalize()
                s3_able = 'was able to'
                s3_unable = 'was unable to'
            else:
                s2 = 'Results indicated that %s\'s %s is in the %s month age range.' % (client_info['first_name'],test['subtest_name'].lower(), test['age_equivalent']//30)
                s3_start = 'It was reported that %s ' % client_info['pronoun']
                s3_able = 'can'
                s3_unable = 'cannot'

            sentence_structure = not sentence_structure

            paragraph.append(s2)

            if i == 0:
                s3 =  '%s %s, %s, and %s.' % (s3_able, test['able'][0][0], test['able'][1][0], test['able'][2][0])
            elif i == 1:
                s3 = '%s %s and %s, but %s %s or %s.' % (s3_able, test['able'][0][0], test['able'][1][0], s3_unable, test['unable'][0][0], test['unable'][1][0])
            else:
                s3 = '%s %s, %s, or %s.' % (s3_unable, test['unable'][0][0], test['unable'][1][0], test['unable'][2][0])

            s3 = s3_start + s3

            paragraph.append(s3)

        summary_text.append('  '.join(paragraph))

    report_summary = '\n\n'.join(summary_text)

    return report_summary


def get_subtest_info(eval):

    subtest_info = []

    pronouns = {}

    pronoun = 'he' if eval.client.gender == 'M' else 'she'

    pronouns['possessive_pronoun'] = 'his'  if pronoun == 'he' else 'her'
    pronouns['self'] = 'him'  if pronoun == 'he' else 'her'
    pronouns['pronoun'] = pronoun

    new_sentence = True

    for subtest in eval.subtests:

        eval_subtest = models.ClientEvalSubtestLookup.query.filter_by(client_eval_id=eval.id, subtest_id=subtest.id).first()

        subtest_obj = {'scaled_score': eval_subtest.scaled_score,
                       'age_equivalent': eval_subtest.age_equivalent,
                       'test_name': subtest.eval.name,
                       'subtest_name': subtest.name,
                       'subtest_id': subtest.id
                       }

        answers = db.session.query(models.EvalQuestion.question_num,models.EvalQuestion.question_cat, models.EvalQuestion.report_text, models.ClientEvalAnswer.answer).\
                        join(models.ClientEvalAnswer).\
                        filter(models.EvalQuestion.subtest_id == subtest.id).\
                        order_by(models.EvalQuestion.question_num.desc()).all()

        able_cat_list = []
        able_list = []

        unable_cat_list = []
        unable_list = []

        for answer in answers:
            if answer[3] == 1:
                if answer[1] not in able_cat_list:
                    able_cat_list += [answer[1]]
                    able_list += [[answer[2] % pronouns]]
                else:
                    i = able_cat_list.index(answer[1])
                    able_list[i] += [answer[2] % pronouns]
            else:
                if answer[1] not in unable_cat_list:
                    unable_cat_list = [answer[1]] + unable_cat_list
                    unable_list = [[answer[2] % pronouns]] + unable_list
                else:
                    i = unable_cat_list.index(answer[1])
                    cat = unable_cat_list.pop(i)
                    temp_list = unable_list.pop(i)
                    unable_cat_list = [cat] + unable_cat_list
                    temp_list = [answer[2] % pronouns] + temp_list
                    unable_list = [temp_list] + unable_list

        subtest_obj['able'] = able_list
        subtest_obj['unable'] = unable_list

        write_up_sentence_1 = 'Results indicated that %s\'s %s is in the %s month age range.' % (eval.client.first_name, subtest.name.lower(), int(subtest_obj['age_equivalent']//30))

        able_write_up = '  '.join(create_subtest_paragraph(able_list, pronoun, able=True))

        unable_write_up = '  '.join(create_subtest_paragraph(unable_list, pronoun, able=False))

        subtest_obj['write_up'] = '\n\n'.join([write_up_sentence_1, able_write_up, unable_write_up])

        subtest_info.append(subtest_obj)

    return subtest_info

def create_subtest_paragraph(categories, pronoun, able=True):

    prefix_1 = ''
    suffix_1 = ''
    conjunction = 'and'
    new_sentence = True

    if not able:
        prefix_1 = 'un'
        suffix_1 = 'not'
        conjunction = 'or'
        new_sentence = False

    paragraph = []

    for category in categories[:3]:

        cat_parts = category[:3]

        if len(cat_parts) == 1:
            sentence_end = cat_parts[0]
        else:
            sentence_end = ', '.join(cat_parts[:-1]) + ' %s ' % conjunction + cat_parts[-1]

        if not new_sentence:
            write_up_sentence = '%s was %sable to %s.' % (pronoun.capitalize(), prefix_1, sentence_end)
        else:
            write_up_sentence = 'It was reported that %s can%s %s.' %(pronoun,  suffix_1, sentence_end)

        new_sentence = not new_sentence

        paragraph.append(write_up_sentence)

    return paragraph




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
    client_info['pronoun'] = 'he' if client.gender == 'M' else 'she'
    client_info['possessive_pronoun'] = 'his' if client.gender == 'M' else 'her'
    background_info = client.background

    background_list = []

    # Start Paragraph 1

    paragraph_one = []

    birth = """%s was born at %s in %s, %s at %s weeks gestation via %s delivery.""" % (client_info['first_name'], background_info.born_hospital,background_info.born_city, background_info.born_state, background_info.gestation, background_info.delivery)

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
        p2_sentence_two_list.append('%s immunizations are up to date' % client_info['possessive_pronoun'])
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
        paragraph_three.append(p3_sentence_1 + '.')


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
        p3_sentence_6 += p3_sentence_6_list[0] + '.'
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
        p4_sentence_4 = 'It was reported that %s has no negative behaviors.' % client_info['first_name']

    paragraph_four.append(p4_sentence_4)

    # Toy dislikes???

    background_list.append(paragraph_four)

    # Toy likes & dislikes - details text box unique characteritics on form

    for x, paragraph in enumerate(background_list):
        background_list[x] = '  '.join([a for a in paragraph if a != None])

    background =  '\n\n'.join(background_list)

    return background



# def test(x):
#
#     test_client = models.Client.query.get(x)
#
#     background = create_background(test_client)
#     print(background)
#     #
#     # for test_eval in test_client.evals.all():
#     #     # get_subtest_info(test_eval)
#     #     create_report(test_eval)
#     #     print(create_eval_report_doc(test_eval))
#
#     # print('created eval reports')
#
#
# test(160)
