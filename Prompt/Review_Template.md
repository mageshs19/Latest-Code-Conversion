# Code Review Template - COBOL DB2 Programs

## Review Information
- **Program Name:** [PROGRAM NAME]
- **Program ID:** [VMDZ####]
- **Review Date:** [DATE]
- **Reviewer:** [NAME]
- **Review Type:** Quick / Standard / Comprehensive
- **Program Type:** Retrieval / Update / Utility

---

## 1. PROGRAM STRUCTURE (CHK-01 to CHK-05)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-01 | Program ID & Declaration | ☐ Pass ☐ Fail | |
| CHK-02 | Environment & Configuration | ☐ Pass ☐ Fail | |
| CHK-03 | Data Division Structure | ☐ Pass ☐ Fail | |
| CHK-04 | Variable Declarations & Types | ☐ Pass ☐ Fail | |
| CHK-05 | Procedure Division Format | ☐ Pass ☐ Fail | |

**Score:** ___ / 5

---

## 2. INPUT FILES & INCLUDES (CHK-06 to CHK-07)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-06 | Copybook Inclusion | ☐ Pass ☐ Fail | |
| CHK-07 | DB2 DCLGEN Includes | ☐ Pass ☐ Fail | |

**Score:** ___ / 2

---

## 3. RECORD & FIELD DEFINITIONS (CHK-08 to CHK-10)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-08 | Record Definitions & Structure | ☐ Pass ☐ Fail | |
| CHK-09 | Variable Naming Conventions (DB2) | ☐ Pass ☐ Fail | |
| CHK-10 | Hyphen vs Underscore Usage | ☐ Pass ☐ Fail | |

**Score:** ___ / 3

---

## 4. DATA TYPES & FORMATS (CHK-11 to CHK-14)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-11 | Date Field Format & Handling | ☐ Pass ☐ Fail | |
| CHK-12 | Timestamp Field Format | ☐ Pass ☐ Fail | |
| CHK-13 | Audit Fields (TS_UPDATE, ID_USERID) | ☐ Pass ☐ Fail | |
| CHK-14 | NULL Sentinel Values (0001-01-01) | ☐ Pass ☐ Fail | |

**Score:** ___ / 4

---

## 5. NAMING TRANSFORMATION (CHK-15 to CHK-16)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-15 | IDMS-to-DB2 Conversion Patterns | ☐ Pass ☐ Fail | |
| CHK-16 | Sheet Mapping Field Naming Applied | ☐ Pass ☐ Fail | |

**Score:** ___ / 2

---

## 6. SQL STATEMENTS & HOST VARIABLES (CHK-17 to CHK-18)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-17 | EXEC SQL Blocks & Basic SQL | ☐ Pass ☐ Fail | |
| CHK-18 | Host Variable Binding & Types | ☐ Pass ☐ Fail | |

**Score:** ___ / 2

---

## 7. SELECT OPERATIONS (CHK-19 to CHK-21)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-19 | SELECT Column Names Match DCLGEN | ☐ Pass ☐ Fail | |
| CHK-20 | INTO Host Variables Match Types | ☐ Pass ☐ Fail | |
| CHK-21 | FROM Clause Table Names | ☐ Pass ☐ Fail | |

**Score:** ___ / 3

---

## 8. WHERE CONDITIONS (CHK-22 to CHK-24)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-22 | WHERE Conditions Correctness | ☐ Pass ☐ Fail | |
| CHK-23 | WHERE Python Logic Mapping | ☐ Pass ☐ Fail | |
| CHK-24 | WHERE Conditions Valid Operators | ☐ Pass ☐ Fail | |

**Score:** ___ / 3

---

## 9. ORDER BY & SORTING (CHK-25 to CHK-26)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-25 | ORDER BY Clause (if used) | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-26 | ORDER BY Logic in Python | ☐ Pass ☐ Fail ☐ N/A | |

**Score:** ___ / 2

---

## 10. CURSOR OPERATIONS (CHK-27 to CHK-32)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-27 | Cursor DECLARE with SELECT | ☐ Pass ☐ Fail | |
| CHK-28 | Cursor OPEN Operation | ☐ Pass ☐ Fail | |
| CHK-29 | Cursor FETCH Logic (INTO clause) | ☐ Pass ☐ Fail | |
| CHK-30 | Cursor CLOSE & Resource Cleanup | ☐ Pass ☐ Fail | |
| CHK-31 | Cursor Loop SQLCODE Handling | ☐ Pass ☐ Fail | |
| CHK-32 | Duplicate Record Handling | ☐ Pass ☐ Fail | |

**Score:** ___ / 6

---

## 11. UPDATE & RESTART LOGIC (CHK-33 to CHK-39)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-33 | Restart Table Declaration (UPDATE) | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-34 | Restart Table DCLGEN Included | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-35 | Restart Status Initialization (0/1) | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-36 | Restart SELECT Logic & Conditions | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-37 | Restart Record FETCH & Check | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-38 | Restart Phase/Job Status Tracking | ☐ Pass ☐ Fail ☐ N/A | |
| CHK-39 | Restart INSERT/UPDATE to Restart Table | ☐ Pass ☐ Fail ☐ N/A | |

**Score:** ___ / 7 (or fewer if N/A)

---

## 12. TRANSACTIONS & CONTROL (CHK-40 to CHK-41)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-40 | Transaction Control (COMMIT/ROLLBACK) | ☐ Pass ☐ Fail | |
| CHK-41 | Prepared Statements (if used) | ☐ Pass ☐ N/A | |

**Score:** ___ / 2

---

## 13. ERROR HANDLING (CHK-42 to CHK-47)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-42 | SQLCODE & Error Handling Basics | ☐ Pass ☐ Fail | |
| CHK-43 | SQLCODE Error Checking (0, 100, -xxx) | ☐ Pass ☐ Fail | |
| CHK-44 | NOT FOUND (SQLCODE 100) Handling | ☐ Pass ☐ Fail | |
| CHK-45 | Error Logging & Messages | ☐ Pass ☐ Fail | |
| CHK-46 | Exception Handling Paths | ☐ Pass ☐ Fail | |
| CHK-47 | Return Codes & Status Flags | ☐ Pass ☐ Fail | |

**Score:** ___ / 6

---

## 14. CODE ORGANIZATION (CHK-48 to CHK-51)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-48 | Paragraph Naming Convention | ☐ Pass ☐ Fail | |
| CHK-49 | Paragraph Hierarchy & Nesting | ☐ Pass ☐ Fail | |
| CHK-50 | PERFORM Logic & Paragraph Calls | ☐ Pass ☐ Fail | |
| CHK-51 | Section Separation & Independence | ☐ Pass ☐ Fail | |

**Score:** ___ / 4

---

## 15. INITIALIZATION & CLEANUP (CHK-52 to CHK-55)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-52 | WORKING-STORAGE Initialization | ☐ Pass ☐ Fail | |
| CHK-53 | File/Cursor Handle Initialization | ☐ Pass ☐ Fail | |
| CHK-54 | Program Termination & STOP RUN | ☐ Pass ☐ Fail | |
| CHK-55 | Resource Cleanup (Cursors, Files) | ☐ Pass ☐ Fail | |

**Score:** ___ / 4

---

## 16. PERFORMANCE & OPTIMIZATION (CHK-56 to CHK-58)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-56 | Cursor Efficiency & Index Usage | ☐ Pass ☐ Fail | |
| CHK-57 | Query Optimization (MIN/MAX) | ☐ Pass ☐ Fail | |
| CHK-58 | Large Dataset Handling | ☐ Pass ☐ Fail | |

**Score:** ___ / 3

---

## 17. DOCUMENTATION & AUDIT (CHK-59 to CHK-61)

| Check | Item | Status | Notes |
|-------|------|--------|-------|
| CHK-59 | Code Documentation & Comments | ☐ Pass ☐ Fail | |
| CHK-60 | Python Workflow Comments | ☐ Pass ☐ Fail | |
| CHK-61 | Standards Compliance & Audit Trail | ☐ Pass ☐ Fail | |

**Score:** ___ / 3

---

## OVERALL RESULTS

| Metric | Result |
|--------|--------|
| **Total Checks** | 61 |
| **Passed** | ___ / 61 |
| **Failed** | ___ / 61 |
| **Compliance %** | __.__% |

---

## CRITICAL ISSUES (Must Fix)
**Checks**: CHK-01, CHK-05, CHK-17, CHK-42, CHK-28, CHK-29, CHK-30, CHK-33, CHK-35, CHK-36, CHK-37, CHK-39, CHK-15, CHK-16, CHK-52

| Issue # | Check | Description | Severity |
|---------|-------|-------------|----------|
| 1 | CHK-?? | [Description] | Critical |
| 2 | CHK-?? | [Description] | Critical |

**Total Critical Issues:** ___  
**Fixed:** [ ] Yes [ ] No

---

## MAJOR ISSUES (Max 2 per file)
**Checks**: CHK-02, CHK-03, CHK-04, CHK-06, CHK-07, CHK-27, CHK-22, CHK-23, CHK-08, CHK-09, CHK-48, CHK-49

| Issue # | Check | Description | Severity |
|---------|-------|-------------|----------|
| 1 | CHK-?? | [Description] | Major |
| 2 | CHK-?? | [Description] | Major |

**Total Major Issues:** ___  
**Fixed:** [ ] Yes [ ] No

---

## MINOR ISSUES (Max 5 per file)
**Checks**: CHK-25, CHK-26, CHK-31, CHK-32, CHK-10, CHK-11, CHK-12, CHK-13, CHK-14, CHK-50, CHK-51, CHK-53, CHK-54, CHK-55, CHK-43, CHK-44, CHK-45, CHK-46, CHK-47, CHK-56, CHK-57, CHK-58, CHK-19, CHK-20, CHK-21, CHK-24, CHK-59, CHK-60, CHK-61

| Issue # | Check | Description | Severity |
|---------|-------|-------------|----------|
| 1 | CHK-?? | [Description] | Minor |
| 2 | CHK-?? | [Description] | Minor |

**Total Minor Issues:** ___  
**Fixed:** [ ] Yes [ ] No

---

## REVIEW DECISION

- [ ] **APPROVED** - Production-ready
- [ ] **APPROVED WITH COMMENTS** - Minor recommendations
- [ ] **REJECTED** - Critical/Major issues must be fixed
- [ ] **CONDITIONAL** - Minor issues OK for follow-up

---

## REFERENCE WORKFLOWS

### Cursor Lifecycle
```cobol
DECLARE → OPEN → FETCH (loop) → CLOSE
  ↓        ↓        ↓              ↓
 CHK-27  CHK-28  CHK-29,31      CHK-30
         Check   SQLCODE=100
         SQLCODE Check status
```

### WHERE Condition Transform
```
COBOL:    "03 NB-FA = :input"
   ↓ canonical_field_key("NB-FA") → "NBFA"
Lookup:   Sheet Mapping "NBFA" → "NB_FA"
   ↓ replace hyphens
SQL:      "WHERE NB_FA = ?" ← CHK-22, CHK-23, CHK-24
```

### Restart Phases (UPDATE Only)
```
Phase 1: SELECT existing records
Phase 2: UPDATE records in DB2
Phase 3: INSERT new records
   ↓ cycle repeats if job restarts (CHK-33 to CHK-39)
```

---

## Recommendations

### Positive Observations
- [What went well]

### Areas for Improvement
- [Specific recommendations]

### Follow-up Actions
- [ ] Action: [Description] - Owner: [Name] - Due: [Date]

---

## Sign-Off

**Reviewer:** _________________________ **Date:** _______________

**Program Lead:** _________________________ **Date:** _______________

---

## Review History

| Date | Reviewer | Result | Notes |
|------|----------|--------|-------|
| | | APPROVED / REJECTED | |
