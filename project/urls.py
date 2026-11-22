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

from django.conf.urls import include
from django.contrib.auth.decorators import login_required
from django.urls import re_path

from apps.mobile_api import urls as mobile_api_urls
from apps.mobile_api.views import requires_patient_access
from apps.my_story_app.views import get_my_story
from project.views import home, signed_out

# The app is the only client. This is the whole list of what the server
# answers: the retired web application's routes are not mounted, and must not
# be mounted again (`project.tests.test_routes` pins the list). A new route
# belongs in `apps.mobile_api.urls`, behind that module's checks.
urlpatterns = [
    re_path(r"^$", home, name="project_home"),
    re_path(r"^api/", include(mobile_api_urls)),
    # LOGIN_URL: where `login_required` sends a signed-out request. It must
    # answer 401. A 404 here reads to older app builds as "that record is
    # gone", and they drop the edit they were sending.
    re_path(r"^u/login/?$", signed_out),
    # The one route of the old web app that the mobile app still calls.
    re_path(
        r"^my_story/(?P<patient_id>\d+)/get_my_story$",
        login_required(requires_patient_access(get_my_story)),
    ),
    # SessionSecurityMiddleware reverses this name on signed-in requests;
    # without it every such request is a 500.
    re_path(r"^session_security/", include("session_security.urls")),
]
