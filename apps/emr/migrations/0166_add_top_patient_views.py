# -*- coding: utf-8 -*-

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

from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('emr', '0165_auto_20190212_0228'),
    ]
    sql_query = "select `auth_user`.`id` AS `id`,`auth_user`.`username` AS `username`,concat(`auth_user`.`first_name`,' ',`auth_user`.`last_name`) AS `name`,`emr_userprofile`.`id` AS `user_profile_id`,(select count(0) from `emr_problem` where ((`emr_problem`.`patient_id` = `auth_user`.`id`) and (`emr_problem`.`is_active` = TRUE) and (`emr_problem`.`is_controlled` = FALSE))) AS `problem_count`,(select count(0) from `emr_todo` where ((`emr_todo`.`patient_id` = `auth_user`.`id`) and (`emr_todo`.`accomplished` = FALSE))) AS `todo_count`,(select count(0) from `emr_encounter` where ((`emr_encounter`.`patient_id` = `emr_userprofile`.`id`) and (`emr_encounter`.`starttime` >= (curdate() - interval 6 week)))) AS `encounter_count`,(select count(0) from `emr_document` where ((`emr_document`.`patient_id` = `auth_user`.`id`) and (`emr_document`.`created_on` >= (curdate() - interval 6 week)))) AS `document_count` from (`auth_user` left join `emr_userprofile` on((`auth_user`.`id` = `emr_userprofile`.`user_id`))) where (`emr_userprofile`.`role` = 'patient')";
    operations = [migrations.RunSQL(sql_query)]
