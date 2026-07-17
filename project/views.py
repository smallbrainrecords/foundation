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
from django.http import JsonResponse


def home(request):
    # Track B1 (2026-07-17): the legacy AngularJS web front end is retired —
    # the root no longer renders `index.html` (an EOL bundle carrying 168
    # open Dependabot advisories, served unauthenticated for zero product
    # benefit) and no longer redirects authenticated users into the legacy
    # web app. The mobile app is the only client (owner policy, recorded
    # 2026-07-09); Django exists to serve the mobile API. Track B2 removes
    # the legacy routes and the static bundle itself — EXCEPT `^my_story/`,
    # which the mobile app still calls (`/my_story/<pid>/get_my_story`).
    return JsonResponse({'service': 'smallbrain-api', 'status': 'ok'})
