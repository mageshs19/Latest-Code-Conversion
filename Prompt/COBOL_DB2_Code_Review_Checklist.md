# COBOL DB2 Code Review Checklist

## Purpose
Comprehensive code review checklist for validating COBOL programs converted from IDMS to DB2, ensuring compliance with COBOL standard compilation and DB2 best practices.

**Applicable to:** 10-25 COBOL program files in conversion project  
**Review Scope:** Syntax, compilation, DB2 integration, data standards, error handling  
**Standards:** COBOL-85/2002, DB2 SQL, IDMS-to-DB2 conversion patterns

---

## A. COBOL Syntax & Compilation Standards (CHK-01 to CHK-05)

### CHK-01: Program Identification & Declaration
- [ ] IDENTIFICATION DIVISION present and properly formatted
- [ ] PROGRAM-ID matches file name (minus extension)
- [ ] AUTHOR, DATE-WRITTEN fields present or explicitly omitted
- [ ] No duplicate PROGRAM-ID definitions
- [ ] PROGRAM-ID follows naming convention: VM + derived name
- **Files to Check:** All 10-25 program files
- **Error Examples:** 
  - Missing IDENTIFICATION DIVISION
  - PROGRAM-ID doesn't match derived DB2 name

### CHK-02: Environment & Configuration
- [ ] ENVIRONMENT DIVISION present (if needed)
- [ ] INPUT-OUTPUT SECTION configured correctly
- [ ] FILE-CONTROL entries match file operations
- [ ] SELECT statements properly formatted
- [ ] No hardcoded file paths
- **Files to Check:** Programs with file I/O operations
- **Error Examples:**
  - Missing FILE-CONTROL for ACCEPT/DISPLAY
  - Malformed SELECT statements

### CHK-03: Data Division Structure
- [ ] FILE SECTION present (if needed)
- [ ] WORKING-STORAGE SECTION present
- [ ] LINKAGE SECTION present (if needed)
- [ ] Proper 01-level record definitions
- [ ] No orphaned variables without 01 parent
- [ ] Variables properly indented and organized
- **Files to Check:** All programs
- **Error Examples:**
  - 05-level variables without 01 parent
  - Missing WORKING-STORAGE SECTION

### CHK-04: Variable Declarations & Data Types
- [ ] All variables have appropriate PIC clauses
- [ ] USAGE CLAUSE used correctly (COMP, COMP-3, BINARY, etc.)
- [ ] Alphanumeric variables use PIC X(n)
- [ ] Numeric variables use PIC 9(n) or COMP variants
- [ ] Date/Time fields use proper format (PIC 9(8) for YYYYMMDD)
- [ ] FILLER clauses used appropriately
- [ ] No ambiguous REDEFINES without clear purpose
- **Files to Check:** All 10-25 programs
- **Error Examples:**
  - Numeric fields with X characters
  - Missing USAGE COMP for binary fields
  - Date fields with wrong picture clause

### CHK-05: Procedure Division Format
- [ ] PROCEDURE DIVISION present and properly declared
- [ ] Paragraphs and sections properly named
- [ ] Paragraph names follow convention (numeric prefix or descriptive)
- [ ] STOP RUN present at program end
- [ ] No unreachable code after STOP RUN
- [ ] Proper paragraph nesting (no crossing sections)
- **Files to Check:** All programs
- **Error Examples:**
  - Code after STOP RUN
  - Mismatched section/paragraph structure

---

## B. COPY & INCLUDE Statement Standards (CHK-06 to CHK-07)

### CHK-06: Copybook Inclusion
- [ ] All COPY statements at top of WORKING-STORAGE or FILE SECTION
- [ ] COPY statements use correct member names (DZ prefix for DB2 records)
- [ ] COPY IDMS statements present (SUBSCHEMA, IDMS-STATUS, etc.)
- [ ] No duplicate COPY statements
- [ ] Copybook dependencies resolved (no circular includes)
- [ ] COPY statements use "REPLACING" when needed
- **Files to Check:** All programs
- **Error Examples:**
  - COPY statement in middle of WORKING-STORAGE
  - COPY with wrong member name (e.g., BD prefix instead of DZ)
  - Duplicate COPY statements

### CHK-07: DB2 DCLGEN Includes
- [ ] EXEC SQL INCLUDE SQLCA present (once, at top)
- [ ] EXEC SQL INCLUDE for all data records (DZBEFFTV, DZEVEFTV, etc.)
- [ ] EXEC SQL INCLUDE for restart table (DZ01RSTV) for UPDATE programs
- [ ] EXEC SQL INCLUDE statements properly closed
- [ ] No orphaned INCLUDE statements
- [ ] Include member names match metadata mapping
- **Files to Check:** All DB2-enabled programs (especially UPDATE)
- **Error Examples:**
  - Missing SQLCA INCLUDE
  - INCLUDE with old copybook name (e.g., VMBEVEF instead of DZEVEFTV)
  - Duplicate INCLUDE statements

---

## C. DB2 SQL Integration (CHK-08 to CHK-12)

### CHK-08: EXEC SQL Blocks & Basic SQL
- [ ] All EXEC SQL statements properly opened (EXEC SQL) and closed (END-EXEC)
- [ ] No nested EXEC SQL blocks
- [ ] Host variables prefixed with colon (:) in SQL context
- [ ] SELECT statements have proper syntax (SELECT ... FROM ... WHERE ...)
- [ ] INSERT statements populate all required columns
- [ ] UPDATE statements have WHERE clause (prevent bulk updates)
- [ ] DELETE statements have WHERE clause (prevent bulk deletes)
- **Files to Check:** All programs with DB2 operations (10-25 files)
- **Error Examples:**
  - EXEC SQL without END-EXEC
  - Host variables without colon prefix
  - DELETE without WHERE clause

### CHK-09: SQLCODE & Error Handling
- [ ] SQLCODE checked after every EXEC SQL statement
- [ ] SQLCODE = 0 treated as success
- [ ] SQLCODE = 100 (NOT FOUND) handled separately
- [ ] Negative SQLCODE (errors) have recovery logic
- [ ] SQLCODE values documented (0, 100, -530, -407, etc.)
- [ ] Error messages logged with SQLCODE and SQLERRM context
- [ ] No silent failures (no SQLCODE 100 ignored)
- **Files to Check:** All DB2 programs (10-25 files)
- **Error Examples:**
  - SQLCODE checked only once at end
  - SQLCODE = 100 treated as error instead of NOT FOUND
  - Missing SQLCODE check after SELECT/INSERT/UPDATE

### CHK-10: Cursor Operations
- [ ] DECLARE CURSOR statements present for multi-row fetches
- [ ] CURSOR names follow naming convention (e.g., CURSOR-RECORDS)
- [ ] OPEN cursor before FETCH
- [ ] FETCH INTO host variables with proper mapping
- [ ] CLOSE cursor after FETCH loop completes
- [ ] PERFORM...UNTIL CURSOR-EOF or similar termination
- [ ] Cursor EOF flag properly initialized and set
- **Files to Check:** Programs with multi-row queries (VMDZ4302, etc.)
- **Error Examples:**
  - FETCH without OPEN
  - PERFORM...UNTIL without cursor EOF condition
  - Missing CLOSE cursor

### CHK-11: Transaction Control & Commit/Rollback
- [ ] EXEC SQL BEGIN TRANSACTION (or implicit)
- [ ] EXEC SQL COMMIT placed after successful operations
- [ ] EXEC SQL ROLLBACK placed in error handlers
- [ ] Commit/Rollback not in cursor FETCH loops
- [ ] Transaction scope matches business logic units
- [ ] No implicit commits hiding logic errors
- **Files to Check:** All UPDATE programs (VMDZ1526, VMDZ1567)
- **Error Examples:**
  - COMMIT inside FETCH loop
  - ROLLBACK without SQLCODE check
  - Missing ROLLBACK in error handler

### CHK-12: Prepared Statements & Dynamic SQL (if used)
- [ ] PREPARE statements use parameterized queries (not concatenation)
- [ ] EXECUTE with proper parameter mapping
- [ ] Parameter markers (?) used instead of literal values
- [ ] Dynamic SQL validated before execution
- [ ] No SQL injection vulnerabilities
- **Files to Check:** Programs with dynamic SQL (if any)
- **Error Examples:**
  - SQL built by string concatenation
  - Literal values in WHERE clause without parameters

---

## D. Restart Table & UPDATE Patterns (CHK-13 to CHK-14)

### CHK-13: Restart Table (DZ01RSTV) Standards for UPDATE Programs
- [ ] UPDATE programs include DZ01RSTV (restart table DCLGEN)
- [ ] Restart record populated with:
  - NM_ID_RS_PROGRAM (program name)
  - NB_ID_RS_PHASE (phase/step identifier)
  - DA_CR_RS (creation date)
  - TE_CH_RS_DATA (timestamp of last change)
  - CO_ID_RS (status code)
  - NB_DAY_RS (retention days)
- [ ] Restart record INSERT or UPDATE in 700-series paragraphs
- [ ] Restart record read before processing (for resume capability)
- [ ] Restart mechanism enables checkpoint/restart on failure
- **Files to Check:** UPDATE programs (VMDZ1526, VMDZ1567)
- **Error Examples:**
  - DZ01RSTV include missing
  - Restart record fields incomplete
  - Restart logic in business paragraph (should be separate)

### CHK-14: IDMS-to-DB2 Conversion Patterns
- [ ] IDMS OBTAIN statements converted to DB2 SELECT
- [ ] IDMS STORE statements converted to DB2 INSERT
- [ ] IDMS MODIFY statements converted to DB2 UPDATE
- [ ] IDMS ERASE statements converted to DB2 DELETE
- [ ] IDMS Set navigation (ALL-...-BY-...) converted to WHERE clauses
- [ ] VIA record clauses converted to JOIN or FK relationships
- [ ] CALC record access converted to WHERE primary key = value
- [ ] LRF (Logical Record Field) mappings validated
- **Files to Check:** All programs originally from IDMS (10-25 files)
- **Error Examples:**
  - OBTAIN not converted to SELECT
  - Set navigation lost in conversion
  - Missing JOIN for VIA record relationships

---

## E. Record & Data Mapping Standards (CHK-15 to CHK-17)

### CHK-15: Record Definitions & Structure
- [ ] All data records defined in WORKING-STORAGE with 01-level
- [ ] Record structure matches DCLGEN copybook
- [ ] Field order and alignment correct
- [ ] OCCURS clause used for arrays/tables
- [ ] DEPENDING ON clause for variable-length arrays
- [ ] No record holes or misaligned fields
- [ ] Record size calculated correctly
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - Record structure doesn't match copybook
  - Missing fields from DCLGEN
  - Misaligned OCCURS clauses

### CHK-16: Variable Naming Conventions
- [ ] Variables follow naming pattern:
  - First 2 chars: application prefix (VM, DZ, etc.)
  - Next 3-5 chars: descriptive name
  - Last 1-3 chars: type suffix (TV for table/view, REC for record, etc.)
- [ ] No abbreviated names without context
- [ ] Consistent naming across related programs
- [ ] Reserved words not used as variable names
- [ ] Underscore/hyphen usage consistent
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - Variable names like X, Y, TEMP (too generic)
  - Inconsistent prefixes (VM vs DZ mixed)
  - Reserved words used (MOVE, ACCEPT, etc.)

### CHK-17: Date & Time Handling
- [ ] Date fields use standard format (YYYYMMDD = PIC 9(8))
- [ ] Time fields use standard format (HHMMSS = PIC 9(6))
- [ ] Timestamp includes both date and time
- [ ] Date validation performed (valid month 01-12, day 01-31, etc.)
- [ ] Year 2000 compliance (4-digit year, not 2-digit)
- [ ] Leap year handling correct (Feb 29 only in leap years)
- [ ] Date arithmetic uses proper COBOL logic (no manual calculations)
- **Files to Check:** All programs with date fields (10-25 files)
- **Error Examples:**
  - 2-digit year (PIC 9(6) instead of 9(8))
  - Date validation missing
  - Hardcoded leap year logic

---

## F. Paragraph & Section Organization (CHK-18 to CHK-19)

### CHK-18: Paragraph Naming & Organization
- [ ] Paragraphs organized by function (MAIN, PROCESS, ERROR, etc.)
- [ ] Naming convention: [100-400]-[DESCRIPTIVE-NAME]
  - 100-series: Initialization/setup
  - 200-series: Main processing
  - 300-series: Retrieve/SELECT operations
  - 400-series: Update/INSERT/DELETE operations
  - 500-series: Utility/helper functions
  - 600-series: Error handling
  - 700-series: Cleanup/exit
  - 800-series: Restart/checkpoint logic (for UPDATE programs)
- [ ] No orphaned paragraphs
- [ ] Paragraph size reasonable (not too large, not trivial)
- [ ] Paragraph documentation (comment line at start)
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - Paragraph names like PARA1, PARA2 (non-descriptive)
  - Huge paragraph (500+ lines)
  - Missing 700-series cleanup

### CHK-19: Paragraph Calling & Perform Logic
- [ ] PERFORM statements properly reference paragraphs
- [ ] PERFORM...UNTIL conditions are testable and eventually true
- [ ] PERFORM...VARYING uses proper index/counter
- [ ] No infinite loops (PERFORM...UNTIL without changing condition)
- [ ] Inline PERFORM used only for simple operations
- [ ] Call hierarchy documented (which para calls which)
- [ ] No circular PERFORM dependencies
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - PERFORM...UNTIL loop with unchanging condition
  - Nested PERFORM...VARYING without proper iteration
  - Inline PERFORM with complex logic

---

## G. Initialization & Termination (CHK-20 to CHK-21)

### CHK-20: Variable Initialization
- [ ] All numeric fields initialized to 0 (or appropriate value)
- [ ] All alphanumeric fields initialized to SPACES
- [ ] Flags initialized before first use (typically to 'N' or OFF)
- [ ] Counter/index variables initialized before loops
- [ ] Array/table elements initialized or populated before access
- [ ] Working-storage values set in 100-series initialization paragraph
- [ ] ACCEPT statements immediately follow initialization logic
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - Variables used without initialization
  - SPACES used for numeric fields
  - Uninitialized flag causing logic error

### CHK-21: Program Termination & Cleanup
- [ ] 700-series cleanup paragraph executed before STOP RUN
- [ ] All open files CLOSED
- [ ] All open cursors CLOSED
- [ ] Restart table written with final status
- [ ] COMMIT or ROLLBACK executed (not left implicit)
- [ ] Error code set appropriately before exit
- [ ] Final status logged or reported
- [ ] No orphaned resources (unclosed files, connections)
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - STOP RUN without closing files
  - ROLLBACK in error path missing
  - Restart record not finalized

---

## H. Error Handling & Logging (CHK-22 to CHK-23)

### CHK-22: Error Handling Patterns
- [ ] Try-catch equivalent: IF SQLCODE < 0 or equivalent check
- [ ] Specific error codes handled (0, 100, -530, -407, -204, etc.)
- [ ] Error messages include context (file, operation, record key)
- [ ] Error handler prevents cascading failures
- [ ] WHEN OTHER or default case present for unexpected errors
- [ ] Error logging includes timestamp
- [ ] Graceful degradation (not hard stop on error)
- **Files to Check:** All DB2 programs (10-25 files)
- **Error Examples:**
  - No SQLCODE check after SQL operation
  - Generic error message without context
  - Hard stop on 100 (NOT FOUND) error

### CHK-23: Logging & Diagnostics
- [ ] Status/progress messages logged (INFO level)
- [ ] Warning messages for unusual conditions (WARNING level)
- [ ] Error messages with full context (ERROR level)
- [ ] Debug messages for development (DEBUG level, optional)
- [ ] Log output includes:
  - Timestamp (HHMMSS or YYYYMMDDHHMMSS)
  - Log level (INFO, WARNING, ERROR, DEBUG)
  - Module/paragraph name
  - Message text
  - Data context (key values, record counts, etc.)
- [ ] No hardcoded "DISPLAY" statements (use logging framework)
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - Hardcoded DISPLAY statements in production code
  - Log messages without timestamp
  - No differentiation of log levels

---

## I. Performance & Optimization (CHK-24)

### CHK-24: Performance Considerations
- [ ] SELECT statements include WHERE clause (no full table scans)
- [ ] Indexes used appropriately (PK in WHERE clause)
- [ ] JOINs necessary and optimized (no cartesian product)
- [ ] Cursor fetch loop avoids unnecessary operations inside loop
- [ ] Arrays/tables use OCCURS DEPENDING ON (not wasted storage)
- [ ] PERFORM...VARYING avoids nested loops when possible
- [ ] No redundant database queries
- [ ] Batch operations used for bulk inserts/updates (not row-by-row)
- [ ] String concatenation minimized in loops
- **Files to Check:** Programs with high-volume operations
- **Error Examples:**
  - SELECT without WHERE (fetches all rows)
  - Single INSERT in loop instead of batch
  - Redundant query inside loop

---

## J. Documentation & Standards (CHK-25)

### CHK-25: Code Documentation & Comments
- [ ] Program header comments (name, purpose, author, date, version)
- [ ] Section comments (purpose of 100-series, 200-series, etc.)
- [ ] Complex logic commented (regex, calculation, conversion)
- [ ] Variable definitions have inline comments (units, range, format)
- [ ] TODO comments for incomplete work
- [ ] Known issues/limitations documented
- [ ] No commented-out code (delete or document reason)
- [ ] Documentation kept current with code changes
- [ ] No sensitive data in comments (passwords, keys, etc.)
- **Files to Check:** All programs (10-25 files)
- **Error Examples:**
  - No program header
  - Cryptic variable names without comments
  - Outdated comments conflicting with code

---

## Review Process

### Quick Review (15 minutes per file)
Focus on: CHK-01, CHK-05, CHK-08, CHK-09, CHK-13

### Standard Review (45 minutes per file)
Focus on: CHK-01 through CHK-18

### Comprehensive Review (2 hours per file)
Focus on: All CHK-01 through CHK-25

### File Priority Order
1. **VMDZ1526** - UPDATE program (high priority) - CHK-01,02,03,04,05,08,09,10,11,13,14,20,21,22,23
2. **VMDZ1567** - UPDATE program (high priority) - CHK-01,02,03,04,05,08,09,10,11,13,14,20,21,22,23
3. **VMDZ4302** - Dual cursor (medium priority) - CHK-01,05,08,09,10,14,18,19,20,21,22
4. **VMDZ4310** - Retrieval (medium priority) - CHK-01,05,06,07,08,09,10,18,19,20
5. **VMDZ4420** - Retrieval (medium priority) - CHK-01,05,06,07,08,09,10,18,19,20
6. **VMDZ7200** - Retrieval (medium priority) - CHK-01,05,06,07,08,09,10,18,19,20

### Passing Criteria
- For **Critical Issues (CHK-01,05,08,09,13,20,21):** Must be 100% compliant
- For **Major Issues (CHK-02,03,04,06,07,10,11,14):** Maximum 1 issue per file
- For **Minor Issues (CHK-12,15,16,17,18,19,22,23,24,25):** Maximum 3 issues per file

### Reporting
Each file gets a review report showing:
- Total checks: 25
- Passed: X/25
- Failed: Y/25
- Critical failures: (CHK-01,05,08,09,13,20,21)
- Major failures: (CHK-02,03,04,06,07,10,11,14)
- Minor failures: Rest
