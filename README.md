# Foundation: Getting Started

## Project setup

Setup instructions to run the project locally using docker compose.

### Requirements:

- Docker and Docker-compose.

### Start containers:
- `$ sudo docker-compose up -d`

### Run migrations:
- `$ sudo docker-compose run --rm web python manage.py migrate`

### Create admin user:

- Open an interactive bash session in db container with: 
    - `$ sudo docker exec -it foundation_db_1 bash`
- Login into mysql with:
    - `# mysql -u root -p` (password root)
- Once your are logged in, select the 'smallbrains_dev' database:
    -  `mysql> use smallbrains_dev;`
- Finally run these SQL queries:

 
    ```sql
    INSERT INTO auth_user (username, first_name, last_name, email, password, is_staff, is_active, is_superuser, date_joined) 
    VALUES ('admin', 'admin@mail.com', 'FN', 'LN', 'pbkdf2_sha256$36000$6WP07jyMdViC$s4Q+E536lNSaS1pJIpu0oo/6MoyfqbHDB3zipaC+XaM=', 0, 1, 1, now());
    ```
    ```sql
    SELECT * FROM auth_user WHERE username = 'admin';
    ```
    ```sql
    -- Change {user_id} for the result id of the query above
    INSERT INTO emr_userprofile (role, user_id, data,cover_image, portrait_image, summary, sex, phone_number,
    inr_target, insurance_medicare, insurance_note, height_changed_first_time) 
    VALUES ('admin', {user_id}, '', '', '', '', 'male', '', 0, 0, '', 0);
    ```
    Your username is `admin` and password `abc12345`.


### Stop containers:

- `$ sudo docker-compose down`

## Run tests

The test are using `LiveServerTestCase` from django.test and `Selenium`.

Use `$ python manage.py test test` to run test.

# Test coverage

Run following commands to generate a coverage report.

- `$ coverage run --source='.' --omit 'venv./*' manage.py test test`

- `$ coverage report > coverage_report`

---

## Admin functions

### Manage users

- Add user
- Edit user
- Deactivate user

## Patient Administration
