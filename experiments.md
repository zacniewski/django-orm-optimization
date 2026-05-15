# Django ORM Optimization Experiments

This document contains a detailed log of experiments conducted to analyze and optimize database queries using the Django ORM.

______________________________________________________________________

## 📋 Table of Contents

- [Environment Setup](#-environment-setup)
- [Experiment 1: QuerySet Count & Fetching](#experiment-1-queryset-count--fetching)
- [Experiment 2: QuerySet Caching](#experiment-2-queryset-caching)
- [Experiment 3: Efficient Updates](#experiment-3-efficient-updates)
- [Experiment 4: Lazy Loading](#experiment-4-lazy-loading)
- [Experiment 5: The N+1 Problem](#experiment-5-the-n1-problem)
- [Experiment 6: Solving N+1 with `select_related`](#experiment-6-solving-n1-with-select_related)
- [Experiment 7: Solving N+1 with `prefetch_related`](#experiment-7-solving-n1-with-prefetch_related)

______________________________________________________________________

## 🛠 Environment Setup

Before running the experiments, ensure the environment is ready and data is loaded.

```bash
# Start Shell Plus with SQL printing enabled
python manage.py shell_plus --print-sql
```

**Common Imports used in Shell Plus:**

```python
from university.models import Mentor, Student
from django.db.models import Avg, Case, Count, F, Max, Min, Prefetch, Q, Sum, When
```

______________________________________________________________________

## Experiment 1: QuerySet Count & Fetching

Analyzing basic interaction with the `Mentor` model.

```python
>>> Mentor.objects.count()
SELECT COUNT(*) AS "__count" FROM "university_mentor"
Execution time: 0.000271s [Database: default]
100

>>> Mentor.objects.all()
SELECT "university_mentor"."id", "university_mentor"."name", "university_mentor"."specialization"
FROM "university_mentor"
LIMIT 21
Execution time: 0.000833s [Database: default]
<QuerySet [<Mentor: Mentor 1>, <Mentor: Mentor 2>, ...]>
```

______________________________________________________________________

## Experiment 2: QuerySet Caching

Demonstrating Django's internal QuerySet caching. Notice the significant drop in execution time on the second call.

```python
# First execution
>>> Mentor.objects.all()
Execution time: 0.000833s

# Second execution
>>> Mentor.objects.all()
Execution time: 0.000168s
```

**Observation:** The second execution is approximately **5x faster** due to caching.

______________________________________________________________________

## Experiment 3: Efficient Updates

Comparing standard `save()` vs. `update_fields` and the `update()` method.

### Standard `save()`

Updates all fields, even if they haven't changed.

```python
>>> mentor = Mentor.objects.get(id=1)
>>> mentor.name = "New Name"
>>> mentor.save()
UPDATE "university_mentor" SET "name" = 'New Name', "specialization" = 'Frontend' WHERE "university_mentor"."id" = 1
Execution time: 0.007082s
```

### Optimized `save(update_fields=...)`

Only updates specified columns.

```python
>>> mentor.save(update_fields=['name'])
UPDATE "university_mentor" SET "name" = 'New Name' WHERE "university_mentor"."id" = 1
Execution time: 0.000343s
```

### QuerySet `update()`

Executes a single SQL UPDATE statement directly.

```python
>>> Mentor.objects.filter(id=1).update(name="New Name")
UPDATE "university_mentor" SET "name" = 'New Name' WHERE "university_mentor"."id" = 1
Execution time: 0.000167s
```

______________________________________________________________________

## Experiment 4: Lazy Loading

QuerySets are lazy—the database is only hit when the data is actually needed (e.g., during iteration or printing).

```python
>>> mentors = Mentor.objects.all() # No query executed yet
>>> print(mentors)                 # Database is hit here
SELECT ... FROM "university_mentor" LIMIT 21
```

______________________________________________________________________

## Experiment 5: The N+1 Problem

Identifying the classic N+1 performance bottleneck where related objects are fetched individually.

```python
>>> students = Student.objects.all()[:5]
>>> for student in students:
...     print(student.mentor.name)

# Results in 1 query for students + 5 queries for each mentor
SELECT ... FROM "university_student" LIMIT 5;
SELECT ... FROM "university_mentor" WHERE "id" = 92;
SELECT ... FROM "university_mentor" WHERE "id" = 49;
SELECT ... FROM "university_mentor" WHERE "id" = 40;
SELECT ... FROM "university_mentor" WHERE "id" = 10;
SELECT ... FROM "university_mentor" WHERE "id" = 5;
```

**Summary:** Total of **6 queries** (N + 1).

______________________________________________________________________

## Experiment 6: Solving N+1 with `select_related`

Using SQL `JOIN` to fetch related objects in a single query. Best for `ForeignKey` or `OneToOne` relationships.

```python
>>> students = Student.objects.select_related("mentor")[:5]
>>> for student in students:
...     print(student.mentor.name)

SELECT "university_student".*, "university_mentor".*
FROM "university_student"
LEFT OUTER JOIN "university_mentor" ON ("university_student"."mentor_id" = "university_mentor"."id")
LIMIT 5
```

**Summary:** Reduced to **1 query**.

______________________________________________________________________

## Experiment 7: Solving N+1 with `prefetch_related`

Using a separate query to fetch related objects for `ManyToMany` or reverse `ForeignKey` relationships.

### Without Optimization (N+1)

```python
>>> mentors = Mentor.objects.all()[:5]
>>> for mentor in mentors:
...     list(mentor.student_set.all())
# Results in 1 query for mentors + 5 queries for students
```

### With `prefetch_related`

```python
>>> mentors = Mentor.objects.prefetch_related("student_set")[:5]
>>> for mentor in mentors:
...     list(mentor.student_set.all())

SELECT ... FROM "university_mentor" LIMIT 5;
SELECT ... FROM "university_student" WHERE "mentor_id" IN (1, 2, 3, 4, 5);
```

**Summary:** Reduced to **2 queries** regardless of N.

______________________________________________________________________
