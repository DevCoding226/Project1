import logging

from querystring_parser import parser as queryparser

from django.db import transaction

from survey.models import Country, Survey, Answer, Question
from .models import SurveyStat, OrganizationStat, QuestionStat, Representation, OptionDict

logger = logging.getLogger(__name__)


class AbstractEvaluator(object):

    # https://app.asana.com/0/232511650961646/257462747620886
    dependencies = [
        {
            'source': 3,
            'target': 5,
            'type': 'set_radio',
            'additional': {
                'options': ['Aripiprazole-oral', 'Aripiprazole-LAI'],
                'anwser': 'Yes'
            }
        },
        {
            'source': 11,
            'target': 13,
            'type': 'set_radio',
            'additional': {
                'options': ['Aripiprazole-oral', 'Aripiprazole-LAI'],
                'anwser': 'Yes'
            }
        }
    ]

    def __init__(self, survey):
        self.survey = survey
        self.survey_stat = {}
        self.organization_stat = {}
        self.question_stat = {}
        self.question_representation_link = {}
        self.question_dict = {}
        self.messages = []
        self.load_stat()

    def type_average_percent_processor(self, question_id, question_data, answer):
        q = self.question_dict[question_id]
        if (q.type != Question.TYPE_TWO_DEPENDEND_FIELDS and
                (q.type != Question.TYPE_SIMPLE_INPUT or
                 q.field not in (Question.FIELD_PERCENT, Question.FIELD_NUMBER))):
            raise ValueError("type_average_percent_processor doesn't process %s, Question: %s" % (q.type, q.pk))

        main_str = question_data['main'].strip() if 'main' in question_data else ''
        additional_str = question_data['additional'].strip() if 'additional' in question_data else ''
        if not main_str and not additional_str:
            return

        if main_str:
            main_float = float(main_str)
            val_str = main_str
        elif additional_str:
            main_float = float(additional_str) * 10
            val_str = str(int(additional_str) * 10)
        org_key = str(answer.organization_id)
        reg_id = answer.region_id
        country_id = answer.country_id
        survey_id = answer.survey_id

        r = self.question_representation_link[question_id]

        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)
        regs = [(k0, country_id), (k1, reg_id)]

        for k, cur_reg_id in regs:
            reg_key = str(cur_reg_id)
            data = self.question_stat[k].data
            if not data:
                data.update({
                    'main_sum': 0.0,
                    'main_cnt': 0,
                    'dist': {},
                    'reg_sum': {},
                    'reg_cnt': {},
                    'org_sum': {},
                    'org_cnt': {}
                })

            data = self.question_stat[k].data
            data['main_sum'] += main_float
            data['main_cnt'] += 1

            if val_str in data['dist']:
                data['dist'][val_str] += 1
            else:
                data['dist'][val_str] = 1

            if reg_key in data['reg_sum']:
                data['reg_sum'][reg_key] += main_float
                data['reg_cnt'][reg_key] += 1
            else:
                data['reg_sum'][reg_key] = main_float
                data['reg_cnt'][reg_key] = 1

            if org_key in data['org_sum']:
                data['org_sum'][org_key] += main_float
                data['org_cnt'][org_key] += 1
            else:
                data['org_sum'][org_key] = main_float
                data['org_cnt'][org_key] = 1

    def type_yes_no_processor(self, question_id, question_data, answer):
        q = self.question_dict[question_id]
        if q.type != Question.TYPE_YES_NO and q.type != Question.TYPE_YES_NO_JUMPING:
            raise ValueError("type_yes_no_processor doesn't process %s. Question: %s" % (q.type, q.pk))

        result = question_data.strip()

        if result == 'Yes':
            yes = 1
        elif result == 'No':
            yes = 0
        else:
            return

        org_key = str(answer.organization_id)
        reg_id = answer.region_id
        country_id = answer.country_id
        survey_id = answer.survey_id

        r = self.question_representation_link[question_id]

        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)
        regs = [(k0, country_id), (k1, reg_id)]

        for k, cur_reg_id in regs:
            reg_key = str(cur_reg_id)
            data = self.question_stat[k].data
            if not data:
                data.update({
                    'main_yes': 0,
                    'main_cnt': 0,
                    'reg_yes': {},
                    'reg_cnt': {},
                    'org_yes': {},
                    'org_cnt': {}
                })

            data = self.question_stat[k].data
            data['main_yes'] += yes
            data['main_cnt'] += 1
            if reg_key in data['reg_yes']:
                data['reg_yes'][reg_key] += yes
                data['reg_cnt'][reg_key] += 1
            else:
                data['reg_yes'][reg_key] = yes
                data['reg_cnt'][reg_key] = 1

            if org_key in data['org_yes']:
                data['org_yes'][org_key] += yes
                data['org_cnt'][org_key] += 1
            else:
                data['org_yes'][org_key] = yes
                data['org_cnt'][org_key] = 1

    def type_multiselect_top_processor(self, question_id, question_data, answer):
        q = self.question_dict[question_id]
        if q.type != Question.TYPE_MULTISELECT_ORDERED:
            raise ValueError("type_multiselect_top_processor doesn't process %s. Question: %s" % (q.type, q.pk))

        if not question_data or '' not in question_data:
            return

        options = question_data['']
        if not options:
            return
        if isinstance(options, str):
            options = [options]

        top3 = []

        for i, opt in enumerate(options):
            opt = opt.strip()
            if not opt:
                continue

            lower = opt.lower()
            OptionDict.register(lower, opt)

            if not i:
                top1 = lower

            if lower not in top3:
                top3.append(lower)
            if len(top3) == 3:
                break

        r = self.question_representation_link[question_id]
        org_key = str(answer.organization_id)
        country_id = answer.country_id
        survey_id = answer.survey_id
        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)

        for k in [k0, k1]:
            data = self.question_stat[k].data
            if not data:
                data.update({
                    'cnt': 0,
                    'top1': {},
                    'top3': {},
                    'org': {},
                })

            data['cnt'] += 1

            if org_key not in data['org']:
                data['org'][org_key] = {
                    'cnt': 0,
                    'top1': {},
                    'top3': {},
                }

            data['org'][org_key]['cnt'] += 1

            if top1 in data['top1']:
                data['top1'][top1] += 1
            else:
                data['top1'][top1] = 1

            if top1 in data['org'][org_key]['top1']:
                data['org'][org_key]['top1'][top1] += 1
            else:
                data['org'][org_key]['top1'][top1] = 1

            for top_i in top3:
                if top_i in data['top3']:
                    data['top3'][top_i] += 1
                else:
                    data['top3'][top_i] = 1

                if top_i in data['org'][org_key]['top3']:
                    data['org'][org_key]['top3'][top_i] += 1
                else:
                    data['org'][org_key]['top3'][top_i] = 1

    def type_multiselect_processor(self, question_id, question_data, answer):
        q = self.question_dict[question_id]
        if q.type != Question.TYPE_MULTISELECT_WITH_OTHER:
            raise ValueError("type_multiselect_processor doesn't process %s. Question: %s" % (q.type, q.pk))

        if not question_data or '' not in question_data:
            return

        options = question_data['']
        if not options:
            return
        if isinstance(options, str):
            options = [options]

        top = []

        for i, opt in enumerate(options):
            opt = opt.strip()
            if not opt:
                continue

            lower = opt.lower()
            OptionDict.register(lower, opt)

            if lower not in top:
                top.append(lower)

        r = self.question_representation_link[question_id]
        org_key = str(answer.organization_id)
        country_id = answer.country_id
        survey_id = answer.survey_id
        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)

        for k in [k0, k1]:
            data = self.question_stat[k].data
            if not data:
                data.update({
                    'cnt': 0,
                    'top': {},
                    'org': {},
                })

            data['cnt'] += 1

            if org_key not in data['org']:
                data['org'][org_key] = {
                    'cnt': 0,
                    'top': {},
                }

            data['org'][org_key]['cnt'] += 1

            for top_i in top:
                if top_i in data['top']:
                    data['top'][top_i] += 1
                else:
                    data['top'][top_i] = 1

                if top_i in data['org'][org_key]['top']:
                    data['org'][org_key]['top'][top_i] += 1
                else:
                    data['org'][org_key]['top'][top_i] = 1

    def type_multiselect_top5_processor(self, question_id, question_data, answer):
        q = self.question_dict[question_id]
        if q.type != Question.TYPE_MULTISELECT_ORDERED:
            raise ValueError("type_multiselect_top5_processor doesn't process %s. Question: %s" % (q.type, q.pk))

        if not question_data or '' not in question_data:
            return

        options = question_data['']
        if not options:
            return
        if isinstance(options, str):
            options = [options]

        top5 = []

        for i, opt in enumerate(options):
            opt = opt.strip()
            if not opt:
                continue

            lower = opt.lower()
            OptionDict.register(lower, opt)

            if lower not in top5:
                top5.append(lower)
            if len(top5) == 5:
                break

        r = self.question_representation_link[question_id]
        org_key = str(answer.organization_id)
        country_id = answer.country_id
        survey_id = answer.survey_id
        k0 = (survey_id, None, r.pk)
        k1 = (survey_id, country_id, r.pk)

        for k in [k0, k1]:
            data = self.question_stat[k].data
            if not data:
                data.update({
                    'cnt': 0,
                    'top5': {},
                    'org': {},
                })

            data['cnt'] += 1

            if org_key not in data['org']:
                data['org'][org_key] = {
                    'cnt': 0,
                    'top5': {},
                }

            data['org'][org_key]['cnt'] += 1

            for top_i in top5:
                if top_i in data['top5']:
                    data['top5'][top_i] += 1
                else:
                    data['top5'][top_i] = 1

                if top_i in data['org'][org_key]['top5']:
                    data['org'][org_key]['top5'][top_i] += 1
                else:
                    data['org'][org_key]['top5'][top_i] = 1

    def get_answers(self):
        raise NotImplementedError

    def load_stat(self):
        surveys = SurveyStat.objects.all()
        for survey in surveys:
            self.survey_stat[(survey.survey_id, survey.country_id)] = survey

        orgs = OrganizationStat.objects.all()
        for org in orgs:
            self.organization_stat[(org.survey_id, org.country_id, org.organization_id)] = org

        quests = (QuestionStat.objects
            .select_related('representation', 'representation__question', 'country', 'survey')
            .prefetch_related('survey__organizations')
            .all())
        for quest in quests:
            self.question_stat[(quest.survey_id, quest.country_id, quest.representation_id)] = quest

    def fill_out(self):
        countries = list(self.survey.countries.all())
        countries.append(None)
        representations = list(Representation.objects.filter(question__survey_id=self.survey.pk).
                               select_related('question').filter(active=True))

        for country in countries:
            # Fill out survey stat
            if country is None:
                country_id = country
            else:
                country_id = country.pk
            surv_key = (self.survey.pk, country_id)

            if surv_key not in self.survey_stat:
                self.survey_stat[surv_key] = SurveyStat(survey=self.survey, country=country)

            # Fill out organizations stat
            for org in self.survey.organizations.all():
                org_key = (self.survey.pk, country_id, org.pk)
                if org_key not in self.organization_stat:
                    self.organization_stat[org_key] = OrganizationStat(
                        survey=self.survey, country=country, organization=org, ordering=org.ordering)
                else:
                    if self.organization_stat[org_key].ordering != org.ordering:
                        self.organization_stat[org_key].ordering = org.ordering

            # Fill out question stat
            for repr in representations:
                q_key = (self.survey.pk, country_id, repr.pk)
                if q_key not in self.question_stat:
                    self.question_stat[q_key] = QuestionStat(
                        survey=self.survey, country=country, representation=repr,
                        ordering=repr.ordering, type=repr.type)
                else:
                    if self.question_stat[q_key].ordering != repr.ordering:
                        self.question_stat[q_key].ordering = repr.ordering

                # Fill out question representation links
                if hasattr(repr, 'question'):
                    self.question_representation_link[repr.question.pk] = repr
                    if repr.question.pk not in self.question_dict:
                        self.question_dict[repr.question.pk] = repr.question

    def update_survey_stat(self, surv_key, answer):
        survey_id, country_id = surv_key
        if surv_key not in self.survey_stat:
            self.survey_stat[surv_key] = SurveyStat(survey_id=survey_id, country_id=country_id, last=answer.created_at)
        self.survey_stat[surv_key].total += 1
        if self.survey_stat[surv_key].last:
            self.survey_stat[surv_key].last = max(self.survey_stat[surv_key].last, answer.created_at)
        else:
            self.survey_stat[surv_key].last = answer.created_at

        surv_key_all = (survey_id, None)
        if surv_key_all not in self.survey_stat:
            self.survey_stat[surv_key_all] = SurveyStat(survey_id=survey_id, country_id=None)
        self.survey_stat[surv_key_all].total += 1
        if self.survey_stat[surv_key_all].last:
            self.survey_stat[surv_key_all].last = max(self.survey_stat[surv_key_all].last, answer.created_at)
        else:
            self.survey_stat[surv_key_all].last = answer.created_at

    def update_organization_stat(self, org_key):
        survey_id, country_id, organization_id = org_key
        if org_key not in self.organization_stat:
            self.organization_stat[org_key] = OrganizationStat(
                survey_id=survey_id, country_id=country_id, organization_id=organization_id)
        self.organization_stat[org_key].total += 1

        org_key_all = (survey_id, None, organization_id)
        if org_key_all not in self.organization_stat:
            self.organization_stat[org_key_all] = OrganizationStat(
                survey_id=survey_id, country_id=None, organization_id=organization_id)
        self.organization_stat[org_key_all].total += 1

    @staticmethod
    def parse_query_string(string):
        return queryparser.parse(string)

    def process_dependencies(self, data):
        if not isinstance(self.dependencies, list):
            return

        if not isinstance(data, dict):
            return

        def list_lower(data):
            return [x.lower() for x in data]

        for dependency in self.dependencies:
            if dependency['type'] == 'set_radio':
                if not dependency['source'] in data:
                    continue
                if '' not in data[dependency['source']]:
                    continue
                options_set = set(list_lower(dependency['additional']['options']))
                data_set = set(list_lower(data[dependency['source']]['']))
                if options_set & data_set:
                    data[dependency['target']] = dependency['additional']['anwser']

    def process_answer(self, answer):
        if not answer.body:
            return

        results = self.parse_query_string(answer.body)
        if 'data' not in results:
            raise KeyError("There is no data in post results. Answer: %s" % answer.pk)

        data = results['data']

        self.process_dependencies(data)

        if type(data) != dict:
            raise KeyError("Answer data should be dict. Answer: %s" % answer.pk)

        survey_id = answer.survey_id
        country_id = answer.country_id
        organization_id = answer.organization_id

        surv_key = (survey_id, country_id)
        self.update_survey_stat(surv_key, answer)

        org_key = (survey_id, country_id, organization_id)
        self.update_organization_stat(org_key)

        for qid, question_data in data.items():
            if qid not in self.question_dict:
                logger.warning("Question %s is not expected" % qid)
                continue
            if qid not in self.question_representation_link:
                logger.warning("Question %s is not connected to any of representations" % qid)
                continue
            repr = self.question_representation_link[qid]
            processor = "%s_processor" % repr.type
            getattr(self, processor)(qid, question_data, answer)

        answer.is_updated = True
        answer.save(update_fields=['is_updated'])

    def save(self):
        for surv_stat in self.survey_stat.values():
            surv_stat.save()
        for org_stat in self.organization_stat.values():
            org_stat.save()
        for quest_stat in self.question_stat.values():
            quest_stat.update_vars()
            quest_stat.save()

    @classmethod
    @transaction.atomic
    def process_answers(cls, survey):
        evaluator = cls(survey)
        evaluator.fill_out()
        answers = evaluator.get_answers()
        for answer in answers:
            try:
                evaluator.process_answer(answer)
            except Exception as e:
                evaluator.messages.append(str(e))
                logger.warning("Answer can't be processed. Exception: %s" % e)

        evaluator.save()
        return evaluator


class TotalEvaluator(AbstractEvaluator):
    def __init__(self, survey):
        survey.clear_stats()

        super().__init__(survey)

    def get_answers(self):
        return self.survey.answers.all()


class LastEvaluator(AbstractEvaluator):
    def get_answers(self):
        return self.survey.answers.filter(is_updated=False)
