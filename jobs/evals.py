import sys, os, shutil, datetime, json

from dateutil.relativedelta import relativedelta

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
    age_tuple = get_client_age(eval.client.birthdate, eval.appt.start_datetime)
    report_info['client'].age_string = '%s months %s days' % age_tuple
    report_info['client'].adjusted_age_string = None

    if age_tuple[0] < 24 and eval.client.weeks_premature >= 4:
        adjusted_age_tuple = get_client_age(eval.client.birthdate + datetime.timedelta(int(eval.client.weeks_premature * 7 // 1)), eval.appt.start_datetime)
        report_info['client'].adjusted_age_string = '%s months %s days' % adjusted_age_tuple

    report_info['eval'] = eval
    report_info['eval'].report_date = datetime.datetime.now()

    report_info['sections'] = []

    report_info['eval_sections'] = {'background': [],
                                    'evaluations': [],
                                    'recommendations': []}

    section_order = ['background', 'evaluations', 'recommendations']

    section_index = 0
    eval_subtest = False
    sections = models.ReportSection.query.filter(models.ReportSection.report.has(client_eval_id = eval.id)).order_by(models.ReportSection.section_order_id)

    for section in sections:

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
                    # Need to handle null subtest scores.  Hopefully through the new scoring.
                    if subtest_scores.age_equivalent is None:
                        subtest_scores.age_equivalent = 0


            test_info['subtests'].append({'scores': subtest_scores,
                                          'report_section': section})

    report_tpl.render(report_info)

    report_tpl.save(os.path.join(file_directory_path, 'eval_report.docx' ))

    return True


def create_report(client_eval):

    client = client_eval.client

    pronoun = 'he' if client.gender == 'M' else 'she'
    possessive_pronoun = 'his' if client.gender == 'M' else 'her'

    client_info = {}

    client_info['first_name'] = client.first_name
    client_info['pronoun'] = 'he' if client.gender == 'M' else 'she'
    client_info['child'] = 'boy' if client.gender == 'M' else 'girl'
    client_info['possessive_pronoun'] = 'his' if client.gender == 'M' else 'her'

    previous_evals = client.evals.order_by(models.ClientEval.created_date.desc()).all()

    last_eval = None

    if len(previous_evals) > 1:
        last_eval = previous_evals[1]

    eval_report = client_eval.report if client_eval.report else models.EvalReport()

    # Generate Client Background

    section_names = [section.name for section in eval_report.sections]

    section_index = 1

    if client.background:

        if 'background' not in section_names:
            if last_eval:
                try:
                    background = last_eval.report.sections.filter(models.ReportSection.name == 'background').first().text
                except:
                    background = create_background(client)
            else:
                background = create_background(client)

            eval_report.sections.append(models.ReportSection(name='background', text=background, section_title='Background', section_order_id = section_index))

        section_index += 1
        if 'social_history' not in section_names:
            if last_eval:
                try:
                    social_history = last_eval.report.sections.filter(models.ReportSection.name == 'social_history').first().text
                except:
                    social_history = create_social_history(client_eval, client_info)
            else:
                social_history = create_social_history(client_eval, client_info)

            eval_report.sections.append(models.ReportSection(name='social_history', text=social_history, section_title='Social History', section_order_id = section_index))

        # Generate Care Givers Concerns
        # From Background input
        section_index += 1
        if 'care_giver_concerns' not in section_names:
            if last_eval:
                try:
                    concerns = last_eval.report.sections.filter(models.ReportSection.name == 'care_giver_concerns').first().text
                except:
                    concerns = create_concerns(client_eval, client_info)
            else:
                concerns = create_concerns(client_eval, client_info)

            eval_report.sections.append(models.ReportSection(name='care_giver_concerns', text=concerns, section_title='Concerns', section_order_id = section_index))

        # Generate Evalution Tools

        # Is this needed as it is built in the report with the evals?

        # eval_report.sections.append(models.ReportSection(name='eval_tools',  section_title='Evaluation Tools'))
    if not client.background:
        section_index = 3

    section_index += 1
    if 'test_environment' not in section_names:
        # Generate Testing Environment

        # Need to find appt location for eval?  - is there a tie to an appt for an eval?
        test_environment = create_testing_environment(client_eval, client_info)

        eval_report.sections.append(models.ReportSection(name='test_environment', text=test_environment, section_title='Testing Environment', section_order_id = section_index))

    # Generate Validity of Findings
    section_index += 1
    if 'findings_validity' not in section_names:

        findings = "Evaluation was performed with minimal distractions and %s demonstrated adequate engagement with therapist. %s attempted to complete all presented tasks, requiring minimal redirections.  Results accurately reflect %s current level of functioning." % (client.first_name, pronoun.capitalize(), possessive_pronoun)

        eval_report.sections.append(models.ReportSection(name='findings_validity', text=findings,  section_title='Validity of Findings', section_order_id = section_index))
    section_index += 1
    if 'clinical_observations' not in section_names:
        # Generate Clinical Observations
        client_info['pronoun_cap'] = client_info['pronoun'].capitalize()

        text = '''{first_name} entered the testing room with {possessive_pronoun} parents. {first_name} greeted therapist at the door. {first_name} was asleep when therapist entered the home.  {pronoun_cap} demonstrated awareness of others in the room, made eye contact, and smiled when given attention.  {pronoun_cap} required a minimal/ moderate habituation period before beginning to engage in testing materials. {pronoun_cap} transitioned from one activity to another with ease and followed simple directions. {pronoun_cap} made vocalizations, produced consonant vowel combinations, pointed to objects {pronoun} wanted, used words to communicate {possessive_pronoun} wants and needs.  {pronoun_cap} was able to crawl and walk in order to explore {possessive_pronoun} environment. {pronoun_cap} enjoyed engaging with hands on activities.'''.format(**client_info)

        eval_report.sections.append(models.ReportSection(name='clinical_observations', text=text, section_title='Clinical Observations', section_order_id = section_index))

    # Generate summary and report for each subtest

    subtest_info = get_subtest_info(client_eval)

    for a in subtest_info:
        section_index += 1
        if a['subtest_name'].lower() not in section_names:

            eval_report.sections = eval_report.sections.all() + [models.ReportSection(name=a['subtest_name'].lower(), eval_subtest_id=a['subtest_id'], text=a['write_up'], section_title=a['subtest_name'], section_order_id = section_index)]

    # Generate Eval Summary
    section_index += 1
    if 'test_results' not in section_names:
        test_results = create_eval_summary(subtest_info, client, client_eval)

        eval_report.sections.append(models.ReportSection(name='test_results',  section_title='Summary of Evaluation', text=test_results, section_order_id = section_index))

    section_index += 1
    if 'recommendations' not in section_names:
        # Generate Recommendations

        eval_report.sections.append(models.ReportSection(name='recommendations',  section_title='Recommendations', text='\n\nRegional center to make the final determination of eligibility and services.', section_order_id = section_index))

    # Generate old goals if exist
    section_index += 1
    if 'old_goals' not in section_names:
        if last_eval:
            try:
                goals = last_eval.report.sections.filter(models.ReportSection.name == 'new_goals').first().text
                eval_report.sections.append(models.ReportSection(name='old_goals',  text=goals, section_title='Previous Goals', section_order_id = section_index))
            except:
                pass

    section_index += 1
    if 'new_goals' not in section_names:
        # Generate new Goals

        eval_report.sections.append(models.ReportSection(name='new_goals',  section_title='Goals', section_order_id = section_index))

    # Generate Closing & Signature
    section_index += 1
    if 'closing' not in section_names:
        therapist_name = ' '.join([client.therapist.user.first_name, client.therapist.user.last_name])

        # Need signature for Therapist User?  Add it to user profile for therapists?
        signature = '_' * 25 + 'MA, OTR/L\n%s, MA, OTR/L\nPediatric Occupational Therapist\nFounder/Clinical Director\n%s' % (therapist_name, client.therapist.company.name)

        closing = 'It was a pleasure working with %s and %s family. Please feel free to contact me with any questions in regards to this case.\n\n%s' % (client_info['first_name'], client_info['possessive_pronoun'], signature)

        eval_report.sections.append(models.ReportSection(name='closing', text=closing, section_title='Closing', section_order_id = section_index))

    client_eval.report = eval_report
    db.session.add(client_eval)
    db.session.commit()

    return True




def create_social_history(eval, client_info):

    client = eval.client

    social_history_list = []

    s_1 = 'It was reported that %(first_name)s lives at home with %(possessive_pronoun)s ' % client_info
    family = json.loads(client.background.family)
    family_list = []
    for member in family:
        family_list.append((member, family[member]['relationship']))

    family_list = sorted(family_list, key=lambda x: x[0])

    if len(family_list) == 1:
        s_1 += family_list[0][1] + '.'
    else:
        family_members = []
        for mem in family_list:
            # if mem[2] == '' or mem[2] is None:
            family_members.append(mem[1].lower())
            # else:
            #     try:
            #         dob = datetime.datetime.strptime(mem[2], '%m/%d/%Y')
            #         now = datetime.datetime.now()
            #
            #         difference = relativedelta(now,dob)
            #
            #         if difference.years > 1:
            #             age = '(%s years)' % difference.years
            #         else:
            #             age = '(%s months)' % difference.months
            #     except:
            #         age = mem[2]
            #
            #     family_members.append(mem[1].lower() + ' ' + age)


        s_1 += ', '.join(family_members[:-1]) + ' and ' + family_members[-1] +'.'

    social_history_list.append(s_1)

    s_2 = '%(pronoun)s is exposed to ' % client_info

    s_2 = s_2.capitalize()

    s_2 += client.background.languages + ' in the home.'

    social_history_list.append(s_2)

    # s_3 = 'It was reported that %(pronoun)s is cared for by '  % client_info
    #
    # s_3 += client.background.daycare + '.'
    #
    # social_history_list.append(s_3)

    if client.background.family_schedule.strip() == 'It was reported that':
        s_4 = ''
    else:
        s_4 = client.background.family_schedule

    social_history_list.append(s_4)

    s_5 = 'It was reported that there is no family history of delays.'

    if client.background.history_of_delays == 'True' and client.background.history_of_delays_detail != None:
        s_5 = client.background.history_of_delays_detail

    social_history_list.append(s_5)

    if client.background.interaction_ops != '':
        s_6 = 'It was reported that %s has opportunities to interact with other children at %s' %(client_info['first_name'], client.background.interaction_ops)
    else:
        s_6 = 'It was reported that %s does not have opportunities to interact with other childern.' % client_info['first_name']

    social_history_list.append(s_6)

    if client.background.how_interact_children != '':
        s_7 = client.background.how_interact_children
        social_history_list.append(s_7)

    if client.background.how_interact_adults != '':
        s_8 = client.background.how_interact_adults
        social_history_list.append(s_8)

    if client.background.negative_behavior != '':
        s_9 = client.background.negative_behavior
    else:
        s_9 = 'It was reported that %s has no negative behaviors.' % client_info['first_name']

    social_history_list.append(s_9)

    social_history = '  '.join(social_history_list)

    return social_history




def create_concerns(eval, client_info):

    client = eval.client

    concerns = client.background.concerns

    return concerns




def create_testing_environment(eval, client_info):

    client = eval.client

    appt = eval.appt

    address = appt.location

    regional_center = client.regional_center
    regional_center_address = regional_center.address + ' ' + regional_center.city + ', ' + regional_center.state + ' ' + regional_center.zipcode

    family = json.loads(client.background.family)
    family_list = []
    for member in family:
        family_list.append((member, family[member]['relationship'].lower()))

    family_list = sorted(family_list, key=lambda x: x[0])

    family_list_text = ', '.join([mem[1] for mem in family_list])

    if regional_center_address == address:
        testing_environment = 'Evaluation was performed at %s Regional Center in %s, %s.  %s, %s, %s case coordinator and the evaluating occupational therapist were present during the evaluation.' % (regional_center.name, regional_center.city, regional_center.state, client.first_name.capitalize(), family_list_text, regional_center.appt_reference_name)
    else:
        testing_environment = 'Evaluation was performed in the client\'s home in %s, %s.  %s, %s, %s case coordinator and the evaluating occupational therapist were present during the evaluation.' % (client.city, client.state, client.first_name.capitalize(), family_list_text, regional_center.appt_reference_name)

    return testing_environment




def create_eval_summary(subtests, client, eval):

    client_info = {}

    age = get_client_age(client.birthdate, eval.appt.start_datetime)

    client_info['first_name'] = client.first_name
    client_info['age_in_months'] = age[0]
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
            skill_level = 'delays'

        if tests_length == 1:
            tests_text = test_names[i][0]
        else:
            tests_text = ', '.join(test_names[i][:-1]) + ' and ' + test_names[i][-1]

        if first_paragraph:
            s1 = '%(first_name)s is a %(age_in_months)s month old %(child)s who presented with ' % client_info
            first_paragraph = False
        else:
            s1 = '%s presented with ' % client_info['pronoun'].capitalize()

        if i <= 1:
            s1 += '%s skills for %s %s.' %(skill_level, client_info['possessive_pronoun'], tests_text)
        else:
            s1 += '%s in %s %s.' %(skill_level, client_info['possessive_pronoun'], tests_text)

        paragraph.append(s1)

        for test in tests:

            if test['test_name'] == 'BAYLEY':
                s2 = '%s scored within the %s month range for %s %s.' % (client_info['first_name'], test['age_equivalent']//30, client_info['possessive_pronoun'], test['subtest_name'].lower())

                if 'motor' in test['subtest_name'].lower():
                    s2 = s2[:-1] + ' skills.'

                s3_start = '%s ' % client_info['pronoun'].capitalize()
                s3_able = 'was able to'
                s3_unable = 'was unable to'

            else:
                s2 = 'Results indicated that %s\'s %s is in the %s month age range.' % (client_info['first_name'],test['subtest_name'].lower(), test['age_equivalent']//30)

                s3_start = 'It was reported that %s ' % client_info['pronoun']
                s3_able = 'can'
                s3_unable = 'cannot'

            paragraph.append(s2)
            print(test)
            s3_able_array = [a[0] for a in test['able']]
            s3_unable_array = [a[0] for a in test['unable']]

            if i == 0:
                s3 =  s3_able + ' ' + ', '.join(s3_able_array[:-1]) + ' and ' if len(s3_able_array) > 1 else ''
                s3 += s3_able_array[-1] + '.'
            elif i == 1:
                s3 = '%s %s,' % (s3_able, test['able'][0][0])
                if len(test['able']) > 1:
                    s3 = s3[:-1] + ' and %s,' % (test['able'][1][0])

                s3 += ' but %s %s.' %(s3_unable, test['unable'][0][0])
                if len(test['unable']) > 1:
                    s3 = s3[:-1] + ' or %s.' % (test['unable'][1][0])

            else:
                s3 = s3_unable + ' ' + ', '.join(s3_unable_array[:-1]) + ' or ' if len(s3_unable_array) > 1 else ''
                s3 += s3_unable_array[-1] + '.'

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

        eval_name = subtest.eval.name

        subtest_obj = {'scaled_score': eval_subtest.scaled_score if eval_subtest.scaled_score else 0,
                       'age_equivalent': eval_subtest.age_equivalent if eval_subtest.age_equivalent else 0,
                       'test_name': eval_name,
                       'subtest_name': subtest.name,
                       'subtest_id': subtest.id
                        }


        answers = db.session.query(models.EvalQuestion.question_num,models.EvalQuestion.question_cat, models.EvalQuestion.report_text, models.ClientEvalAnswer.answer).\
                        join(models.ClientEvalAnswer).\
                        filter(models.EvalQuestion.subtest_id == subtest.id, models.ClientEvalAnswer.client_eval_id == eval.id).\
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

        if eval_name == 'BAYLEY':
            write_up_sentence_1 = '%s scored within the %s month age range for %s %s.' % (eval.client.first_name,  int(subtest_obj['age_equivalent']//30), pronouns['possessive_pronoun'], subtest.name.lower())
            if 'motor' in subtest.name.lower():
                write_up_sentence_1 = write_up_sentence_1[:-1] + ' skills.'
        else:
            write_up_sentence_1 = 'Results indicated that %s\'s %s in the %s month age range.' % (eval.client.first_name, subtest.name.lower() + ' is' if 'emotional' not in subtest.name.lower() else subtest.name.lower() + ' skills are', int(subtest_obj['age_equivalent']//30))

        able_write_up = '  '.join(create_subtest_paragraph(able_list, pronoun, True, eval_name))

        unable_write_up = '  '.join(create_subtest_paragraph(unable_list, pronoun, False, eval_name))

        subtest_obj['write_up'] = '  '.join([write_up_sentence_1, able_write_up, unable_write_up])

        subtest_info.append(subtest_obj)

    return subtest_info

def create_subtest_paragraph(categories, pronoun, able, eval_name):

    prefix_1 = ''
    suffix_1 = ''
    conjunction = 'and'
    new_sentence = True

    if not able:
        prefix_1 = 'un'
        suffix_1 = 'not'
        conjunction = 'or'
        new_sentence = False

    reported = ''

    if eval_name != 'BAYLEY':
        reported = 'It was reported that '

    paragraph = []

    for category in categories:

        cat_parts = category

        if len(cat_parts) == 1:
            sentence_end = cat_parts[0]
        else:
            sentence_end = ', '.join(cat_parts[:-1]) + ' %s ' % conjunction + cat_parts[-1]

        if not new_sentence or eval_name == 'BAYLEY':
            write_up_sentence = '%s%s was %sable to %s.' % (reported, pronoun if len(reported) > 0 else pronoun.capitalize(), prefix_1, sentence_end)
        else:
            write_up_sentence = '%s%s can%s %s.' %(reported,  pronoun if len(reported) > 0 else pronoun.capitalize(),  suffix_1, sentence_end)

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

    client_age_tuple = get_client_age(eval.client.birthdate, eval.appt.start_datetime)

    if client_age_tuple[0] < 24 and eval.client.weeks_premature >= 4:
        client_age_tuple = get_client_age(eval.client.birthdate + datetime.timedelta(int(eval.client.weeks_premature * 7 // 1)), eval.appt.start_datetime)

    client_age = client_age_tuple[0]*30 + client_age_tuple[1]

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

	return ((eval_year - birth_year) * 12 + (eval_month - birth_month), eval_day - birth_day)


def create_background(client):

    client_info = {}
    client_info['first_name'] = client.first_name
    client_info['pronoun'] = 'he' if client.gender == 'M' else 'she'
    client_info['possessive_pronoun'] = 'his' if client.gender == 'M' else 'her'
    background_info = client.background

    background_list = []

    # Start Paragraph 1

    paragraph_one = []

    if client.background.gestation == 'full':
        birth = """%s was born at %s in %s, %s at full term via %s delivery.""" % (client_info['first_name'], background_info.born_hospital,background_info.born_city, background_info.born_state, background_info.delivery)
    else:
        birth = """%s was born at %s in %s, %s at %s weeks gestation via %s delivery.""" % (client_info['first_name'], background_info.born_hospital,background_info.born_city, background_info.born_state, background_info.gestation, background_info.delivery)

    paragraph_one.append(birth)

    weight = """%s weighed %s and measured %s inches long at birth.""" % (client_info['pronoun'], background_info.birth_weight, background_info.birth_length)

    paragraph_one.append(weight.capitalize())

    delivery_birth = ''

    if background_info.pregnancy_complications != None or background_info.delivery_complications != None:
        if background_info.pregnancy_complications == 'False':
            delivery_birth += 'It was reported that there were no complications during pregnancy.'
        elif background_info.pregnancy_complications_detail != None and background_info.pregnancy_complications == 'True':
            delivery_birth += background_info.pregnancy_complications_detail
        else:
            delivery_birth += 'There were complications during the pregnancy.'

        if background_info.pregnancy_complications == 'False' and background_info.delivery_complications == 'False':
            delivery_birth = delivery_birth[:-1] + " or during %s birth." % client_info['possessive_pronoun']
        elif background_info.delivery_complications == 'False' or background_info.delivery_complications_detail == None:
            delivery_birth += '  ' + 'It was reported there were no complications during birth.'
        elif background_info.delivery_complications_detail != None:
            delivery_birth += '  ' + background_info.delivery_complications_detail
        elif background_info.delivery_complications_detail == None and background_info.delivery_complications == 'True':
            delivery_birth += '  ' + 'There were also complications with the delivery.'

    paragraph_one.append(delivery_birth)

    if background_info.newborn_hearing_test == 'False':
        hearing = "It was reported that %s passed %s newborn hearing screen." % (client_info['pronoun'], client_info['possessive_pronoun'])
    elif background_info.newborn_hearing_test == 'It was reported that ':
        hearing = ''
    else:
        hearing = background_info.newborn_hearing_test_detail

    paragraph_one.append(hearing)

    if background_info.vision_test == 'False':
        vision = "It was reported that %s passed %s vision screen." % (client_info['pronoun'], client_info['possessive_pronoun'])
    elif background_info.vision_test_detail == 'It was reported that ':
        vision = ''
    else:
        vision = background_info.vision_test_detail

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
        if background_info.hospitalizations_detail:
            p2_sentence_one_details.append(background_info.hospitalizations_detail)

    if background_info.medical_concerns == 'False':
        p2_sentence_one_list.append('ongoing medical concerns')
    else:
        if background_info.medical_concerns_detail:
            p2_sentence_one_details.append(background_info.medical_concerns_detail)

    if background_info.illnesses == 'False':
        p2_sentence_one_list.append('major illnesses')
    else:
        if background_info.illnesses_detail:
            p2_sentence_one_details.append(background_info.illnesses_detail)

    if background_info.surgeries == 'False':
        p2_sentence_one_list.append('surgeries')
    else:
        if background_info.surgeries_detail:
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



    p2_sentence_two = 'It was reported that '
    p2_sentence_two_list = []
    p2_sentence_two_details = []

    if background_info.medications == 'False':
        p2_sentence_two_list.append('does not take any medications')
    else:
        if background_info.medications_detail:
            p2_sentence_two_details.append(background_info.medications_detail)

    if background_info.allergies == 'False':
        p2_sentence_two_list.append('has no known allergies')
    else:
        if background_info.allergies_detail:
            p2_sentence_two_details.append(background_info.allergies_detail)

    if background_info.immunizations == 'False':
        p2_sentence_two_list.append('%s immunizations are up to date' % client_info['possessive_pronoun'])
    else:
        if background_info.immunizations_detail:
            p2_sentence_two_details.append(background_info.immunizations_detail)

    if len(p2_sentence_two_list) == 1:
        if 'immunizations' not in p2_sentence_two_list[0]:
            p2_sentence_two += client_info['first_name'] + ' '
        p2_sentence_two += p2_sentence_two_list[0]
        paragraph_two.append(p2_sentence_two + '.')
    elif len(p2_sentence_two_list) > 1:
        p2_sentence_two += client_info['first_name'] + ' '
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
            p2_sentence_three = p2_sentence_three[:-1] + ', and was last seen %s.' % (background_info.last_seen_appt)

        if background_info.follow_up_appt:
            p2_sentence_three = p2_sentence_three[:-1] + ', and is scheduled to be seen %s.' % (background_info.follow_up_appt)

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
        p3_sentence_1_list.append('spoke first word at %s' % background_info.first_speak)
    if background_info.combine_speak:
        p3_sentence_1_list.append('combined words at %s' % background_info.combine_speak)

    if len(p3_sentence_1_list) > 0:
        if len(p3_sentence_1_list) > 1:
            p3_sentence_1 += ', '.join(p3_sentence_1_list[:-1])
            p3_sentence_1 += ', and ' + p3_sentence_1_list[-1]
        else:
            p3_sentence_1 += ', '.join(p3_sentence_1_list[:-1])
        paragraph_three.append(p3_sentence_1 + '.')


    p3_sentence_2 = "It was reported that %s goes to bed around %s and wakes up around %s" % (client_info['first_name'], background_info.bed_time, background_info.wake_time)

    if background_info.sleep_thru_night == 'False':
        p3_sentence_2 += ' sleeping through the night.'
    else:
        if background_info.sleep_thru_night_detail:
            p3_sentence_2 += '.  %s' % background_info.sleep_thru_night_detail

    paragraph_three.append(p3_sentence_2)


    p3_sentence_3 = 'It was reported that %s takes naps %s.' % (client_info['pronoun'], background_info.nap_time)

    paragraph_three.append(p3_sentence_3)


    p3_sentence_4 = 'It was reported that %s ' % client_info['pronoun']

    if background_info.picky_eater == 'good':
        p3_sentence_4 += 'eats well.'
    elif background_info.picky_eater == 'kind_of':
        p3_sentence_4 += 'sometimes eats well and is sometimes picky.'
    else:
        p3_sentence_4 += 'is a picky eater.'

    if background_info.feeding_concerns == 'False':
        p3_sentence_4 += '  Care giver reported that there are no feeding concerns at this time.'
    else:
        p3_sentence_4 += '  %s' % background_info.feeding_concerns_detail

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



    # Toy likes & dislikes - details text box unique characteritics on form

    for x, paragraph in enumerate(background_list):
        background_list[x] = '  '.join([a for a in paragraph if a != None])

    background =  '\n\n'.join(background_list)

    return background



# def test(x):
#
#     test_eval = models.ClientEval.query.get(x)
#
#     print('stuff', create_report(test_eval))
#
# test(19)
