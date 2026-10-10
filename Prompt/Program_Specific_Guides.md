# Program-Specific Code Review Guides

## VMDZ1526 (UPDATE Program - High Priority)

### Program Profile
- **Type:** UPDATE (INSERT/UPDATE operations)
- **Complexity:** High (Restart logic, multi-table updates)
- **Critical Checks:** CHK-01,05,08,09,10,11,13,14,20,21,22,23
- **Estimated Time:** 2 hours (Comprehensive)
- **Pass Rate Target:** 24/25 checks

### Focus Areas for VMDZ1526
1. **Restart Table (CHK-13)** - MUST have DZ01RSTV
   - Verify INCLUDE DZ01RSTV present
   - Check restart record initialization in 100-series
   - Verify restart record updated before each 700-series operation
   - Confirm checkpoint save interval logic

2. **Cursor Operations (CHK-10)** - If multi-row update
   - Check DECLARE CURSOR syntax
   - Verify OPEN/FETCH/CLOSE flow
   - Validate cursor EOF flag (e.g., DZBEFFC1-EOC, DZEVEFC1-EOC)
   - Ensure PERFORM...UNTIL includes cursor condition

3. **Transaction Control (CHK-11)** - Critical
   - COMMIT after successful batch update (NOT in loop)
   - ROLLBACK in error handlers
   - Verify restart record written before COMMIT

4. **SQLCODE Handling (CHK-09)** - After INSERT/UPDATE
   - Check for 0 (success), 100 (not found), negatives (errors)
   - Verify error message includes record key and operation

---

## VMDZ1567 (UPDATE Program - High Priority)

### Program Profile
- **Type:** UPDATE (specialized operations)
- **Complexity:** High
- **Critical Checks:** CHK-01,05,08,09,10,11,13,14,20,21,22,23
- **Estimated Time:** 2 hours (Comprehensive)
- **Pass Rate Target:** 24/25 checks

### Focus Areas for VMDZ1567
1. **Restart Table (CHK-13)** - MUST have DZ01RSTV
   - Same checks as VMDZ1526
   - Verify specialized restart fields populated

2. **IDMS-to-DB2 Conversion (CHK-14)**
   - Check OBTAIN → SELECT conversion
   - Verify STORE → INSERT mapping
   - Ensure MODIFY → UPDATE with proper WHERE clause

3. **Error Recovery (CHK-22)**
   - Verify program can resume from checkpoint
   - Check error logging includes restart point info

---

## VMDZ4302 (Dual Cursor Retrieval - Medium Priority)

### Program Profile
- **Type:** Retrieval (multi-cursor fetch)
- **Complexity:** Medium (Two concurrent cursors)
- **Critical Checks:** CHK-01,05,08,09,10,14,18,19,20,21,22
- **Estimated Time:** 90 minutes (Comprehensive)
- **Pass Rate Target:** 22/25 checks

### Focus Areas for VMDZ4302
1. **Multiple Cursors (CHK-10)** - MAIN FOCUS
   - Verify two cursor names: CURSOR-... and CURSOR-...
   - Check both cursors declared correctly
   - Ensure proper OPEN/FETCH/CLOSE for each cursor
   - Critical: PERFORM...UNTIL with proper cursor EOF logic
   - Verify cursor names match DCLGEN record mappings

2. **Cursor EOF Flags (CHK-10)**
   - First cursor EOF: DZBEFFC1-EOC (or similar)
   - Second cursor EOF: DZEVEFC1-EOC (or similar)
   - Both flags properly initialized in 100-series
   - Both flags set when cursor closes or NOT FOUND

3. **Nested Loops (CHK-19)**
   - Verify outer loop controlled by Cursor1
   - Inner loop controlled by Cursor2
   - No loop crossing or skipping

---

## VMDZ4310 (Retrieval Program - Medium Priority)

### Program Profile
- **Type:** Retrieval (single-table SELECT)
- **Complexity:** Low-Medium
- **Critical Checks:** CHK-01,05,06,07,08,09,10,18,19,20
- **Estimated Time:** 45 minutes (Standard)
- **Pass Rate Target:** 23/25 checks

### Focus Areas for VMDZ4310
1. **Copybook Mapping (CHK-06,07)**
   - Verify COPY VMBD510I and related copybooks
   - Check EXEC SQL INCLUDE statements for data records

2. **SELECT with WHERE (CHK-08,09)**
   - Ensure WHERE clause present (not full table scan)
   - Verify SQLCODE checking post-SELECT
   - Check for 0 (success) and 100 (NOT FOUND) handling

3. **Error Handling (CHK-09)**
   - Simple error path (log error, return code, exit)

---

## VMDZ4420 (Retrieval Program - Medium Priority)

### Program Profile
- **Type:** Retrieval (multi-column retrieval)
- **Complexity:** Low-Medium
- **Critical Checks:** CHK-01,05,06,07,08,09,10,18,19,20
- **Estimated Time:** 45 minutes (Standard)
- **Pass Rate Target:** 23/25 checks

### Focus Areas for VMDZ4420
1. **COPY Statements (CHK-06)**
   - Verify COPY ESDATMAS present and used correctly
   - Ensure copybook fields properly referenced in SQL

2. **DB2 Integration (CHK-08,09)**
   - Verify SELECT statement properly formatted
   - Check DZBEFFTV, DZEVEFTV includes present
   - Validate SQLCODE handling (especially 100)

---

## VMDZ7200 (Retrieval Program - Medium Priority)

### Program Profile
- **Type:** Retrieval (table lookup)
- **Complexity:** Low
- **Critical Checks:** CHK-01,05,06,07,08,09,10,18,19,20
- **Estimated Time:** 45 minutes (Standard)
- **Pass Rate Target:** 23/25 checks

### Focus Areas for VMDZ7200
1. **COPY Mapping (CHK-06)**
   - Verify COPY VMBZ270I (renamed from VMBD270I)
   - Check conversion from BD to DZ prefix correct

2. **Simple SELECT (CHK-08)**
   - Verify SELECT is straightforward (single table)
   - No complex JOINs that might have translation issues

3. **Initialization (CHK-20)**
   - Verify program state properly initialized
   - No carryover from previous run

---

## Cross-Program Review Patterns

### Pattern 1: UPDATE Programs (VMDZ1526, VMDZ1567)
**Common Issues to Watch:**
- Missing or incomplete DZ01RSTV
- COMMIT inside loop
- Cursor EOF flag not set properly
- Restart record not written

**Extra Focus:**
- CHK-13 (Restart Table) - CRITICAL
- CHK-11 (Transaction Control) - CRITICAL
- CHK-10 (Cursor Operations) - If multi-row

### Pattern 2: Multi-Cursor Programs (VMDZ4302)
**Common Issues to Watch:**
- Cursor EOF flags not distinct
- Cursor opening/closing in wrong order
- Loop condition references wrong cursor EOF
- Inner loop doesn't reset for next outer iteration

**Extra Focus:**
- CHK-10 (Cursor Operations) - CRITICAL
- CHK-19 (Perform Logic) - CRITICAL

### Pattern 3: Simple Retrieval (VMDZ4310, VMDZ4420, VMDZ7200)
**Common Issues to Watch:**
- WHERE clause missing (accidental full table scan)
- SQLCODE = 100 treated as error
- No error recovery path

**Extra Focus:**
- CHK-08,09 (SQL & SQLCODE) - CRITICAL
- CHK-20 (Initialization) - Important

---

## Common Issues to Watch Across All Programs

| Issue | Check | Programs Affected | Fix |
|-------|-------|-------------------|-----|
| DCLGEN member name wrong (BD vs DZ) | CHK-06,07 | All 6 | Use DZ prefix |
| Missing SQLCA INCLUDE | CHK-07 | All 6 | Add EXEC SQL INCLUDE SQLCA once |
| SQLCODE = 100 treated as error | CHK-09 | All 6 | Separate NOT FOUND from error |
| PERFORM...UNTIL cursor EOF missing | CHK-10 | VMDZ4302, VMDZ1526/67 | Add cursor EOF condition |
| Date field wrong PIC clause | CHK-17 | All 6 | Use PIC 9(8) for YYYYMMDD |
| Variable initialized wrong type | CHK-20 | All 6 | Numeric→0, Alpha→SPACES, Flags→'N' |
| No error logging in error path | CHK-22 | All 6 | Add INFO/ERROR log statements |
| Paragraph names too generic | CHK-18 | All 6 | Use descriptive names with numeric prefix |

---

## Review Checklist Prioritization

### Phase 1: Critical Path (30 min)
- [ ] CHK-01: Program ID correct (matches VMDZ####)
- [ ] CHK-08: EXEC SQL blocks properly formatted
- [ ] CHK-09: SQLCODE checking present
- [ ] CHK-13: Restart table present (UPDATE only)
- [ ] CHK-20,21: Initialization and termination

### Phase 2: Data & SQL (45 min)
- [ ] CHK-04: Variable types correct (PIC clauses)
- [ ] CHK-06,07: Copybooks and DCLGEN includes
- [ ] CHK-10: Cursor operations (multi-row)
- [ ] CHK-14: IDMS→DB2 conversion patterns
- [ ] CHK-17: Date/time field format

### Phase 3: Quality & Standards (45 min)
- [ ] CHK-15,16: Record structures and naming
- [ ] CHK-18,19: Paragraph organization
- [ ] CHK-22,23: Error handling and logging
- [ ] CHK-24: Performance (no full table scans)
- [ ] CHK-25: Documentation

---

## Questions to Ask When Reviewing

1. **Can you explain this PERFORM...UNTIL logic?**
   - If hesitation: CHK-19 issue likely

2. **Where is the restart record written?**
   - If UPDATE program and no clear answer: CHK-13 issue

3. **What happens when SQLCODE = 100?**
   - If treated as error: CHK-09 issue

4. **How are the two cursors managed?**
   - If logic unclear: CHK-10 issue (multi-cursor programs)

5. **When is the transaction committed?**
   - If answer is "inside loop": CHK-11 issue
