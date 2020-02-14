/*
 * Copyright (c) Small Brain Records 2014-2020. Kevin Perdue, James Ryan with contributors Timothy Clemens and Dinh Ngoc Anh
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>
 */
(function () {

    'use strict';

    angular.module('app.filters').filter('age', function () {
            return function (input, current) {
                // This syntax is usable in this case
                // NaN || {whatever} evaluates to {whatever}
                current = Date.parse(current) || Date.now();

                // Difference in milliseconds
                var ageDiffMs = current - new Date(input).getTime();
                var ageDate = new Date(ageDiffMs);

                return Math.abs(ageDate.getUTCFullYear() - 1970);
            }
        });
})();