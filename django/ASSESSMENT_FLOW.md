# Assessment Flow

This document defines the intended assessment product flow for PathWise.

## Goal

The assessment should help PathWise understand a student well enough to generate meaningful guidance from a single assessment journey.

The assessment currently combines three areas:

- Aptitude
- Personality
- Interest

The result of the assessment should be used as a stable profile signal for the student.

## Core Product Decision

Each student has only one assessment attempt.

That means:

- A student can start the assessment once
- A student can pause and continue later if the assessment is still in progress
- A student cannot create multiple attempts
- A student cannot start a new assessment after completing it

For now, there is no retake flow.

## Assessment Lifecycle

The assessment has three practical states:

1. Not started
2. Started
3. Completed

Lifecycle:

`not started -> started -> completed`

## Endpoint Responsibilities

### 1. Get Questions

`GET /api/assessments/questions/`

Purpose:

- Return all questions required for the assessment

Rules:

- Does not create an assessment
- Can be called at any time by an authenticated student
- Returns questions grouped or labeled by section such as `aptitude`, `personality`, and `interest`

### 2. Start Assessment

`POST /api/assessments/start/`

Purpose:

- Start the student's assessment, or resume it if it was already started

Rules:

- If the student has no assessment, create one with status `started`
- If the student already has a `started` assessment, return that same assessment
- If the student already has a `completed` assessment, do not create a new one

This endpoint is effectively a "start or resume" endpoint.

### 3. Continue Assessment

Continuing the assessment means the student returns later and resumes the same in-progress assessment.

Rules:

- A student can leave midway and come back later
- If the assessment status is `started`, the same assessment should be resumed
- No second assessment should be created

Frontend note:

- The frontend may temporarily store answers locally until final submission
- A future improvement may add draft-saving to the backend, but that is not required for the current product flow

### 4. Submit Assessment

`POST /api/assessments/<assessment_id>/submit/`

Purpose:

- Finalize the student's assessment

Rules:

- Only the owner of the assessment can submit it
- Only assessments with status `started` can be submitted
- Submission is final
- All required questions must be answered before submission is accepted
- The backend calculates scores and generates report data
- After successful submission, the assessment status becomes `completed`
- A completed assessment cannot be edited or submitted again

Important meaning:

- `submit` means final submit, not partial submit

### 5. Get Latest Assessment

`GET /api/assessments/latest/`

Purpose:

- Tell the frontend the current assessment state for the logged-in student

Rules:

- If no assessment exists, return a clear "not started" result or `404`
- If the assessment is `started`, the frontend should continue the in-progress flow
- If the assessment is `completed`, the frontend should move the student to the report or results screen

This endpoint acts as a status-check endpoint.

### 6. Get Report

`GET /api/assessments/<assessment_id>/report/`

Purpose:

- Return the final assessment result

Rules:

- Only the owner of the assessment can access the report
- The report should only be available after the assessment is completed
- If the assessment is still `started`, the report should not be returned

## Recommended User Journey

1. Student opens the assessment area
2. Frontend calls `GET /api/assessments/latest/`
3. If no assessment exists, show a start screen
4. Student starts the assessment using `POST /api/assessments/start/`
5. Student answers all questions
6. Student may leave and later resume the same in-progress assessment
7. Student submits final answers using `POST /api/assessments/<assessment_id>/submit/`
8. Backend marks the assessment as `completed` and generates report data
9. Frontend shows the report screen

## Product Rules To Enforce In Code

- One assessment per student
- `start` must create or resume, never create duplicates
- `submit` must be final
- `submit` must require all required questions
- `report` must only be available for completed assessments
- No retake flow for now

## Future Enhancements

These are intentionally out of scope for the current version:

- Retake assessment flow
- Backend draft save endpoint
- Versioned assessments
- Admin-configurable question sets
- Multiple reports over time
