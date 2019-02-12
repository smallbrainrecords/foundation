**Run mysql server using docker enviroment**

`docker run  -d -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -v D:\Workspace\database\smallbrain:/var/lib/mysql mysql:5.7.22 --sql_mode=""`

**NOTE for updating to Django 1.11 and other dependencies(django-reversion):**
1. Run `python manage.py migrate reversion --fake`
2. Add column `db VARCHAR(191)` to table `reversion_version` 
