
from datetime import datetime, timedelta, timezone

from app.models.job import Job, ExecutionTarget
from app.scheduler.policies import (
    RandomPolicy,
    GreedyCostLatencyPolicy,
    PredictiveDeadlineAwarePolicy,
)


def make_job(**overrides):
    values = {
        "name": "Policy Test",
        "classical_runtime": 5.0,
        "quantum_runtime": 1.0,
        "classical_cost_per_second": 0.02,
        "quantum_cost_per_second": 0.15,
        "priority": 3,
    }
    values.update(overrides)
    return Job(**values)


def future_deadline(seconds=60):
    return datetime.now(timezone.utc) + timedelta(seconds=seconds)


def test_random_policy_returns_valid_target():
    job = make_job()
    policy = RandomPolicy()

    for _ in range(20):
        result = policy.decide(job, 0, 0)
        assert result in (
            ExecutionTarget.CLASSICAL,
            ExecutionTarget.QUANTUM,
        )


def test_greedy_prefers_cheaper_classical_resource():
    job = make_job(
        classical_runtime=1.0,
        quantum_runtime=1.0,
    )

    result = GreedyCostLatencyPolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.CLASSICAL


def test_greedy_uses_quantum_when_runtime_advantage_wins():
    job = make_job(
        classical_runtime=8.0,
        quantum_runtime=0.5,
    )

    result = GreedyCostLatencyPolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.QUANTUM


def test_high_priority_job_prefers_faster_resource():
    job = make_job(
        classical_runtime=8.0,
        quantum_runtime=0.5,
        priority=5,
    )

    result = GreedyCostLatencyPolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.QUANTUM


def test_predictive_policy_overrides_for_deadline():
    job = make_job(
        classical_runtime=10.0,
        quantum_runtime=1.0,
        classical_cost_per_second=0.001,
        quantum_cost_per_second=10.0,
        deadline=datetime.now(timezone.utc)
        + timedelta(seconds=3),
    )

    result = PredictiveDeadlineAwarePolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.QUANTUM


def test_predictive_policy_keeps_greedy_choice_without_deadline():
    job = make_job()

    predictive = PredictiveDeadlineAwarePolicy()
    greedy = GreedyCostLatencyPolicy(
        cost_weight=0.4,
        latency_weight=0.6,
    )

    assert predictive.decide(job, 0, 0) == greedy.decide(job, 0, 0)


def test_predictive_chooses_classical_when_only_it_meets_deadline():
    job = make_job(
        classical_runtime=2.0,
        quantum_runtime=10.0,
        deadline=future_deadline(5),
    )

    result = PredictiveDeadlineAwarePolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.CLASSICAL


def test_predictive_chooses_quantum_when_only_it_meets_deadline():
    job = make_job(
        classical_runtime=10.0,
        quantum_runtime=2.0,
        deadline=future_deadline(5),
    )

    result = PredictiveDeadlineAwarePolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.QUANTUM


def test_predictive_chooses_faster_resource_when_neither_meets_deadline():
    job = make_job(
        classical_runtime=10.0,
        quantum_runtime=8.0,
        deadline=future_deadline(3),
    )

    result = PredictiveDeadlineAwarePolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.QUANTUM


def test_predictive_high_priority_chooses_faster_when_both_meet_deadline():
    job = make_job(
        classical_runtime=5.0,
        quantum_runtime=2.0,
        priority=5,
        deadline=future_deadline(60),
    )

    result = PredictiveDeadlineAwarePolicy().decide(job, 0, 0)

    assert result == ExecutionTarget.QUANTUM


def test_predictive_low_priority_uses_greedy_when_both_meet_deadline():
    job = make_job(
        classical_runtime=1.0,
        quantum_runtime=1.0,
        priority=3,
        deadline=future_deadline(60),
    )

    predictive = PredictiveDeadlineAwarePolicy()
    greedy = GreedyCostLatencyPolicy(
        cost_weight=0.4,
        latency_weight=0.6,
    )

    assert predictive.decide(job, 0, 0) == greedy.decide(job, 0, 0)
