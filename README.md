# Foundation: Getting Started

### Database Setup
To set up MySQL server using docker environment run:
```sql
docker run -d --name mysql -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -v /local/db/path:/var/lib/mysql mysql:5.7.22 --sql_mode=""
```
where `/local/db/path` directory is where you want to persist the database locally.

### Admin user
Connect to you local database `test` and insert these records:
```sql
INSERT INTO auth_user (username, first_name, last_name, email, password, is_staff, is_active) 
VALUES ('admin', 'admin@mail.com', 'FN', 'LN', 'pbkdf2_sha256$36000$6WP07jyMdViC$s4Q+E536lNSaS1pJIpu0oo/6MoyfqbHDB3zipaC+XaM=', 0, 1);
SELECT * FROM auth_user WHERE username = 'admin';
-- Change \#\# for the result id of the query above
INSERT INTO emr_userprofile (role, user_id) VALUES ('admin', \#\#);
```
Your password for that admin user is `abc12345`.

**NOTE for updating to Django 1.11 and other dependencies(django-reversion):**
1. Run `python manage.py migrate reversion --fake`
2. Add column `db VARCHAR(191)` to table `reversion_version` 

### Create a virtualenv to your project

```bash
virtualenv .env
```

This command will create a new directory `.env/`

To enable the virtualenv run `source .env/bin/activate`

### Install Requirements

Install all the required requirements on our local virtualenv running:

```bash
pip install -r requirements.txt
```

**Note:** if it fails you\'ll probably need to install _pathlib_ running `pip install pathlib`

### Run Migrations

```bash
python manage.py migrate
```

### Install node packages

On the `static/` directory run

```bash
npm install
```

### Start the local sever

```bash
python manage.py runserver
```

## Test Coverage

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

## Admin functions

### Manage users

- Add user
- Edit user
- Deactivate user

## Patient Administration


## Run tests

The test are using `LiveServerTestCase` from django.test and `Selenium`.

Use `python manage.py test test` to run test.

# Test coverage

Run following commands to generate a coverage report.

`coverage run --source='.' manage.py test test`
`coverage report`

