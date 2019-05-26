#  Copyright (c) Small Brain Records 2014-2019. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>
from unittest import TestCase

from django.contrib.auth.models import User, AnonymousUser
from django.test import RequestFactory
from django.urls import reverse

from project.views import home


class TestProjectView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='jacob', email='doctor@smallbrainrecords', password='top_secret')

    def test_home_anonymous(self):
        """

        :return:
        """
        url = reverse('project_home')
        request = self.factory.get(url)
        request.user = AnonymousUser()
        response = home(request)

        self.assertEqual(response.status_code, 200)

    def test_home_authenticated_user(self):
        """

        :return:
        """
        url = reverse('project_home')
        request = self.factory.get(url)
        request.user = self.user
        response = home(request)

        self.assertEqual(response.status_code, 302)

    def tearDown(self):
        User.objects.get(username='jacob').delete()
