# Bincom Django Test (Delta 2011 dummy results)

This is my solution to the Bincom preliminary test. I used Django and the MySQL dump they sent (`bincom_test.sql`).

Live version: https://bincomtest.pythonanywhere.com/ (PythonAnywhere, username `bincomtest`)

The data is dummy 2011 election results for Delta State. Polling units sit under wards, wards sit under LGAs. Party scores are stored per polling unit, not as one row per unit.

## How I approached it

First I imported the SQL dump into MySQL and looked at the tables. The ones that actually matter for the questions are `polling_unit`, `announced_pu_results`, `lga`, `ward` and `party`.

I did not recreate those tables from Django. They already exist, so I mapped models onto them using:

```
python manage.py inspectdb polling_unit announced_pu_results lga ward party announced_lga_results
```

I copied that into `bincom_test/models.py`, left `managed = False` so Django would not try to rebuild the tables, and just read/write through the ORM.

One thing that is easy to get wrong: results are tied to `polling_unit.uniqueid`, not `polling_unit_id`. The brief even flags this. Also, `polling_unit.lga_id` matches `lga.lga_id`, not `lga.uniqueid`.

### Question 1 – results for one polling unit

A page with a dropdown of polling units. When you pick one, I load rows from `announced_pu_results` where `polling_unit_uniqueid` is that unit's `uniqueid`.

A lot of units in the dump have no scores. That is just how the dummy data is. Unit 8 is a good one to try (PDP 802, DPP 719, etc.).

### Question 2 – summed results for an LGA

Dropdown of LGAs. I find every polling unit in that LGA, then sum `announced_pu_results` by party.

I did not use `announced_lga_results`. The question says that table is for comparing later, not for building this total.

If an LGA has units but none of them have PU results, the page says so. Aniocha-South is like that. Sapele has data because unit 8 belongs there.

### Question 3 – save results for a new polling unit

Form to pick LGA and ward, name the new unit, and enter a score for every party. On submit I insert the polling unit, then one `announced_pu_results` row per party, using the new `uniqueid`.

Party abbreviation in the results table is only 4 characters, so LABOUR is stored as LABO (same as the original dump).

After saving, it takes you to Question 1 for that new unit so you can see it worked. If you then open Question 2 for the same LGA, the new scores should be in the total.

## Setup

You need Python, MySQL, and the dump file.

1. Create a MySQL database (I called mine `bincomdjangotest`) and import `bincom_test.sql` into it.

2. Create a virtualenv and install packages:

```
python -m venv virtual
virtual\Scripts\activate
pip install -r requirements.txt
```

On Mac/Linux, activate with `source virtual/bin/activate`.

3. Create a `.env` file in the project root (it is not committed). You need at least:

```
SECRET_KEY=anything-random
DB_PASSWORD=your-mysql-password
```

Database name, user and host are in `project/settings.py`. Change them if yours are different.

4. Run:

```
python manage.py migrate
python manage.py runserver
```

Migrate only creates Django's own tables (users, sessions, etc.). It should not rebuild the election tables.

Open http://127.0.0.1:8000/

- `/polling-unit/` – Question 1
- `/lga/` – Question 2
- `/new-result/` – Question 3

## Note

I am on Django 6, which wanted MySQL 8.4. If `manage.py check` complains about the MySQL version, either upgrade MySQL or use Django 5.2 with MySQL 8.0.
