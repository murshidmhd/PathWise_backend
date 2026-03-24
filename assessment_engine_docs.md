# Assessment Engine Documentation

This document explains how the Assessment Engine works in the PathWise backend.

The goal is to help you understand the code in simple English so you can explain it clearly in interviews or while working on the project.

## What This Module Does

The Assessment Engine lets a student:

1. Fetch assessment questions
2. Start an assessment
3. Submit answers
4. Get scored results
5. View a final report

This engine is built using five main files:

- `models.py`
- `serializers.py`
- `services.py`
- `views.py`
- `urls.py`

Each file has a different job.

## Big Picture Flow

Think of the module like this:

- `models.py` defines the database structure
- `serializers.py` controls input and output data
- `services.py` contains the business logic
- `views.py` handles API requests and responses
- `urls.py` connects URLs to views

So the normal request flow is:

`URL -> View -> Serializer -> Service -> Model/Database -> Response`

## File-by-File Explanation

### 1. `models.py`

#### What it does

This file defines the database tables for the assessment system.

#### Why it exists

Without models, Django would not know what data to store. The models describe questions, assessments, answers, and reports.

#### How it connects to other files

- `serializers.py` reads data from these models and returns safe API output
- `services.py` creates and updates these models
- `views.py` calls service functions that use these models

### 2. `serializers.py`

#### What it does

This file validates incoming request data and controls outgoing response data.

#### Why it exists

Serializers protect the API by making sure request data has the correct format and by making sure only the right fields are returned to the client.

#### How it connects to other files

- `views.py` uses serializers before calling service functions
- `serializers.py` uses models from `models.py`
- the final API responses returned by `views.py` are often serialized model data

#### Why `correct_answer` is not returned

`correct_answer` is intentionally excluded from `QuestionSerializer`.

That is a security decision. If the frontend received the correct answer for aptitude questions, a student could inspect the API response and cheat. The backend must keep the answer key private and only use it internally while scoring the submission.

### 3. `services.py`

#### What it does

This file contains the main business logic of the module.

It handles:

- finding the student profile
- starting an assessment
- validating answers
- calculating scores
- generating the report data
- fetching the latest assessment
- fetching the final report

#### Why it exists

Putting business logic in services keeps the views clean and easier to understand. It also makes the logic easier to reuse and test.

#### How it connects to other files

- `views.py` calls functions from `services.py`
- `services.py` reads and writes the models from `models.py`
- `services.py` raises controlled errors that `views.py` returns as API responses

### 4. `views.py`

#### What it does

This file receives HTTP requests and returns HTTP responses.

Each API endpoint has a view class.

#### Why it exists

Views are the bridge between the outside world and your internal logic. They handle authentication, request validation, service calls, and response formatting.

#### How it connects to other files

- `urls.py` routes requests to views
- `views.py` uses serializers to validate request data
- `views.py` calls service functions to do the real work

### 5. `urls.py`

#### What it does

This file maps URL paths to view classes.

#### Why it exists

Without `urls.py`, Django would not know which code should run for each API endpoint.

#### How it connects to other files

- it imports the views from `views.py`
- it exposes the assessment API to the rest of the backend

## The 4 Models

### 1. `Question`

This model stores every question used in the assessment.

Fields:

- `section`: tells which part of the assessment the question belongs to. Current choices are `aptitude`, `personality`, and `interest`.
- `sub_section`: gives more detail inside a section. For aptitude it can be things like `logical`, `numerical`, `verbal`, or `spatial`.
- `question_text`: the actual question shown to the student.
- `option_a`, `option_b`, `option_c`, `option_d`: the answer choices shown to the student.
- `option_a_type`, `option_b_type`, `option_c_type`, `option_d_type`: for personality-style questions, each option can map to a RIASEC type like `R`, `I`, `A`, `S`, `E`, or `C`.
- `correct_answer`: used mainly for aptitude questions so the backend can score correct answers.
- `marks`: how many points this question gives if answered correctly.
- `created_at`: when the question was created.

Why this model matters:

It is the source of truth for the full assessment content.

### 2. `Assessment`

This model stores one assessment attempt for one student.

Fields:

- `student`: links the assessment to the student who owns it.
- `status`: tells whether the assessment is `started` or `completed`.
- `total_score`: combined score stored after submission.
- `aptitude_score`: score from aptitude questions.
- `personality_score`: count used for personality part.
- `interest_score`: count used for interest part.
- `time_taken`: optional number showing how long the student took.
- `attempt_number`: stores which attempt number this is.
- `created_at`: when the assessment started.
- `completed_at`: when the assessment was finished.

Why this model matters:

It represents the main assessment record and acts like the parent object for all submitted answers and the final report.

### 3. `AssessmentAnswer`

This model stores one answer for one question inside one assessment.

Fields:

- `assessment`: links the answer to an assessment.
- `question`: links the answer to the question being answered.
- `selected_answer`: the option chosen by the student, such as `a`, `b`, `c`, or `d`.
- `is_correct`: mainly used for aptitude questions. It stores whether the answer was correct.
- `created_at`: when the answer record was created.

Important design:

`unique_together = ['assessment', 'question']` means one assessment cannot store duplicate answers for the same question.

Why this model matters:

It keeps the detailed answer history that supports scoring and reporting.

### 4. `AssessmentReport`

This model stores the final interpreted result of the assessment.

Fields:

- `assessment`: one-to-one link to the assessment. One assessment gets one report.
- `student`: links the report to the student.
- `personality_type`: the main personality type found after scoring.
- `interest_areas`: a JSON list of top interest areas.
- `recommended_careers`: a JSON list of suggested careers.
- `strengths`: a JSON list of strengths.
- `weaknesses`: a JSON list of weaknesses.
- `report_text`: a human-readable summary of the result.
- `report_pdf_url`: optional URL if the report is also generated as a PDF.
- `created_at`: when the report was created.

Why this model matters:

It stores the final result in a form the frontend can show directly to the student.

## The 5 API Endpoints

### 1. Get Questions

- Method: `GET`
- URL: `/api/assessments/questions/`
- Request body: none
- Purpose: returns all assessment questions

Example response shape:

```json
[
  {
    "id": 1,
    "section": "aptitude",
    "sub_section": "logical",
    "question_text": "What is 2 + 2?",
    "option_a": "3",
    "option_b": "4",
    "option_c": "5",
    "option_d": "6"
  }
]
```

Notes:

- it does not expose `correct_answer`
- it does not create an assessment

### 2. Start Assessment

- Method: `POST`
- URL: `/api/assessments/start/`
- Request body: empty object is fine
- Purpose: creates a new started assessment, or returns the current started one if it already exists

Example request:

```json
{}
```

Example response shape:

```json
{
  "id": 5,
  "status": "started",
  "attempt_number": 1,
  "aptitude_score": 0,
  "personality_score": 0,
  "interest_score": 0,
  "total_score": 0,
  "time_taken": null,
  "created_at": "2026-03-24T10:00:00Z",
  "completed_at": null
}
```

### 3. Submit Assessment

- Method: `POST`
- URL: `/api/assessments/<assessment_id>/submit/`
- Request body: answers and optionally time taken
- Purpose: validates answers, scores the assessment, stores answers, creates a report, and marks the assessment as completed

Example request:

```json
{
  "answers": [
    {
      "question_id": 1,
      "selected_answer": "b"
    },
    {
      "question_id": 2,
      "selected_answer": "a"
    }
  ],
  "time_taken": 120
}
```

Example response shape:

```json
{
  "id": 5,
  "status": "completed",
  "attempt_number": 1,
  "aptitude_score": 1,
  "personality_score": 1,
  "interest_score": 0,
  "total_score": 2,
  "time_taken": 120,
  "created_at": "2026-03-24T10:00:00Z",
  "completed_at": "2026-03-24T10:15:00Z"
}
```

### 4. Get Latest Assessment

- Method: `GET`
- URL: `/api/assessments/latest/`
- Request body: none
- Purpose: returns the latest assessment for the logged-in student

Example response shape:

```json
{
  "id": 5,
  "status": "completed",
  "attempt_number": 1,
  "aptitude_score": 1,
  "personality_score": 1,
  "interest_score": 1,
  "total_score": 3,
  "time_taken": 120,
  "created_at": "2026-03-24T10:00:00Z",
  "completed_at": "2026-03-24T10:15:00Z"
}
```

### 5. Get Assessment Report

- Method: `GET`
- URL: `/api/assessments/<assessment_id>/report/`
- Request body: none
- Purpose: returns the saved report for the student’s assessment

Example response shape:

```json
{
  "id": 10,
  "personality_type": "Investigative",
  "interest_areas": ["Investigative", "Artistic"],
  "recommended_careers": ["Data Analyst", "Scientist", "Researcher"],
  "strengths": ["analytical thinking"],
  "weaknesses": ["fast social decision-making"],
  "report_text": "Your strongest assessment trend is Investigative.",
  "report_pdf_url": null,
  "created_at": "2026-03-24T10:15:00Z"
}
```

## Full Scoring Logic

The main scoring happens in `submit_assessment()` inside `services.py`.

### Aptitude Scoring

For aptitude questions:

- the backend compares `selected_answer` with `correct_answer`
- if the answer is correct, the student gets that question’s `marks`
- `is_correct` is stored in `AssessmentAnswer`
- these marks are added to `aptitude_score`

Simple example:

- question marks = `2`
- student picks the correct option
- `aptitude_score` increases by `2`

### Personality Logic Using RIASEC

For personality questions:

- each option can be mapped to a RIASEC code
- example: option `a` may map to `I` for Investigative
- when the student selects an option, the system looks at the matching `option_<letter>_type`
- that RIASEC code is counted

The current RIASEC labels are:

- `R`: Realistic
- `I`: Investigative
- `A`: Artistic
- `S`: Social
- `E`: Enterprising
- `C`: Conventional

The engine counts the selected RIASEC types and finds the top types.

Those top types are then used to generate:

- `personality_type`
- `interest_areas`
- `recommended_careers`
- `strengths`
- `weaknesses`
- `report_text`

### Interest Counting

For interest questions:

- the current code increases `interest_score` by `1` for each interest question answered
- it also counts the selected option’s mapped type if that option has a RIASEC value

So in the current implementation, interest contributes both to count-based scoring and to the report generation through selected type mapping.

### Total Score

The current total score is:

`total_score = aptitude_score + personality_score + interest_score`

So:

- aptitude adds marks based on correctness
- personality adds count values
- interest adds count values

## Student Journey Step by Step

Here is the full student journey in simple English.

### Step 1. Student logs in

All assessment endpoints require authentication, so the student must be logged in first.

### Step 2. Frontend fetches questions

The frontend calls:

`GET /api/assessments/questions/`

This returns all the questions needed to display the assessment UI.

### Step 3. Student starts the assessment

The frontend calls:

`POST /api/assessments/start/`

The backend:

- finds the student profile
- checks whether the student already has a started assessment
- if yes, returns it
- if no, creates a new assessment row

### Step 4. Student answers questions

The frontend collects question IDs and selected answers.

At this stage, answers are not yet scored until submit is called.

### Step 5. Student submits the assessment

The frontend calls:

`POST /api/assessments/<assessment_id>/submit/`

The backend then:

1. checks that the assessment belongs to the logged-in student
2. checks that the assessment exists
3. checks that it is not already completed
4. checks that the request contains answers
5. checks that there are no duplicate question IDs
6. loads the questions from the database
7. checks that all question IDs are valid
8. loops through answers and scores them
9. saves each answer to `AssessmentAnswer`
10. calculates final scores
11. marks the assessment as completed
12. creates or updates the `AssessmentReport`
13. marks the student profile as `assessment_taken = True`

### Step 6. Frontend can fetch latest status

The frontend can call:

`GET /api/assessments/latest/`

This helps the frontend know whether the student has an assessment and whether it is started or completed.

### Step 7. Student views the report

The frontend calls:

`GET /api/assessments/<assessment_id>/report/`

The backend returns the saved report from `AssessmentReport`.

## Security Decisions In This Module

These are the important security decisions already present in the assessment engine.

### 1. Authentication is required

All views use `IsAuthenticated`.

That means only logged-in users can use the assessment endpoints.

### 2. Students can only access their own assessments

In the service layer, the code fetches the assessment using both:

- `assessment_id`
- `student`

This prevents one student from accessing another student’s assessment just by changing the ID in the URL.

### 3. Correct answers are hidden from the frontend

`QuestionSerializer` does not expose `correct_answer`.

This prevents cheating and keeps scoring logic secure on the backend.

### 4. Duplicate answers are blocked

The code checks for duplicate `question_id` values in the submission.

This prevents broken or manipulated payloads from submitting the same question multiple times.

### 5. Invalid question IDs are rejected

The backend loads questions from the database and rejects IDs that do not exist.

This prevents fake or malformed question submissions.

### 6. Completed assessments cannot be submitted again

The code blocks re-submission if the assessment status is already `completed`.

This protects the final result from being overwritten after completion.

### 7. Database transaction is used during submission

`submit_assessment()` uses `@transaction.atomic`.

That means the submit flow is treated like one safe database operation. If something fails in the middle, Django can roll back the whole transaction instead of saving partial data.

## Why This Design Is Good

This module follows a clean backend structure:

- models store the data
- serializers validate and format the data
- services handle the logic
- views handle HTTP
- urls connect endpoints

This makes the code easier to read, easier to test, and easier to scale.

## Simple Interview Explanation

If you want a short interview answer, you can say:

"I built an assessment engine in Django REST Framework using a service-based structure. The models store questions, assessment attempts, submitted answers, and final reports. The serializers validate request data and hide sensitive fields like correct answers. The views expose endpoints for fetching questions, starting an assessment, submitting answers, checking the latest assessment, and viewing the report. The service layer handles scoring, RIASEC personality mapping, report generation, and ownership validation. This keeps the logic clean, secure, and easy to maintain."
