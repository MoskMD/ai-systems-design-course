# Module 07: Agents and Multi-Agent Systems — Laboratory

> **Status:** Ready for Students — approved for publication by the instructor on 2026-11-20

## Goal

The goal of this laboratory is:

1. Closure of the fixed path’s gap in selecting the next permitted operation in response to returned information.
2. Execution of an inspectable, read-only **agent loop**.
3. Evaluation of task accomplishment, response quality and resource use for the adaptive and fixed paths under declared comparison conditions.

## Tasks

1. Execute a model-selected information request and inspect the application permission decision and actual read.
2. Continue the same task through evidence admission, model-directed operation choices, returned observations and bounded stopping.
3. Execute the predefined continuation from the same retained read, judge actual responses independently and interpret resource observations under common conditions.
4. Exercise controlled permission-denial, retained-versus-delivered-evidence and interrupted-call checks without additional paid model calls.
5. Complete the Ukrainian source report, preserve the required screenshots, verify the exact final student commit and prepare the standalone Teams report.

## Expected result

The completed route leaves the following inspectable artifacts under `reports/lab07/`:

- `first-read/` — the actual first action, permission decision, executed query and returned candidates, or the preserved stopping outcome.
- `adaptive/` — the bounded adaptive continuation, admitted evidence, actual requests, responses and task-progress delivery.
- `fixed/` — the predefined continuation from the same first read, preserving actual generation or failure.
- `boundaries/` — explicitly controlled diagnostic captures and their summary, when completed.
- `REPORT.md` and `screenshots/` — the student's independent judgments, resource interpretation, stopping boundary and own checkpoint images.
- `verification-report.json` — exact final-commit verification, distinguishing complete from honestly partial records.
- `submission/REPORT.md` — generated Ukrainian Teams report with reached images embedded, not a Git source artifact.

An incomplete or unfavorable attempt is preserved rather than replaced. A successful command or model stop is not a favorable human response judgment, proof of task accomplishment or permission for a canonical write.

## Expected competencies

After completing the laboratory, the student can:

- distinguish an **agent**, **agent environment**, **agent harness** and **multi-agent system**;
- separate action choice, permission, actual execution and returned observation;
- trace **planning agent actions**, **agent memory** and **agent operation orchestration** through actual bounded requests;
- apply the inherited response **rubric** separately from task and execution judgments;
- compare adaptive and predefined control without treating observed resource differences as causal superiority;
- preserve a truthful interrupted result and complete commit-bound reporting.

## Prerequisites

- Laboratories 01–06 completed; the current cumulative `training-project` synchronized and dependencies installed.
- Approved Module 07 theory, including the six capability areas, and Module 06 response-judging procedure.
- A personal course fork and permission to create a branch named `lab07/<student-id>` from the completed Laboratory 06 branch.
- Authenticated AGY access with the requested model available and sufficient no-cost allowance. Stop on unavailability or exhaustion; no paid-credit purchase or automatic retry is required.
- A Windows workstation with a local administrator account, or Linux/macOS with equivalent installation and repository-write permissions. Eligibility depends on capabilities, not the operating-system name.

## Starting state

The teaching example applies the general control approach to explaining why a **query embedding** is needed for **embedding-based retrieval**. The course supplies the synthetic two-passage resource `cases/lab07/accessible-passages.json`, not another accepted-collection change or graph-preparation task. The initial request supplies AP-1, which names the prerequisite; the model must not receive AP-2 merely because the human can inspect the source resource.

The student runs the actual route and separately acts as **human evaluator**. The application owns source access, admission, permission checks, invocation, observation delivery and stopping limits. The **canonical knowledge collection** remains unchanged. Workspace report/runtime outputs are not accepted knowledge. The experiment does not implement a **multi-agent system** or another retrieval algorithm.

All commands below run from the synchronized `training-project` directory. Replace `<student-id>` with the personal branch identifier; create that branch using the course Git procedure before initialization. Do not begin model execution before the source report exists.

## Steps

### Preparation — initialize the report

The student follows [Laboratory standing rules](../../LABORATORY_STANDING_RULES.md), creates the personal branch `lab07/<student-id>` from the completed Laboratory 06 branch, and works from `training-project`. Before the first model call, the student initializes the source report and screenshot directory from the course-owned `fixtures/lab07/REPORT.md`:

```text
uv run learning-project lab07 init-report --report-dir reports/lab07
```

The command creates `reports/lab07/REPORT.md` and `reports/lab07/screenshots/`; an existing report stops initialization without overwrite. The report is editable instructional scaffolding. The student replaces/removes all prompts and opening directions, preserves the Ukrainian headings, and writes in formal third-person or impersonal technical style. Record the common conditions and evaluator-only judging basis before the fixed call, keeping that material outside model requests. Every screenshot must show the operating-system or GitHub account and system date.

The report's `## Хід виконання` links follow the producing student checkpoints:

- Student Step 1: `screenshots/01-model-selected-read.png` — requested action, permission, actual input/return and no-next-request boundary, or the actual stopping result.
- Student Step 2: `screenshots/02-adaptive-explanation-feedback.png` — actual admission, chosen operations, available generation/feedback and final status.
- Student Steps 3–4: `screenshots/03-fixed-adaptive-comparison.png` — actual route outcomes, independent human rubric/task judgments and resource boundaries.
- Student Step 5: `screenshots/04-boundary-checks.png` — controlled permission, delivery and interruption observations.
- Student Step 6: `screenshots/05-final-verification.png` — post-commit command, exact full commit hash, outcome, account and system date.

### Purpose and boundary

The student begins one prerequisite-explanation task: explain why a **query embedding** is needed for **embedding-based retrieval** in the teaching route. The initial passage names the prerequisite without explaining the representation's role. The model chooses the next action; application code decides whether the request is permitted and executes a permitted **retrieval operation**.

Student Step 1 stops after the operation returns candidate passages. The candidate passages have not undergone **retrieval-unit selection**, have not been delivered in another **bounded model request**, and do not constitute a generated answer. Later steps continue the same task, rather than starting independent section exercises.

### Inputs and responsibilities

The student starts from the cumulative `training-project` with the supported `uv` environment from Laboratories 01–06. The student needs authenticated AGY access with available no-cost allowance. The example uses the currently verified model identifier `gemini-3.8-flash-low`; `agy models` must list the identifier before execution. A successful catalogue request does not prove remaining quota or model capacity. The command disables paid-credit opt-in through `useG1Credits: false`; the student must stop on exhaustion rather than purchase credits for the exercise.

The course supplies `cases/lab07/accessible-passages.json`, a read-only synthetic source resource identified as `S-AGENT/v1`. The passages instantiate Module 07 Section 1.3; the resource is not a change to the **canonical knowledge collection** accepted in Laboratory 06.

- `AP-1`, source `S-AGENT`, version `v1`, passage 1: “In this teaching route, understanding embedding-based retrieval requires understanding a query embedding.”
- `AP-2`, source `S-AGENT`, version `v1`, passage 2: “A query embedding represents the question as a vector for comparison with stored vectors representing retrieval units. Understanding that representation explains how the question can be matched to candidate retrieval units.”

The application initially admits only `AP-1` as **supplied source evidence**. `AP-2` remains accessible to the retrieval operation but is absent from the action-selection request. The course-owned admission is fixed for the starting request; this step does not ask the student to approve new knowledge.

The **tool inventory** exposes two operations:

- The **retrieval operation** accepts a nonempty `text query` and `collection` equal to `S-AGENT/v1`. The application searches the two source passages with the established lexical-overlap method from Laboratory 04, retaining source locators. The subject of the explanation is embedding-based retrieval; the search method used to obtain the explanation's evidence is lexical retrieval.
- The **model-backed prerequisite-explanation operation** accepts empty arguments; application code would construct the operation's request from admitted evidence. Student Step 2 can execute that operation after evidence admission.

The model may also propose `stop` with empty arguments. The student observes the actual choice without replacing an unfavorable choice. The application, not the model or student, enforces the fixed source scope. Model-selected paths, shell commands and canonical writes are not executable inputs.

### Student Step 1 — Execute and inspect the first action

From `training-project`, run the following commands in Windows PowerShell or a Linux/macOS terminal:

```text
agy models
uv run learning-project lab07 run-first-action --model gemini-3.8-flash-low --output-dir reports/lab07/first-read
```

The command reserves a create-only attempt and writes the exact action-selection **bounded model request** before invoking AGY. The three request fields are `task instruction`, `supplied source evidence` and `output contract`. The operation schema is part of the output contract, not a separate AGY schema-repair turn. The model returns a proposed action; application code performs the permitted search. No model tool call executes the search directly.

Open the generated files in the editor:

- `attempt.json` records the requested adapter/model, source version and acquisition mode.
- `request.json` preserves the original task, operation descriptions, initial `AP-1` evidence and action-output contract.
- `provider-response.json` preserves complete stdout, stderr and process exit code, including the provider envelope and reported usage when present.
- `action.json` preserves the single extracted action request.
- `trace.json` separates the requested action, permission decision, executed inputs and **ranked candidate output**.
- `run-metadata.json` records the observed status and provider-process duration; `semantic_judgment` remains `not performed`.

**Observed normal-path result:** `status` is `candidates returned`; the requested operation is `retrieval operation`, the permission decision is allowed, and `executed input` equals the model's actual query and `S-AGENT/v1`. Another live model query may produce another ranking or no candidates. Neither the observed order nor an exact query is a required favorable model choice.

The student verifies that:

1. `request.json` contains only `AP-1` as supplied source evidence; the explanatory text of `AP-2` is absent.
2. The action request names the operation and exact arguments; the permission decision is a separate application result.
3. Every returned candidate's identifier, text and source locator resolve to the supplied resource. A lexical score is not a human support judgment.
4. `delivered to next model request` is `false` and `next_model_request_count` is zero. No new explanation or favorable task-accomplishment judgment is claimed.

Capture `01-model-selected-read.png` showing the requested action, allowed permission, executed query, returned identifiers and source locators, and the no-next-request boundary. Preserve the generated files and screenshot for the later report route; do not edit provider evidence or treat a screenshot as a replacement for the machine-readable trace.

If the command fails, outputs already exist, permission is denied, the model proposes stopping, the model requests the unexecuted explanation operation, or retrieval returns no candidates, stop and preserve the actual available evidence. Do not overwrite the attempt, rename an operation or substitute a predefined query to manufacture the normal path. Provider execution failure is not a **refusal** from the prerequisite-explanation operation. Even a normally returned nonempty candidate list does not prove the original task is complete.

### Purpose and boundary

The student continues the original task: explain why a **query embedding** is needed for **embedding-based retrieval** in the teaching route. The preceding read returned candidates but did not deliver another model request. The application now admits eligible passages, delivers the next action-selection **bounded model request**, executes a permitted requested operation and returns the operation result to a later decision. The **agent loop** ends on the model's stop proposal or an application-enforced limit, not an automatic favorable judgment.

### Inputs and application limits

Use the completed `reports/lab07/first-read` from Student Step 1 and the unchanged course resource `cases/lab07/accessible-passages.json`. Continue only after the first-read checks establish `candidates returned` and a nonempty candidate list. The continuation validates the retained request, action and trace by replaying the captured response against the course resource without calling a provider. The original capture remains unchanged. Authenticated AGY access with available no-cost allowance is still required; stop on unavailability or exhaustion. The requested model identifier remains `gemini-3.8-flash-low`; the provider envelope does not independently attest the served model or account.

The application owns the following limits:

- **Retrieval-unit selection** reuses `RUS-05-v1`: **provenance link** resolution against the supplied source precedes **context budget** fit. The course sets the **context budget** to 600 source-text characters, processed in actual candidate order. The limit excludes request instructions, locators and provider overhead; the limit is not 600 tokens or a whole-prompt size.
- The **tool inventory** remains the two operations from Student Step 1. The model may request another permitted **retrieval operation**, request the **model-backed prerequisite-explanation operation** with empty arguments, or propose `stop` with empty arguments. The application never substitutes a preferred choice.
- The application permits at most three additional action-selection decisions after the first read. Each decision invokes at most one selected operation. Generation uses a separate provider invocation; retrieval executes locally. Every provider invocation has a five-minute AGY timeout and a 330-second process timeout. No automatic retry or schema-repair turn is requested; `useG1Credits: false` remains enforced.
- No requested action changes the **canonical knowledge collection**. Generated workspace artifacts are not accepted knowledge or canonical-write authority.

### Student Step 2 — Continue and inspect the adaptive attempt

From `training-project`, run the following commands in Windows PowerShell or a Linux/macOS terminal:

```text
agy models
uv run learning-project lab07 continue-adaptive --first-action-dir reports/lab07/first-read --model gemini-3.8-flash-low --output-dir reports/lab07/adaptive
```

The output directory is create-only. If the model identifier is absent, the first-read capture is missing or inconsistent, or any reserved output exists, stop and preserve the available files. Do not overwrite an attempt or repeat the model call to obtain a favorable choice.

Open the generated files in the editor. Paths below are relative to `reports/lab07/adaptive`:

- `attempt.json` preserves the source resource, complete first-read capture, requested model and application limits.
- `decision-N/selection-record.json`, where `N` is 1–3, records actual candidates, admission checks, exclusions and remaining **context budget** before decision `N`. The concrete first path is `reports/lab07/adaptive/decision-1/selection-record.json`.
- `decision-N/request.json` preserves the action-selection **bounded model request**. Only admitted passages appear as **supplied source evidence**. Selected completed-read information or a preceding generation return appears as quoted task-progress data inside the **task instruction**, not a fourth field or another source passage.
- `decision-N/action.json` and `decision-N/trace.json` distinguish the actual requested action, application permission, executed input and operation return. A stop proposal or denied action has no executed operation input.
- `decision-N/generation/request.json` and `decision-N/generation/outcome.json` exist when generation is invoked and a structurally valid outcome is extracted. The generation **bounded model request** uses the same admitted passages, the original question and the inherited citation/**refusal** conditions, not the entire retained history.
- Each invoked model call preserves `provider-response.json` and `call-metadata.json` beside the corresponding request. The complete provider envelope remains separate from the extracted action or outcome; a failed call may have no extracted file.
- `retained-state.json` records the original question, latest executed query, latest retained candidates, generation returns and last selected task-progress data. The files together implement **agent memory** for the attempt, not personal cross-session storage.
- `run-metadata.json` records actual continuation status, new provider-invocation count and elapsed continuation time. Timing starts after predecessor-capture validation and excludes the earlier first read and human judgment. Unreported consumption remains unknown, not zero.

Each **bounded model request** contains exactly three fields:

- **Task instruction**: the original task and purpose-specific instructions; selected progress appears only in action-selection requests.
- **Supplied source evidence**: the passages admitted for the current invocation.
- **Output contract**: the action schema for action selection, or the inherited explanation/**refusal** schema for generation.

The student verifies the following checklist in reading order:

1. Compare the first-read candidates with `decision-1/selection-record.json`: each admitted passage retains a resolvable source locator and fits the budget. Compare admitted identifiers and text with `decision-1/request.json`; retained candidate text alone does not establish delivery.
2. Follow each action and trace in numeric decision order. A model choice is an observable next-action intention within **planning agent actions**, not proof of execution. Check the permission decision and executed input before attributing an operation to the model's requested route. The application performs **agent operation orchestration**; the separate generation call is not another **agent**.
3. When generation occurs, inspect actual claims and **claim citations**, or the structured **refusal** and blocking condition. Check any subsequent action-selection request for the quoted actual return. Generation text is task-progress data, not newly admitted source evidence. An operation at the final decision limit may have no subsequent request; inspect the limit status instead of claiming feedback was delivered.
4. Read the final status separately from the response. `stop proposed` means the model requested no further operation. `application decision limit reached` means the application ended continuation without a model stop proposal. Neither status establishes task accomplishment. The student later acts as **human evaluator** under the inherited **rubric**; `semantic_judgment` remains `not performed` and `task_accomplishment` remains `not judged` here.

Capture `02-adaptive-explanation-feedback.png` showing the admission record, actual operation choice, generation return when available, subsequent feedback request when available, and final status. Preserve the screenshot and generated files for the later report route. Record absent response or feedback explicitly rather than substituting an example.

### Purpose and comparison conditions

The student compares the completed adaptive attempt with a predefined continuation of the same prerequisite-explanation task. The fixed path admits the retained read candidates, invokes the **model-backed prerequisite-explanation operation** once and terminates. The fixed path makes no model-directed next-action choice, performs no additional search and requests no feedback decision. The comparison concerns control over the remaining operations, not a new **retrieval** algorithm or another **agent**.

Both continuations use the same completed `reports/lab07/first-read`, original question, source corpus, read-only permissions, requested model identifier and **retrieval-unit admission criteria**. The source-text **context budget** remains 600 characters. Both generation paths use the same purpose-specific **bounded model request** builder, citation/**refusal** contract and AGY settings. The adaptive path can change the candidates through an additional permitted read; any resulting evidence difference belongs to the executed route and must be recorded, not silently removed.

The student records the comparison conditions before the fixed call:

- **Task and starting evidence:** the original question and exact retained first-read capture already used by the adaptive attempt; no extra passage is preloaded.
- **Available resources and permissions:** unchanged `cases/lab07/accessible-passages.json`, two-operation **tool inventory**, no canonical writes and create-only local outputs.
- **Model and acquisition:** requested `gemini-3.8-flash-low`, provider-default generation settings, `useG1Credits: false`, one attempt per call, no repair turn or retry. The served model and account are not independently attested by the envelope.
- **Changed factors:** fixed versus adaptive control, any subsequently changed evidence, independent call times and any observable provider/context difference. Unknown provider conditions remain unknown.
- **Observation boundary:** each continuation starts after validation of the same retained first read and ends after outcome handling, before writing final run metadata. Admission, provider waiting and extraction are included. Initial first-read execution, human judgment and reporting are excluded from both continuation times.

The comparison is descriptive, not a fresh whole-task benchmark or configuration-selection decision. Independently timed calls do not isolate the cause of a timing difference. No quality improvement, response difference or favorable result is required. Preserve the earlier adaptive attempt rather than rerunning the model to obtain a better comparison.

### Evaluator-only judging basis

Before the fixed call, the student records the evaluator-only judging basis from `AP-1` and `AP-2` and the original question:

1. Preserve the teaching-route qualification and the prerequisite connection between **embedding-based retrieval** and **query embedding**.
2. Explain the **query embedding**'s vector representation of the question, comparison with stored vectors representing **retrieval units**, and the role of that comparison in matching candidate **retrieval units**.
3. Require a supporting **claim citation** for every factual claim; extra claims must remain source-supported and within scope.

### Student Step 3 — Execute the predefined continuation

Use the completed adaptive attempt from Student Step 2. From `training-project`, run the following commands in Windows PowerShell or a Linux/macOS terminal:

```text
agy models
uv run learning-project lab07 run-fixed --first-action-dir reports/lab07/first-read --model gemini-3.8-flash-low --output-dir reports/lab07/fixed
```

Stop if no-cost model access is unavailable, the retained capture is inconsistent or any fixed output position already exists. Do not overwrite an attempt or retry after failure. A generation failure leaves available request, raw response and status records; preserve the missing outcome and actual reason rather than substituting a **refusal**.

Open the following files under `reports/lab07/fixed`:

- `attempt.json` — complete retained first-read capture, source resource, requested model, acquisition settings and predefined path.
- `selection-record.json` — actual admission after provenance resolution and budget checks; compare with the adaptive admission record before claiming the model received the same passages.
- `generation/request.json` — actual three-field generation **bounded model request**. Compare with every adaptive generation request, when present; record any changed evidence separately from the unchanged instructions and output contract.
- `generation/provider-response.json` and `generation/call-metadata.json` — complete transport capture, measured process duration and actual failure, when present.
- `generation/outcome.json` — extracted explanation or **refusal**, when a structurally valid outcome exists. An extracted outcome is not a favorable response judgment.
- `trace.json` and `run-metadata.json` — predefined control, permission, actual generation input, return or failure, invocation count, continuation duration and final status. `fixed path completed` means the application finished the predefined operations, not that the question was answered correctly.

### Student Step 4 — Judge responses and interpret resources

Keep the judging basis and resulting judgments outside every model request. The numbered response-judging procedure below follows Module 06 precedence; judge each route's actual response independently rather than preferring the faster route:

1. Identify the actual response. Inspect `generation/outcome.json` when present and the raw provider response when extraction failed. An identifiable attempted explanation with missing fields or citations fails the **Prerequisite explanation check**; failed extraction does not turn that attempted explanation into a **refusal**. When no identifiable permitted response exists, record the execution failure or absent response and stop response judging for that route.
2. For a **generated prerequisite explanation**, the student acts as **human evaluator** and applies the **Prerequisite explanation check** against the recorded basis and the actual admitted text. Record pass/fail and claim-specific reasons, checking citation support rather than locator resolution alone.
3. For a **refusal**, the **human evaluator** applies the **Refusal check** against the actual request. Insufficiency or a conflicting source instruction must actually hold. A correct **refusal** can leave the requested explanation unprovided.
4. Separately record whether the original task was accomplished under the permission and evidence constraints, citing the actual explanation or the missing result and reason. Neither stop status nor a successful generation process establishes task accomplishment. Automated metadata remains `semantic_judgment: not performed` and `task_accomplishment: not judged`; the student's human judgments belong in the report, not edited runtime files.

For each route, the student records the following resource observations, including failed and unfinished work:

- Actual additional action-selection decisions, generation invocations and extra local retrieval invocations. Count a stop proposal as a decision without a tool invocation. Exclude the shared initial read and its model call from both continuation totals.
- `continuation_seconds` from each `run-metadata.json`, using the declared shared boundary. Record individual `provider_process_seconds` separately; summed process durations are not the same measurement as continuation elapsed time.
- Each included provider envelope's reported `usage`, when available. Sum `total_tokens` only when every included invocation reports that field; otherwise report the partial sum with its included-call count and mark the complete total unknown. Provider-reported tokens are not money, quota percentage, source-text characters or human-review time.
- Human judging time only if measured separately; otherwise record unknown. Do not infer zero from the absence of a measurement.

The student writes a bounded comparison supported by the actual requests, responses, judgments and resource records. Identify which decisions the adaptive model made and which fixed operations were predefined; state whether the additional choices supplied a missing result in the observed attempt. Disclose changed evidence, different execution times and unknown served identities. Equal or equally successful responses are valid observations. One pair supports no general superiority, deployment choice or canonical-write authority.

Capture `03-fixed-adaptive-comparison.png` showing both final statuses, actual responses or their absence, separate human rubric/task judgments and resource observations with the continuation boundary visible. Preserve the screenshot and runtime files for the later report route. The report is completed in Student Step 6.

### Purpose

The student checks three application boundaries without another paid model call: an out-of-scope request must not execute, retained source text need not be delivered to the next model request, and an interrupted call must stop without becoming a refusal or a successful task result. The command uses the same permission, admission, request-construction and failure-handling code as the adaptive route, with explicitly injected transport returns. These are controlled diagnostics, not observations of additional live model choices.

### Student Step 5 — Check permission, delivery and honest stopping

Input: the completed first read at `reports/lab07/first-read/`. The command validates the retained capture against the unchanged synthetic source before diagnostics. If the actual first action did not produce `candidates returned`, preserve the actual result and record the blocked continuation; do not replace the action with a predicted read to obtain a passing diagnostic.

From the `training-project` directory, the student runs the same command on Windows, Linux and macOS:

```text
uv run learning-project lab07 check-boundaries --first-action-dir reports/lab07/first-read --output-dir reports/lab07/boundaries
```

The output directory must not already contain `attempt.json`, `summary.json` or any of the three diagnostic subdirectories. Existing outputs stop the command before input replay or transport use; the student preserves those outputs rather than overwriting them. A diagnostic failure stops continuation, preserves completed files and requires recording the observed error and missing result instead of assuming the boundary passed.

The student inspects the following cases in order:

1. **Permission denial.** `denial/decision-1/action.json` contains the injected `canonical write` request. `denial/decision-1/trace.json` must show `permission.allowed` as `false`, `executed input` as `null` and `returned result` as `null`. `denial/run-metadata.json` must report `permission denied`. The request is preserved but no canonical-write operation exists or executes. Rejection does not imply execution or a response-quality failure.
2. **Retained versus delivered source text.** The diagnostic injects a permitted retrieval request so the check does not depend on the live query having returned both passages. The application performs the local read; the second injected choice proposes stopping. This controlled read is not an extra retrieval in the adaptive/fixed comparison. `delivery/attempt.json` declares a controlled 150-character source-text budget, deliberately different from the normal comparison's 600 characters.

   `delivery/decision-2/selection-record.json` admits AP-1 and excludes AP-2 under the inherited admission criteria. AP-2 remains in `delivery/retained-state.json`, but its text must be absent from the entire `delivery/decision-2/request.json`, including quoted task-progress data. The student checks that the request's `supplied source evidence` matches the admitted evidence. The stop return is injected; no inference about a live model's next choice or answer quality follows. Do not use this diagnostic budget as a third comparison condition or replace the earlier adaptive/fixed captures.
3. **Honest stopping.** `interrupted/decision-1/provider-response.json` records a deliberately injected `TimeoutExpired` and a controlled partial return. `interrupted/run-metadata.json` must report `execution failure`, one injected transport invocation and `task_accomplishment` as `not judged`. No second decision, valid action or generated explanation/refusal is produced. This is not a newly observed provider outage; the diagnostic exercises the existing stop-and-preserve behavior without automatic retry.

`boundaries/attempt.json` identifies controlled diagnostic evidence and preserves the validated first read and synthetic source. `boundaries/summary.json` must report `permission_denial`, `retained_versus_delivered` and `honest_stop` as `passed`, with `live_provider_invocations` equal to zero. A passing summary means the three application checks behaved as specified, not that the explanation task was accomplished or the whole laboratory is complete. Counts in the nested metadata describe injected transport invocations, not paid provider calls.

Capture `04-boundary-checks.png` immediately after the diagnostic command and inspection. Show the permission denial without execution, AP-2 retained but omitted from the next request, the injected interruption and summary, or the actual diagnostic error. The operating-system or GitHub account and system date must be visible. A screenshot of a failed started checkpoint records failure rather than manufacturing the expected result.

The student preserves every diagnostic file and records the distinctions among request, permission, execution, delivery, model refusal and execution failure in the report. The normal adaptive and fixed responses remain subject to independent human judgment under the previously frozen comparison basis.

If the command itself fails before a summary is written, the student keeps the existing directory and records the exact command, error, last completed check and unperformed work. A missing summary is not a pass; a failed diagnostic is not converted into a refusal, a successful comparison or a complete laboratory.

### Student Step 6 — Validate, bind and prepare the report

The student completes the report from actual artifacts and independent judgments before the final commit. Preserve all existing files under `first-read/`, `adaptive/`, `fixed/` and `boundaries/`, including raw responses and failed attempts. For `complete`, all four execution checkpoints, human comparisons and required runtime files must be present. Report completion does not mean that every model response passed or the original question was answered. Human response/task judgments remain in the report; never change automated `not performed`/`not judged` metadata.

For a stopped or unfinished route, set `Статус завершення` to `honest-partial`, describe the exact command, observed problem, last completed action and missing results under `### Межа зупинки`, and retain all available files. Keep screenshot links/files for every started runtime directory and final verification; remove only links for checkpoints not started. The verifier may confirm an honestly partial committed record without claiming domain completion. No model rerun or replacement capture is required to make the partial record look complete.

Before the final commit, the source report describes the purpose of final verification and refers to its separate future JSON/image; do not predict a successful result. Both platforms run report validation before staging:

```text
uv run learning-project lab07 validate-report --report-dir reports/lab07
git diff --check
git status --short
git add reports/lab07
git commit -m "Complete Laboratory 07 report"
```

Continue only when source validation passes. The student commits the source report, reached checkpoint screenshots and all available machine evidence. The course-owned `cases/lab07/accessible-passages.json` must remain unchanged and already tracked in that repository. Never substitute a source-baseline digest for the final student commit.

Windows PowerShell — verify the exact current branch head:

```powershell
$finalCommit = (git rev-parse HEAD).Trim()
uv run learning-project lab07 verify --report-dir reports/lab07 --final-commit $finalCommit
whoami
Get-Date
```

Linux and macOS — verify the exact current branch head:

```bash
final_commit=$(git rev-parse HEAD)
uv run learning-project lab07 verify --report-dir reports/lab07 --final-commit "$final_commit"
whoami
date
```

The student inspects `reports/lab07/verification-report.json` and captures `05-final-verification.png` now, with the command, full hash, outcome, account and date visible. Do not commit this post-commit screenshot or the verification JSON and do not edit committed evidence afterwards. An existing verification output is create-only. A failed verification is preserved as an actual failure; it does not license an automatic repeat or a successful-completion claim.

A passing verifier confirms source-report structure, exact branch/HEAD binding, committed source and evidence bytes, and, for `complete`, consistency with readonly replay of captured responses and controlled diagnostics. Replay makes no new provider calls. The verifier does not grade the human's response judgments, independently attest served provider/model identity or prove task accomplishment. Missing images required before final verification, untracked/ignored inputs, changed/deleted source or evidence, incorrect branch/head, or inconsistent captures block successful verification.

After final verification and its screenshot, the student uses the shared submission command:

```text
uv run learning-project prepare-report reports/lab07/REPORT.md --max-width 1800 --max-height 1800
```

The explicit 1800-pixel bounds preserve the readable detail of the checkpoint images within that size; inspect the generated copy before submission. The generated `reports/lab07/submission/REPORT.md` embeds the reached images. The source report keeps relative image links. The generated copy is ignored by the shared project rule and is not committed. If packaging fails, preserve the exact error and do not claim that a standalone report was produced.

## Submission artifacts

Submit according to [Laboratory standing rules](../../LABORATORY_STANDING_RULES.md). Attach these files individually to the corresponding Microsoft Teams assignment, not an archive or repository link:

- `reports/lab07/submission/REPORT.md` — generated standalone Ukrainian narrative report.
- `reports/lab07/verification-report.json` — actual exact final-commit verification, including a failed outcome when observed.
- `reports/lab07/boundaries/summary.json` — bounded diagnostic result, only when that file was actually produced.
- `reports/lab07/screenshots/05-final-verification.png` — separate actual post-commit verification screenshot.

All other reached screenshots are embedded in the Teams report; complete runtime evidence remains committed on the personal branch. For `honest-partial`, never fabricate a missing diagnostic summary; describe its absence in the report. The fork URL/personal branch are in the source report and the full final hash is in verification JSON. A generated attachment or passing structural check does not authorize publication, canonical writes or general superiority claims.

## Control questions

1. Under the module's selected convention, what makes the observed route model-directed rather than merely a predefined workflow? Why do repeated model calls not by themselves constitute a **multi-agent system**?
2. Which actual fields distinguish a requested action, application permission and executed operation? Why does an action request not grant canonical-write authority?
3. Which delivered observation informed the next action in the actual attempt? What remains unknown when the application limit ends continuation without another request?
4. Which AP-2 text was retained but not delivered in the controlled check? Why does retained information or quoted progress not automatically become **supplied source evidence**?
5. Which application performs **agent operation orchestration**, and what additional coordination benefit would justify task delegation to several **agents** under these constraints?
6. How do response quality, original-task accomplishment and execution status differ? Which resource quantities were measured, partially reported or unknown, and what can one independently timed comparison not establish?

## Optional extensions

- Propose a different public or synthetic question on paper, identifying an initial evidence gap, permitted operations and a stopping condition without modifying the supplied corpus or making another paid call.
- Describe a task division that could justify several interacting **agents**, including the expected coordination cost and permission boundary. No MAS implementation or deployment is required.
