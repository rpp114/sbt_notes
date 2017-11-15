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

score_eval(36)
