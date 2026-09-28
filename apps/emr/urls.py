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

# Nothing includes this module: project/urls.py never loads apps/emr/urls.py,
# so a route added here is unreachable (it 404s). Mobile API routes belong in
# apps/mobile_api/urls.py. The last route here, api/snomed/validate/, 404'd on
# every call from 2026-05 until it was removed on 2026-09-28; the app now runs
# that broader/narrower SNOMED check locally.

urlpatterns = []
