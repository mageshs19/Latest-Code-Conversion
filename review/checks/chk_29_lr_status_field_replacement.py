"""CHK-29 LR-STATUS field - replaced with cursor end-of-cursor logic.

Validates LR-STATUS field removal per lrf_conversion_rules.py:

1. LR-STATUS field usage eliminated (COPY IDMS SUBSCHEMA-LR-CTRL removed)
2. LR-STATUS comparisons replaced with SQLCODE = 100 checks
3. End-of-set status (0307) mapped to cursor SQLCODE checking
4. Record-not-found (0326) mapped to SQLCODE = 100 
5. Conversion comments document field replacement

Source: lrf_conversion_rules.py, cursor_flow_rules.py
"""

from __future__ import annotations

from review.engine import metadata as meta
from review.engine.check_base import CRITICAL, BOTH, Check
from review.standards import cobol_standards as std


class LRStatusFieldReplacementCheck(Check):
    CHECK_ID = "CHK-29"
    TITLE = "LR-STATUS field - replaced with cursor end-of-cursor logic"
    SEVERITY = CRITICAL
    APPLIES_TO = BOTH
    ORDER = 290

    def relevant(self, ctx, view) -> bool:
        """True when this program WAS a logical-record program.

        CORRECTION - the gate asked the wrong question.

        It fired only when LR-STATUS text SURVIVED, so a clean
        conversion and a program that never used LRF both SKIPped. The
        check could fail but could never meaningfully pass. Relevance is
        now evidence that LRF conversion HAPPENED; the criteria then
        assert that it finished.
        """
        upper = [l.logical.upper() for l in view.lines]
        return any(
            std.LRF_EXPANSION_MARKER in line
            or std.LR_STATUS_FIELD in line
            or std.LR_QUALIFIER in line
            or any(t in line for t in std.IDMS_STATUS_TOKENS)
            for line in upper
        )

    def not_relevant_reason(self) -> str:
        return "Program shows no sign of logical record usage."

    def review(self, ctx, view, record):
        code = [l for l in view.lines if not l.is_comment]

        # ---- 01 NO LR-STATUS IN EXECUTABLE CODE
        record.expect_none(
            "01",
            "No LR-STATUS field usage remains in generated output",
            [l for l in code if std.LR_STATUS_FIELD in l.logical.upper()],
        )

        # ---- 02 NO LR-CTRL COPYBOOK
        record.expect_none(
            "02",
            "COPY IDMS SUBSCHEMA-LR-CTRL directive removed",
            [
                l for l in code
                if any(t in l.logical.upper() for t in std.LR_CTRL_TOKENS)
            ],
        )

        # ---- 03 NO RESIDUAL IDMS STATUS TOKEN
        # The expander emits DB-END-OF-SET / DB-REC-NOT-FOUND /
        # DB-REC-FOUND as an intermediate form. They are CONDITION NAMES
        # declared by the copybook the converter removes, so any survivor
        # is undefined at compile time. Previously an unconditional ok().
        record.expect_none(
            "03",
            "No residual IDMS status token remains",
            [
                l for l in code
                if any(t in l.logical.upper() for t in std.IDMS_STATUS_TOKENS)
            ],
        )

        # ---- 04 THE STATUS TEST WAS CONVERTED, NOT DELETED
        upper = [l.logical.upper() for l in code]
        converted = any(
            any(t in line for t in std.SQLCODE_END_TESTS)
            or std.CURSOR_EOC_SUFFIX in line
            for line in upper
        )
        record.expect(
            "04",
            "End-of-set test converted to SQLCODE or an end-of-cursor flag",
            converted,
            note=(
                "No SQLCODE = 100 test and no -EOC flag found. The "
                "LR-STATUS test may have been removed rather than "
                "translated."
            ),
        )

        # ---- 05 THE CONVERSION IS DOCUMENTED
        documented = any(
            l.is_comment
            and (
                std.LRF_EXPANSION_MARKER in l.logical.upper()
                or std.LR_STATUS_FIELD in l.logical.upper()
            )
            for l in view.lines
        )
        record.expect(
            "05",
            "LR-STATUS replacement is documented in a comment",
            documented,
            note="No LRF or LR-STATUS audit comment found.",
        )