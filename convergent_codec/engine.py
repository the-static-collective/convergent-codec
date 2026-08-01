"""Candidate generation, engine-owned verification and cost measurement, selection by emitted length."""

import hashlib
from dataclasses import dataclass
from typing import List, Optional
from .models import raw, periodic_sparse
from .frames import deserialize, Family
from .canonical import source_sha256, require_int32
from .errors import CodecFormatError
from .witness import WitnessLedger, ProposalDisposition
from .limits import MAX_SAMPLES_PER_FRAME


@dataclass(frozen=True)
class Candidate:
    family: Family
    frame: bytes
    exact_bits: int
    reconstructed_sha256: bytes
    evidence: dict


def _frame_sha256(frame: bytes) -> str:
    return hashlib.sha256(frame).hexdigest()


def encode(values: List[int], ledger: Optional[WitnessLedger] = None) -> Candidate:
    require_int32(values)
    if len(values) > MAX_SAMPLES_PER_FRAME:
        raise CodecFormatError("sample count exceeds format limit")
    source_digest = source_sha256(values)
    candidates: List[Candidate] = []

    def try_proposal(prop: Optional[dict], family_name: str) -> None:
        if prop is None:
            if ledger is not None:
                ledger.record(family_name, ProposalDisposition.NO_PROPOSAL, "no_proposal")
            return
        frame = prop["frame"]
        try:
            decoded, fam = deserialize(frame)
            if decoded != values:
                if ledger is not None:
                    ledger.record(
                        family_name, ProposalDisposition.REJECTED, "decode_mismatch",
                        emitted_bits=len(frame)*8, frame_sha256=_frame_sha256(frame),
                        evidence=prop.get("evidence"),
                    )
                return
            actual_digest = source_sha256(decoded)
            if actual_digest != source_digest:
                if ledger is not None:
                    ledger.record(
                        family_name, ProposalDisposition.REJECTED, "digest_mismatch",
                        emitted_bits=len(frame)*8, frame_sha256=_frame_sha256(frame),
                        evidence=prop.get("evidence"),
                    )
                return
            exact_bits = len(frame) * 8
            c = Candidate(
                family=prop["family"],
                frame=frame,
                exact_bits=exact_bits,
                reconstructed_sha256=actual_digest,
                evidence=prop.get("evidence", {}),
            )
            candidates.append(c)
            if ledger is not None:
                ledger.record(
                    family_name, ProposalDisposition.ELIGIBLE, "eligible",
                    emitted_bits=exact_bits, frame_sha256=_frame_sha256(frame),
                    evidence=prop.get("evidence"),
                )
        except CodecFormatError as e:
            if ledger is not None:
                ledger.record(
                    family_name, ProposalDisposition.REJECTED, f"format_error:{e}",
                    emitted_bits=len(frame)*8 if frame else None,
                    frame_sha256=_frame_sha256(frame) if frame else None,
                )

    try_proposal(raw.propose(values), "RAW")
    try_proposal(periodic_sparse.propose(values), "PERIODIC_SPARSE")

    if not candidates:
        raise RuntimeError("no eligible candidates (RAW must always succeed)")

    # Deterministic tie-breaker: (bits, family value, frame bytes)
    winner = min(candidates, key=lambda x: (x.exact_bits, int(x.family), x.frame))

    if ledger is not None:
        ledger.mark_selected(winner.family.name)

    return winner


def decode(frame: bytes) -> List[int]:
    values, _ = deserialize(frame)
    return values
