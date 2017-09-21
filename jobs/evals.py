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
        print(answer.question.question_num, answer.answer)
        answers_by_subtest[answer.question.subtest.id].append(answer.question.question_num)

    for subtest in answers_by_subtest:
        print(' Raw score on %s is %d' %(subtest, min(answers_by_subtest[subtest]) + len(answers_by_subtest[subtest])-1))
    print(answers_by_subtest)



score_eval(19)
