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

1. Selecting related objects
   Let's check how many queries are executed when we fetch the first 5 students and then print their mentors:

```shell
>>> students = Student.objects.select_related("mentor")[:5]
>>> for student in students:
...     student.mentor.name
...
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id",
       "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_student"
  LEFT OUTER JOIN "university_mentor"
    ON ("university_student"."mentor_id" = "university_mentor"."id")
 LIMIT 5
Execution time: 0.000271s [Database: default]
'Mentor 92'
'Mentor 49'
'Mentor 40'
'Mentor 10'
'Mentor 5'
```

Now we have only one query to get all students and mentors we need.
The `select_related()` is a solution of `N + 1` problem for many-to-one relationships.

1. Using `prefetch_related()`
   When we want to solve the `N +1` problem with one-to-many relationship or many-to-many relationship, we can use `prefetch_related()` method.
   But first, let's check how many queries are executed when we fetch the first 5 students and then print their mentors:

```shell
>>> mentors = Mentor.objects.all()[:5]
>>> for mentor in mentors:
...     mentor.student_set.all()
...
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 LIMIT 5
Execution time: 0.000232s [Database: default]
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 WHERE "university_student"."mentor_id" = 1
 LIMIT 21
Execution time: 0.000247s [Database: default]
<QuerySet [<Student: Student 20>, <Student: Student 38>, <Student: Student 402>, <Student: Student 718>, <Student: Student 754>, <Student: Student 791>, <Student: Student 1105>, <Student: Student 1139>, <Student: Student 1331>, <Student: Student 1429>, <Student: Student 1805>, <Student: Student 1899>, <Student: Student 2064>, <Student: Student 2090>, <Student: Student 2139>, <Student: Student 2256>, <Student: Student 2464>, <Student: Student 2609>, <Student: Student 2632>, <Student: Student 2758>, '...(remaining elements truncated)...']>
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 WHERE "university_student"."mentor_id" = 2
 LIMIT 21
Execution time: 0.000142s [Database: default]
<QuerySet [<Student: Student 800>, <Student: Student 810>, <Student: Student 859>, <Student: Student 1250>, <Student: Student 1353>, <Student: Student 1396>, <Student: Student 1438>, <Student: Student 1630>, <Student: Student 1669>, <Student: Student 1784>, <Student: Student 1922>, <Student: Student 1953>, <Student: Student 2198>, <Student: Student 2286>, <Student: Student 2484>, <Student: Student 2517>, <Student: Student 2527>, <Student: Student 2613>, <Student: Student 2875>, <Student: Student 2915>, '...(remaining elements truncated)...']>
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 WHERE "university_student"."mentor_id" = 3
 LIMIT 21
Execution time: 0.000117s [Database: default]
<QuerySet [<Student: Student 119>, <Student: Student 186>, <Student: Student 270>, <Student: Student 330>, <Student: Student 650>, <Student: Student 683>, <Student: Student 762>, <Student: Student 766>, <Student: Student 887>, <Student: Student 990>, <Student: Student 1054>, <Student: Student 1062>, <Student: Student 1127>, <Student: Student 1218>, <Student: Student 1278>, <Student: Student 1348>, <Student: Student 1485>, <Student: Student 1534>, <Student: Student 1547>, <Student: Student 1571>, '...(remaining elements truncated)...']>
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 WHERE "university_student"."mentor_id" = 4
 LIMIT 21
Execution time: 0.000096s [Database: default]
<QuerySet [<Student: Student 99>, <Student: Student 174>, <Student: Student 212>, <Student: Student 666>, <Student: Student 685>, <Student: Student 697>, <Student: Student 729>, <Student: Student 772>, <Student: Student 832>, <Student: Student 951>, <Student: Student 956>, <Student: Student 1053>, <Student: Student 1196>, <Student: Student 1505>, <Student: Student 1584>, <Student: Student 1693>, <Student: Student 1740>, <Student: Student 1987>, <Student: Student 2099>, <Student: Student 2170>, '...(remaining elements truncated)...']>
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 WHERE "university_student"."mentor_id" = 5
 LIMIT 21
Execution time: 0.000132s [Database: default]
<QuerySet [<Student: Student 5>, <Student: Student 23>, <Student: Student 117>, <Student: Student 324>, <Student: Student 371>, <Student: Student 439>, <Student: Student 493>, <Student: Student 569>, <Student: Student 589>, <Student: Student 844>, <Student: Student 901>, <Student: Student 924>, <Student: Student 1120>, <Student: Student 1351>, <Student: Student 1387>, <Student: Student 1440>, <Student: Student 1533>, <Student: Student 1549>, <Student: Student 1556>, <Student: Student 1654>, '...(remaining elements truncated)...']>
```

The `student_set` attribute is a [ManyRelatedManager](https://docs.djangoproject.com/en/6.0/ref/models/relations/) object.

- Now let's check how many queries are executed when we fetch the first 5 students with `prefetch_related()` and then print their mentors:

```shell
>>> mentors = Mentor.objects.prefetch_related("student_set")[:5]
>>> for mentor in mentors:
...     student.mentor.name
...
SELECT "university_mentor"."id",
       "university_mentor"."name",
       "university_mentor"."specialization"
  FROM "university_mentor"
 LIMIT 5
Execution time: 0.000144s [Database: default]
SELECT "university_student"."id",
       "university_student"."name",
       "university_student"."bio",
       "university_student"."mentor_id"
  FROM "university_student"
 WHERE "university_student"."mentor_id" IN (1, 2, 3, 4, 5)
Execution time: 0.000356s [Database: default]
'Mentor 5'
'Mentor 5'
'Mentor 5'
'Mentor 5'
'Mentor 5'
```

Now, we have only two queries to get all students and mentors we need.
