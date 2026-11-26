def _is_hex64(s: str) -> bool:
    return isinstance(s, str) and bool(HEX64_RE.match(s))

def check_archive_immutability(body: UnfoldingReceiptBody) -> InvariantResult:
    a = body.archive
    if not (_is_hex64(a.prior_state_hash) and _is_hex64(a.realized_frame_hash) and _is_hex64(a.source_sha256)):
        return InvariantResult(ConstitutionalInvariant.ARCHIVE_IMMUTABILITY, False, "invalid_archive_hash_format", (a.prior_state_hash, a.realized_frame_hash, a.source_sha256))
    if a.prior_state_hash == a.realized_frame_hash:
        return InvariantResult(ConstitutionalInvariant.ARCHIVE_IMMUTABILITY, False, "prior_equals_realized", (a.prior_state_hash,))
    return InvariantResult(ConstitutionalInvariant.ARCHIVE_IMMUTABILITY, True, "archive_hashes_valid", (a.prior_state_hash, a.realized_frame_hash, a.source_sha256))

def check_context_declaration(body: UnfoldingReceiptBody) -> InvariantResult:
    inter = body.interaction
    if not (_is_hex64(inter.environment_snapshot_hash) and _is_hex64(inter.permissions_hash)):
        return InvariantResult(ConstitutionalInvariant.CONTEXT_DECLARATION, False, "invalid_context_hash_format", (inter.environment_snapshot_hash, inter.permissions_hash))
    for h in inter.declared_input_hashes:
        if not _is_hex64(h):
            return InvariantResult(ConstitutionalInvariant.CONTEXT_DECLARATION, False, "invalid_input_hash", (h,))
    if not isinstance(inter.actor_choices, (tuple, list)):
        return InvariantResult(ConstitutionalInvariant.CONTEXT_DECLARATION, False, "actor_choices_not_declared", ())
    return InvariantResult(ConstitutionalInvariant.CONTEXT_DECLARATION, True, "context_declared", (inter.environment_snapshot_hash, inter.permissions_hash) + tuple(inter.declared_input_hashes))

def check_revision_lineage(body: UnfoldingReceiptBody) -> InvariantResult:
    gen = body.generator
    if not gen.prior_generator_id:
        return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, False, "missing_prior_generator_id", ())
    if not (_is_hex64(gen.executable_hash) and _is_hex64(gen.prior_state_hash) and _is_hex64(gen.predicted_set_hash)):
        return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, False, "invalid_generator_hash", (gen.executable_hash, gen.prior_state_hash, gen.predicted_set_hash))
    if not body.parent_ids:
        return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, False, "missing_parent_ids", ())
    for pid in body.parent_ids:
        if not _is_hex64(pid):
            return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, False, "invalid_parent_id_format", (pid,))
    if body.disposition in (ReceiptDisposition.REVISED, ReceiptDisposition.BRANCHED, ReceiptDisposition.RETIRED):
        if body.next_generator is None:
            return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, False, "next_generator_required", (body.disposition.value,))
        if not (_is_hex64(body.next_generator.state_hash) and _is_hex64(body.next_generator.update_program_hash)):
            return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, False, "invalid_next_generator_hash", ())
    return InvariantResult(ConstitutionalInvariant.REVISION_LINEAGE, True, "lineage_valid", tuple(body.parent_ids))
