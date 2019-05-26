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

from django.test import RequestFactory

from common.views import ajax_response, get_date


class TestCommonView(TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def test_ajax_response(self):
        response = ajax_response({})
        self.assertEqual(response.status_code, 200)

    def test_get_date_supported_format(self):
        """
        Correct datetime string format
        :return:
        """
        date = get_date('2019-12-23')
        self.assertEqual(date.year, 2019)

    def test_get_date_unsupported_format(self):
        response = get_date('2019-23-12')
        self.assertEqual(response, "Unsupported format")


    def tearDown(self):
        pass
