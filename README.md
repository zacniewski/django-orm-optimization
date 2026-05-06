### django-orm-optimization

> Helper project for analyzing optimization in Django (based on the [article](https://www.devs-mentoring.pl/optymalizacja-w-django/) from devs-mentoring.pl).

## Setup Instructions

### 1. Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Create a Django project and app (for reference)

If you were starting from scratch, you would use:

```bash
django-admin startproject core .
python manage.py startapp university
```

*Note: These are already created in this repository.*

### 4. Database migrations

```bash
python manage.py migrate
```

______________________________________________________________________

## Data Generation and Loading

### 1. Generate data

To generate a file with 100 mentors and 100,000 students, run:

```bash
python generate_data.py
```

This will create a `data.json` file (around 27 MB).

### 2. Load data into the database

To insert the generated data into your database, use the Django `loaddata` command:

```bash
python manage.py loaddata data.json
```

______________________________________________________________________

## Useful Commands

- Run the development server: `python manage.py runserver`
- Create a superuser: `python manage.py createsuperuser`
- Open Django shell: `python manage.py shell`
- Open Django shell with `shell_plus` (auto-imports models and prints SQL executed under the hood): `python manage.py shell_plus --print-sql`

______________________________________________________________________

## Experiments

> All experiments will be done in the Django shell.

1. Starting shell_plus

```shell
python manage.py shell_plus --print-sql
# Shell Plus Model Imports
from django.contrib.admin.models import LogEntry
from django.contrib.auth.models import Group, Permission, User
from django.contrib.contenttypes.models import ContentType
from django.contrib.sessions.models import Session
from university.models import Mentor, Student
# Shell Plus Django Imports
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When
from django.utils import timezone
from django.urls import reverse
from django.db.models import Exists, OuterRef, Subquery
Python 3.12.3 (main, Mar 23 2026, 19:04:32) [GCC 13.3.0] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
```

1. Getting information about the Mentor model for the first time

```shell
>>> Mentor.objects.count()
SELECT COUNT(*) AS "__count"
  FROM "university_mentor"
Execution time: 0.000271s [Database: default]
100

>>> Mentor.objects.all()
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 LIMIT 21
Execution time: 0.000833s [Database: default]
<QuerySet [<Mentor: Mentor 1>, <Mentor: Mentor 2>, <Mentor: Mentor 3>, <Mentor: Mentor 4>, <Mentor: Mentor 5>, <Mentor: Mentor 6>, <Mentor: Mentor 7>, <Mentor: Mentor 8>, <Mentor: Mentor 9>, <Mentor: Mentor 10>, <Mentor: Mentor 11>, <Mentor: Mentor 12>, <Mentor: Mentor 13>, <Mentor: Mentor 14>, <Mentor: Mentor 15>, <Mentor: Mentor 16>, <Mentor: Mentor 17>, <Mentor: Mentor 18>, <Mentor: Mentor 19>, <Mentor: Mentor 20>, '...(remaining elements truncated)...']>
```

1. Built-in cache mechanism

> Look at the time of the second execution of the above command.

```shell
>>> Mentor.objects.all()
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 LIMIT 21
Execution time: 0.000168s [Database: default]
```

It's almost 5 x faster than the first execution!

1. Updating given fields

```shell
>>> mentor = Mentor.objects.get(id=1)
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 WHERE "university_mentor"."id" = 1
 LIMIT 21
Execution time: 0.000162s [Database: default]
>>> mentor.name = "New Name"
>>> mentor.save()
UPDATE "university_mentor"
   SET "name" = 'New Name',
       "specialization" = 'Frontend'
 WHERE "university_mentor"."id" = 1
Execution time: 0.007082s [Database: default]
```

Looking at the code, we can see that also `specialization` field was updated.
We didn't ask for that. There is a way to avoid that (using `update_fields` parameter):

```shell
>>> mentor.save(update_fields=['name'])
UPDATE "university_mentor"
   SET "name" = 'New Name'
 WHERE "university_mentor"."id" = 1
Execution time: 0.000343s [Database: default]
```

- we can also use the `update()` method (must be used with `filter()` method, not `get()`):

```shell
>>> Mentor.objects.filter(id=1).update(name="New Name")
UPDATE "university_mentor"
   SET "name" = 'New Name'
 WHERE "university_mentor"."id" = 1
Execution time: 0.000167s [Database: default]
1
```

1. Lazy loading
   The idea is to load data when we need it:

```shell
>>> mentors = Mentor.objects.all()
>>> print(mentors)
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 LIMIT 21
Execution time: 0.000113s [Database: default]
<QuerySet [<Mentor: New Name>, <Mentor: Mentor 2>, <Mentor: Mentor 3>, <Mentor: Mentor 4>, <Mentor: Mentor 5>, <Mentor: Mentor 6>, <Mentor: Mentor 7>, <Mentor: Mentor 8>, <Mentor: Mentor 9>, <Mentor: Mentor 10>, <Mentor: Mentor 11>, <Mentor: Mentor 12>, <Mentor: Mentor 13>, <Mentor: Mentor 14>, <Mentor: Mentor 15>, <Mentor: Mentor 16>, <Mentor: Mentor 17>, <Mentor: Mentor 18>, <Mentor: Mentor 19>, <Mentor: Mentor 20>, '...(remaining elements truncated)...']>
```

1. N+1 problem
   Let's check how many queries are executed when we fetch the first 5 students and then print their mentors:

```shell
>>> students = Student.objects.all()[:5]
>>> for student in students:
...     student.mentor.name
...
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 LIMIT 5
Execution time: 0.006812s [Database: default]
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 WHERE "university_mentor"."id" = 92
 LIMIT 21
Execution time: 0.000104s [Database: default]
'Mentor 92'
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 WHERE "university_mentor"."id" = 49
 LIMIT 21
Execution time: 0.000103s [Database: default]
'Mentor 49'
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 WHERE "university_mentor"."id" = 40
 LIMIT 21
Execution time: 0.000146s [Database: default]
'Mentor 40'
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 WHERE "university_mentor"."id" = 10
 LIMIT 21
Execution time: 0.000113s [Database: default]
'Mentor 10'
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 WHERE "university_mentor"."id" = 5
 LIMIT 21
Execution time: 0.000102s [Database: default]
'Mentor 5'
```

We got one query for all students and five (N) queries to get mentors for each student. In summary, we have six (N + 1) queries.
