**Run mysql server using docker enviroment**

`docker run  -d -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -v D:\Workspace\database\smallbrain:/var/lib/mysql mysql:5.7.22 --sql_mode=""`

**NOTE for updating to Django 1.11 and other dependencies(django-reversion):**
1. Run `python manage.py migrate reversion --fake`
2. Add column `db VARCHAR(191)` to table `reversion_version` 

** TEST COVERAGE **
1. project
2. users_app
3. common
4. emr
5. generic
6. problems_app
7. todo_app
8. data_app
9. a1c_app
10. colons_app
11. goals_app
12. document_app
13. encounters_app
14. inr_app
15. medication_app
16. pain
17. my_story_app
18. project_admin_app
19. site_pages_app