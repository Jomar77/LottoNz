"""Schema validator for the predictions.json document (single source of truth).

The human-readable contract lives in ``backend/docs/predictions_contract.md``.
This module encodes it as :func:`validate_predictions_document`, which returns a
list of human-readable error strings (empty list == valid). The frontend mirrors
this contract via the TypeScript types in ``frontend/src/types.ts``.

The doc file is the authority; this validator and the TS types must not diverge
from it.
"""

from __future__ import annotations

from datetime import datetime, timezone

MAIN_NUMBERS_PER_SET = 6
MAIN_MIN, MAIN_MAX = 1, 40
POWERBALL_MIN, POWERBALL_MAX = 1, 10

ALLOWED_STRATEGIES = (
    "burst_volatility",
    "mean_reversion",
    "momentum_carry",
    "balanced_hybrid",
    "lean_bias",
)

REQUIRED_METADATA_KEYS = (
    "total_draws_analyzed",
    "date_range",
    "uniformity_confirmed",
    "chi_square_p_main",
    "chi_square_p_powerball",
)


def _is_int(value) -> bool:
    """True for genuine ints (bool is a subclass of int — exclude it)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_iso_utc(value) -> bool:
    if not isinstance(value, str) or not value:
        return False
    text = value.replace("Z", "+00:00") if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return False
    # Must be timezone-aware and represent UTC.
    return parsed.tzinfo is not None and parsed.utcoffset() == timezone.utc.utcoffset(None)


def _validate_set(s, index: int) -> list[str]:
    label = f"sets[{index}]"
    errors: list[str] = []

    if not isinstance(s, dict):
        return [f"{label}: must be an object"]

    if not _is_int(s.get("id")):
        errors.append(f"{label}.id: must be an int")

    strategy = s.get("strategy")
    if strategy not in ALLOWED_STRATEGIES:
        errors.append(
            f"{label}.strategy: must be one of {ALLOWED_STRATEGIES}, got {strategy!r}"
        )

    mains = s.get("main_numbers")
    if not isinstance(mains, list):
        errors.append(f"{label}.main_numbers: must be a list")
    else:
        if len(mains) != MAIN_NUMBERS_PER_SET:
            errors.append(
                f"{label}.main_numbers: must contain exactly {MAIN_NUMBERS_PER_SET} numbers, got {len(mains)}"
            )
        if not all(_is_int(n) for n in mains):
            errors.append(f"{label}.main_numbers: all entries must be ints")
        else:
            if any(n < MAIN_MIN or n > MAIN_MAX for n in mains):
                errors.append(
                    f"{label}.main_numbers: all entries must be within {MAIN_MIN}-{MAIN_MAX}"
                )
            if len(set(mains)) != len(mains):
                errors.append(f"{label}.main_numbers: must not contain duplicates")
            if mains != sorted(mains):
                errors.append(f"{label}.main_numbers: must be sorted ascending")

    pb = s.get("powerball")
    if not _is_int(pb):
        errors.append(f"{label}.powerball: must be an int")
    elif pb < POWERBALL_MIN or pb > POWERBALL_MAX:
        errors.append(
            f"{label}.powerball: must be within {POWERBALL_MIN}-{POWERBALL_MAX}, got {pb}"
        )

    rationale = s.get("rationale")
    if not isinstance(rationale, str) or not rationale.strip():
        errors.append(f"{label}.rationale: must be a non-empty string")

    return errors


def _validate_metadata(meta) -> list[str]:
    if not isinstance(meta, dict):
        return ["metadata: must be an object"]

    errors: list[str] = []
    for key in REQUIRED_METADATA_KEYS:
        if key not in meta:
            errors.append(f"metadata.{key}: missing")

    if "total_draws_analyzed" in meta and not _is_int(meta["total_draws_analyzed"]):
        errors.append("metadata.total_draws_analyzed: must be an int")
    if "date_range" in meta and (
        not isinstance(meta["date_range"], str) or not meta["date_range"].strip()
    ):
        errors.append("metadata.date_range: must be a non-empty string")
    if "uniformity_confirmed" in meta and not isinstance(meta["uniformity_confirmed"], bool):
        errors.append("metadata.uniformity_confirmed: must be a bool")
    for pkey in ("chi_square_p_main", "chi_square_p_powerball"):
        if pkey in meta:
            val = meta[pkey]
            if not _is_number(val):
                errors.append(f"metadata.{pkey}: must be a float")
            elif val < 0.0 or val > 1.0:
                errors.append(f"metadata.{pkey}: must be within 0.0-1.0, got {val}")

    return errors


def validate_predictions_document(doc) -> list[str]:
    """Validate a predictions document against the contract.

    Returns a list of human-readable error strings; an empty list means the
    document is valid.
    """
    if not isinstance(doc, dict):
        return ["document: must be an object"]

    errors: list[str] = []

    if "draw_reference" not in doc:
        errors.append("draw_reference: missing")
    elif not _is_int(doc["draw_reference"]):
        errors.append("draw_reference: must be an int")

    if "generated_at" not in doc:
        errors.append("generated_at: missing")
    elif not _is_iso_utc(doc["generated_at"]):
        errors.append("generated_at: must be an ISO-8601 UTC timestamp")

    if "sets" not in doc:
        errors.append("sets: missing")
    elif not isinstance(doc["sets"], list):
        errors.append("sets: must be a list")
    elif not doc["sets"]:
        errors.append("sets: must not be empty")
    else:
        for i, s in enumerate(doc["sets"]):
            errors.extend(_validate_set(s, i))

    if "metadata" not in doc:
        errors.append("metadata: missing")
    else:
        errors.extend(_validate_metadata(doc["metadata"]))

    return errors
