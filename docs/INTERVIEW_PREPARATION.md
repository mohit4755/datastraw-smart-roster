# Interview preparation — simple professional English

Use these answers after reading and running the code. Do not claim personal understanding until you can explain and demonstrate it. AI-assisted development is explicitly allowed in the assessment. Say what you reviewed and tested; do not claim that you independently wrote every line.

## 30-second introduction

“I am Mohit Vijay Wankhede, an MCA student at ASM's IBMR, Pune. My project is a Smart Roster Management System for employees working across brands and processes. I used React, FastAPI and OR-Tools CP-SAT. It considers calendars, leave, comp-offs, weekly offs and staffing needs. It reports shortages instead of silently breaking rules. I used AI assistance and focused on understanding the data model, validating constraints and testing the important workflows.”

## Two-minute project explanation

“The problem is monthly staffing for several brands with different schedules. A brand may operate on public holidays, while another closes on Sundays and holidays. Some brands have one employee handling multiple processes, while others have a small team.

I separated employees, pods, pod leads, brands, processes, demands and absences. A demand connects a brand and process with eligible employees and a staffing requirement. A brand calendar is different from an employee's availability. The sample has 33 fictional employees and 25 brands, with 80 percent of brands using a single dedicated resource.

The frontend uses React and TypeScript. It sends JSON requests to FastAPI. Pydantic validates input and SQLAlchemy saves changes in a transaction. The assessment version stores one workspace document. It is simple and atomic, but I would normalize it for larger scale.

The solver creates assignment variables only for eligible employees. It prevents incompatible brand shifts on the same day, respects approved absences and limits monthly work. It maximizes coverage first, then balances workload. A single employee may cover several compatible processes within one brand shift; this still counts as one working day.

An independent validator checks every generated or edited roster. Shortages remain visible. When leave changes after generation, retrieval recalculates conflicts and coverage. Manual changes use a preview and revision number. I can explain the executed tests from the test report. Deployment and browser checks must be described using their real status, not assumed success.”

## Five-minute walkthrough

- **Minute 1: problem and relationships.** Open employees and assignments. Explain employee → pod, pod → lead, employee → process skills, demand → brand/process/employee pool. Show 80% single-resource sample.
- **Minute 2: frontend and backend.** Show form → api.ts fetch → `/api` route → Pydantic → transaction → JSON response. Explain loading, errors and reload.
- **Minute 3: optimization.** Open engine.py. Explain Boolean process assignment, brand-shift variable, calendar exclusion, at most one brand per day, work limits, coverage-first stage and fairness stage.
- **Minute 4: verification and changes.** Show validate(), a shortage, leave update impact and rejected manual edit. Explain `valid`, `coverage_optimal`, revisions and HTTP 409.
- **Minute 5: persistence, deployment and trade-offs.** Explain one JSON workspace row, PostgreSQL lock, local SQLite limitations, Vercel function/static routing, test evidence, absent Gemini and future normalization/audit work.

## Architecture in plain language

The browser is the interface. FastAPI is the controlled entry point. Pydantic checks the shape and range of requests. Reference validation checks relationships. The database transaction saves related changes together. CP-SAT searches for assignments. The independent validator checks the result. The browser displays both assignments and remaining problems.

A **hard constraint** is a rule that cannot be bypassed, such as approved leave or incompatible simultaneous brand shifts. A **soft objective** is something to improve, such as workload balance. A shortage is explicit unmet business demand; the system does not call a shortage-free or valid plan unless the evidence supports it. Configured weekly off is treated as mandatory in this version. A future preferred-off feature would require a separate preference field and penalty, rather than weakening approved availability.

## Questions and answers

1. **Why Python?** Python has strong validation, API and optimization libraries. OR-Tools provides a supported CP-SAT interface, and the business rules are readable.
2. **What is a Python virtual environment?** It keeps this project's dependencies separate from other projects. It helps reproduce local behavior.
3. **What is a set used for here?** IDs and weekday memberships should be unique. Sets make membership checks clear; the API serializes them as JSON lists.
4. **Why avoid mutable default lists?** Shared mutable defaults can leak state between objects. Pydantic `default_factory` creates a fresh collection.
5. **What is a context manager?** It handles setup and cleanup around a block. The database transaction context commits on success and rolls back on an exception.
6. **Why FastAPI?** It works naturally with typed Python models, validates inputs and produces OpenAPI documentation. Its endpoints are easy to integration-test.
7. **Why are scheduling endpoints synchronous?** CP-SAT and the database driver are synchronous. Declaring them async would not make CPU work non-blocking; FastAPI handles synchronous endpoints in its worker thread pool.
8. **What does Pydantic validate?** Types, required fields, ID ranges, weekdays, allowed absence statuses and date order. Relationship checks happen separately against stored data.
9. **Why HTTP 422?** The request is syntactically readable but fails input validation, such as an invalid month or malformed record.
10. **Why HTTP 409?** The request conflicts with existing state: duplicate IDs, invalid references, stale revisions or an edit that violates scheduling rules.
11. **What happens if the database fails?** The API returns a structured 503 response and logs the exception class without exposing connection secrets.
12. **How does React communicate with the backend?** The `api` helper uses fetch with JSON. It checks status codes and turns backend failures into visible UI errors.
13. **Why TypeScript?** It catches many mismatches between UI state, component inputs and expected API responses before a build succeeds. It does not replace runtime backend validation.
14. **What is React state used for?** It tracks page selection, loaded records, month, filters, form data, preview results, loading and errors.
15. **Why useEffect?** It loads configuration on mount and loads the selected month's roster when the month changes. User-triggered saves remain explicit event handlers.
16. **What frontend tests exist?** Tests cover navigation/rendering, employee form JSON, calendar/manual-preview gating and API errors. They mock fetch, so they do not prove real browser-to-database behavior.
17. **What is the database schema?** One `roster_workspace` table has an ID and JSON document. Collections inside the document hold the configuration and saved monthly rosters.
18. **Why not normalized tables?** The document simplifies atomic edits and impact analysis for this assessment scale. Its limitations are coarse locks, whole-document writes and application-level referential integrity. Normalization is an important next step.
19. **How are broken references prevented?** A transaction validates every related ID before committing. For example, a demand cannot reference an employee from a different pod or an unsupported process.
20. **How do transactions help?** If a validation error occurs after an attempted change, the entire transaction rolls back. The workspace does not keep a partially invalid update.
21. **How do you handle concurrent edits?** PostgreSQL locks the workspace row during the transaction. A roster revision also rejects a client saving against an outdated version.
22. **Is SQLite equivalent to PostgreSQL?** No. SQLite is convenient for local tests but does not provide the same row-level concurrency behavior. PostgreSQL-specific locking still needs hosted integration verification.
23. **What does CP-SAT solve?** It chooses true or false assignment variables under integer constraints and optimizes an objective. It can prove optimality or return a feasible solution within a time budget.
24. **What are the decision variables?** Process-assignment variables identify a date, employee and demand. Brand-shift variables link compatible same-brand processes and restrict the employee to one brand per day.
25. **How do you prevent double booking?** The sum of brand-shift variables for an employee/day is at most one. Duplicate identical slots are also rejected. Several same-brand processes are documented as one compatible shift.
26. **How do single-resource brands work?** Their demand pools contain one employee. If that employee is unavailable, the system reports the gap. It does not invent a backup or override approved leave.
27. **How do multi-resource brands work?** Each brand/process demand has its own pool and minimum requirement. Employees can share a process or handle different processes; all assignments still obey daily brand and availability rules.
28. **How do operating calendars differ from weekly offs?** A calendar says whether the business needs coverage. A weekly off says whether a particular employee can work. The business may remain open while the employee is off.
29. **How do process-specific rules work?** Brand rules define the outer calendar; a demand adds process weekday restrictions and holiday closure. A seven-value staffing vector can vary coverage from Monday through Sunday.
30. **How are leave and comp-offs handled?** Approved absence ranges exclude the employee. Pending or rejected records do not block generation. The kind distinguishes leave, comp-off and unavailability.
31. **Why two optimization stages?** Coverage has higher business priority than fairness. The first stage maximizes coverage. Only after that proof does the second stage fix coverage and improve workload balance.
32. **What does optimal mean?** The solver proved the objective cannot improve under this model. It does not mean the model covers every real-world business detail. A feasible result alone is not an optimality proof.
33. **Is generation deterministic?** One worker, a fixed seed and deterministic search limits improve reproducibility. Tests demonstrate repeatability for chosen cases. Different library versions or a wall-clock timeout can still affect output.
34. **Why an independent validator?** It protects the system from manual edits and modeling mistakes. A solver result is checked against explicit business rules before being treated as valid.
35. **What changes after new leave?** Existing assignments are retained for review, but validation recalculates conflicts and valid coverage. The manager can assign a qualified backup or regenerate; changes are not silently ignored.
36. **How do manual edits work?** The client sends a revision and complete proposed slot list. A preview reports problems without saving. The server rejects hard violations and any daily shortage that is newly created or worsened.
37. **What does workload mean?** It is the count of unique employee work dates. Two compatible processes within one brand shift count as one work day.
38. **How is Vercel configured?** The configuration builds the Python API and Vite static frontend. API routes are evaluated before the SPA fallback. PostgreSQL persists data outside the ephemeral function filesystem.
39. **What runtime risks need checking?** Native OR-Tools imports, total bundle size, memory, cold starts, solve duration, database network access and connection limits. Local tests do not prove production compatibility.
40. **Why not save to SQLite on Vercel?** Function filesystems are temporary and may be isolated across instances. Persistent state belongs in the hosted database.
41. **Where are secrets stored?** In server-side environment variables. They are excluded from Git. The optional admin token is supplied to the browser privately and retained only for that session.
42. **What did the testing actually verify?** I would quote the current test report exactly. Pytest covers API and scheduler behavior. Vitest covers selected UI behavior. Browser and production status must be stated separately.
43. **How would you add Gemini safely?** Send verified conflict facts to the server-side model call, label the output as advice and validate any proposed change with deterministic rules. Keep the app fully usable without the AI service.
44. **What would you change at twice the size?** Measure first, normalize storage, add indexes and audit versions, paginate APIs and test realistic larger solver instances. Move expensive generation to a controlled job workflow only if measurements justify it.
45. **What would you improve in one week?** Finish production and browser acceptance first, then normalized persistence and audit history, better rule forms, accessibility and targeted backup suggestions.

## Personal contributions and difficult decisions

A truthful answer is: “I used AI-assisted development to accelerate implementation. I am responsible for understanding the requirements, reviewing the generated code, running and interpreting the tests, checking the result and explaining its limitations.” Replace that with specific work you actually performed; do not claim a review or test you did not do yourself.

The most important decisions to practice explaining are: coverage before fairness; approved leave as a hard rule; bundled same-brand processes as one shift; independent validation; revisions on manual edits; a compact transactional workspace with clear scaling limits; and deferring optional AI until mandatory scheduling works.

Practice: open a test, predict its result, run it, then explain why. Use Marathi for your private first explanation if helpful: **hard constraint = मोडता न येणारा नियम; shortage = आवश्यक कर्मचाऱ्यांची कमतरता; trade-off = एका फायद्यासाठी स्वीकारलेली मर्यादा.** Then repeat the answer in the simple English used above.
