# Workflow: Bug Fix

## Handoff Sequence

```
USER reports bug → TECH LEAD (reproduces, creates Task File)
  → ENGINEER (fixes)
  → QA REVIEWER (verifies fix + writes regression test)
  → TECH LEAD (merges)
```

## Step 1: Tech Lead Triages

1. Reproduce the bug. Note exact inputs and wrong output.
2. Identify which module and layer contains the defect.
3. Create a Task File with:
   - Bug description and reproduction steps
   - Expected vs actual behavior
   - Context Bundle with relevant schema and API contract
   - Acceptance criteria: "The failing scenario now produces [expected result]"
   - Exit signal: the specific test that must pass

## Step 2: Engineer Fixes

1. Read the Task File.
2. Write a failing test that demonstrates the bug BEFORE fixing.
3. Make the minimum change to fix the bug.
4. Run the failing test — it should now pass.
5. Run full test suite — no regressions.
6. Report completion.

## Step 3: QA Reviewer Verifies

1. Review the fix: is it the root cause or just a symptom patch?
2. Verify the regression test covers the exact scenario.
3. Run full test suite.
4. Produce verdict.

## Step 4: Tech Lead Merges

Same merge protocol as any task.
