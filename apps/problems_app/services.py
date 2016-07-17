from datetime import datetime, timedelta

from emr.models import Goal, ToDo, TextNote, PatientImage

class ProblemService(object):
    @staticmethod
    def populate_multiplicity(problems_json):
        for problem in problems_json:
            todo = ToDo.objects.filter(problem_id=problem['id'], accomplished=False).count()
            event = ProblemActivity.objects.filter(problem_id=problem['id'], created_on__gte=datetime.now()-timedelta(days=30)).count()
            if todo == 0 and event == 0:
                problem['multiply'] = 0
            elif todo == 0 or event == 0:
                problem['multiply'] = 1
            else:
                problem['multiply'] = todo * event

    @staticmethod
    def update_from_timeline_data(problem_json):
        problem = Problem.objects.get(id=int(problem_json['id']))
        start_date = datetime.strptime(problem_json['events'][-1]['startTime'], "%d/%m/%Y %H:%M:%S")
        problem.start_date = start_date.date()
        problem.start_time = start_date.time()
        problem.save()

        if len(problem_json['events']) > 1:
            # break if the last one, this is current problem
            for event in problem_json['events'][:-1]:
                try:
                    event_id = int(event['event_id'])
                    try:
                        problem_segment = ProblemSegment.objects.get(event_id=event_id)
                    except ProblemSegment.DoesNotExist:
                        problem_segment = ProblemSegment()
                        problem_segment.event_id = event_id
                        problem_segment.problem = problem

                    start_date = datetime.strptime(event['startTime'], "%d/%m/%Y %H:%M:%S")
                    problem_segment.start_date = start_date.date()
                    problem_segment.start_time = start_date.time()
                    problem_segment.is_active = event["state"] != "inactive"
                    problem_segment.is_controlled = event["state"] == "controlled"
                    problem_segment.save()
                except ValueError:
                    event_id = None
        return problem
