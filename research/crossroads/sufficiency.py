"""Bounded observational sufficiency checks, not causal or semantic proof."""
from collections import defaultdict


def collisions(bank):
    """Identical observed inputs with distinct outputs refute deterministic sufficiency."""
    groups = defaultdict(lambda: defaultdict(list))
    for index, (x, y) in enumerate(zip(bank['inputs'], bank['outputs'])):
        groups[tuple(x)][y].append(index)
    return [
        {'input': list(x), 'outputs': sorted(ys),
         'indices': [ys[y][0] for y in sorted(ys)],
         'count': sum(map(len, ys.values()))}
        for x, ys in sorted(groups.items()) if len(ys) > 1
    ]


def assess(train, validation):
    """Calibration only: never inspect target outcomes for routing."""
    witnesses = {name: collisions(bank) for name, bank in
                 (('train', train), ('validate', validation))}
    if any(witnesses.values()):
        return {'status': 'OBSERVATION_COLLISION', 'search': 'HOLD',
                'witnesses': witnesses,
                'next': 'Check source consistency, hidden state, timing and missing input features; then collect paired observations.'}
    return {'status': 'NO_COLLISION_OBSERVED', 'search': 'ALLOW',
            'witnesses': witnesses,
            'next': 'Bounded generator search; absence of collisions does not establish sufficiency.'}


def classify(report, train_exact, validation_exact, composed, admitted, budget=False):
    if report['search'] == 'HOLD':
        return 'OBSERVATION_COLLISION'
    if admitted:
        return 'VALIDATED_NEW_GENERATOR'
    if train_exact and validation_exact:
        return 'VALIDATED_EXISTING_OR_UNADMITTED_GENERATOR'
    if budget:
        return 'SEARCH_BUDGET_EXHAUSTED'
    if train_exact:
        return 'VALIDATION_FAILURE'
    return 'UNRESOLVED_BOUNDED_GRAMMAR' if composed else 'LIMITED_SEARCH_UNRESOLVED'
