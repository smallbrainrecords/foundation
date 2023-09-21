"""
Copyright (c) Small Brain Records 2014-2018 Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
"""
from datetime import datetime, timedelta

from common.views import timeit
from emr.models import Problem, ProblemActivity, ProblemSegment, ToDo


class ProblemService(object):
    @staticmethod
    #@timeit
    def populate_multiplicity(problems_json):
        for problem in problems_json:
            todo = ToDo.objects.filter(problem_id=problem['id'], accomplished=False).count()
            event = ProblemActivity.objects.filter(problem_id=problem['id'],
                                                   created_on__gte=datetime.now() - timedelta(days=30)).count()
            if todo == 0 and event == 0:
                problem['multiply'] = 0
            elif todo == 0 or event == 0:
                problem['multiply'] = 1
            else:
                problem['multiply'] = todo * event

    @staticmethod
    #@timeit
    def update_from_timeline_data(problem_json):
        problem = Problem.objects.get(id=int(problem_json['id']))
        start_date = datetime.strptime(problem_json['events'][0]['startTime'], "%d/%m/%Y %H:%M:%S")
        problem.start_date = start_date.date()
        problem.start_time = start_date.time()
        problem.save()

        if len(problem_json['events']) > 1:
            # start time of the next one is for the current one,
            # first loop item, start time is problem
            # other side, state of last loop item is problem
            i = 0
            for event in problem_json['events']:
                if not i == len(problem_json['events']) - 1:
                    try:
                        event_id = int(event['event_id'])
                        try:
                            problem_segment = ProblemSegment.objects.get(event_id=event_id)
                        except ProblemSegment.DoesNotExist:
                            problem_segment = ProblemSegment()
                            problem_segment.event_id = event_id
                            problem_segment.problem = problem

                        start_date = datetime.strptime(problem_json['events'][i + 1]['startTime'], "%d/%m/%Y %H:%M:%S")
                        problem_segment.start_date = start_date.date()
                        problem_segment.start_time = start_date.time()
                        problem_segment.is_active = event["state"] != "inactive"
                        problem_segment.is_controlled = event["state"] == "controlled"
                        problem_segment.save()
                    except ValueError:
                        event_id = None

                i += 1

        return problem
