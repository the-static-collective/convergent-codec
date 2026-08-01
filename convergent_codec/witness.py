"""Witness ledger: exact decision lineage. Optional for decompression."""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Any, Optional


class ProposalDisposition(str, Enum):
    NO_PROPOSAL = "no_proposal"
    REJECTED = "rejected"
    ELIGIBLE = "eligible"
    SELECTED = "selected"


@dataclass(frozen=True)
class ProposalWitness:
    family: str
    disposition: ProposalDisposition
    reason: str
    emitted_bits: Optional[int] = None
    frame_sha256: Optional[str] = None
    evidence: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WitnessLedger:
    entries: List[ProposalWitness] = field(default_factory=list)
    codec_version: str = "0.1.2"
    decision_rule_version: str = "min_emitted_bits_v1"

    def record(
        self,
        family: str,
        disposition: ProposalDisposition,
        reason: str = "",
        emitted_bits: Optional[int] = None,
        frame_sha256: Optional[str] = None,
        evidence: Optional[dict] = None,
    ) -> None:
        self.entries.append(ProposalWitness(
            family=family,
            disposition=disposition,
            reason=reason,
            emitted_bits=emitted_bits,
            frame_sha256=frame_sha256,
            evidence=evidence or {},
        ))

    def mark_selected(self, family: str) -> None:
        """Promote the matching ELIGIBLE entry to SELECTED (deterministic first match)."""
        for i, e in enumerate(self.entries):
            if e.family == family and e.disposition == ProposalDisposition.ELIGIBLE:
                self.entries[i] = ProposalWitness(
                    family=e.family,
                    disposition=ProposalDisposition.SELECTED,
                    reason="selected_minimum_emitted_frame_size",
                    emitted_bits=e.emitted_bits,
                    frame_sha256=e.frame_sha256,
                    evidence=e.evidence,
                )
                return

    def to_dict(self) -> dict:
        return {
            "codec_version": self.codec_version,
            "decision_rule_version": self.decision_rule_version,
            "entries": [
                {
                    "family": e.family,
                    "disposition": e.disposition.value,
                    "reason": e.reason,
                    "emitted_bits": e.emitted_bits,
                    "frame_sha256": e.frame_sha256,
                    "evidence": e.evidence,
                }
                for e in self.entries
            ],
        }
