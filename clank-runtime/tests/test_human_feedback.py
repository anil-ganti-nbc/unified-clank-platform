from datetime import UTC, datetime

import pytest

from clank_runtime.contracts.human_feedback import (
    CapabilitySupport,
    FeedbackProvenance,
    FindingReference,
    HumanQCCapability,
    HumanQCCapabilityDeclaration,
    ModelPrediction,
    OperatorDisposition,
    ReviewItem,
    ReviewProgress,
    ReviewState,
    apply_disposition,
    next_unreviewed,
)


def reference(number: int) -> FindingReference:
    return FindingReference(clank_id="future-clank", finding_id=f"finding-{number}")


def provenance() -> FeedbackProvenance:
    return FeedbackProvenance(
        actor="operator-1",
        recorded_at=datetime.now(UTC),
        channel="web_qc",
        run_id="run-1",
        epoch_id="epoch-1",
    )


def test_shared_dispositions_are_exactly_four_and_distinct():
    assert {d.value for d in OperatorDisposition} == {
        "USEFUL", "NOT USEFUL", "FALSE POSITIVE", "OUT OF STOCK"
    }
    assert OperatorDisposition.NOT_USEFUL != OperatorDisposition.FALSE_POSITIVE
    assert OperatorDisposition.NOT_USEFUL != OperatorDisposition.OUT_OF_STOCK


def test_disposition_is_distinct_from_review_state_and_persists_as_record():
    item = ReviewItem(reference=reference(1))
    reviewed, record = apply_disposition(item, OperatorDisposition.FALSE_POSITIVE, provenance())
    assert item.review_state is ReviewState.UNREVIEWED
    assert reviewed.review_state is ReviewState.REVIEWED
    assert reviewed.disposition is OperatorDisposition.FALSE_POSITIVE
    assert record.finding == item.reference
    assert record.review_state is ReviewState.REVIEWED
    assert record.provenance.actor == "operator-1"


def test_human_disposition_is_distinct_from_model_prediction():
    prediction = ModelPrediction(
        model_id="qc-ranking-v1",
        predicted_label="FALSE POSITIVE",
        probability=0.9,
        generated_at=datetime.now(UTC),
    )
    _, record = apply_disposition(
        ReviewItem(reference=reference(1)), OperatorDisposition.USEFUL, provenance()
    )
    assert prediction.predicted_label == OperatorDisposition.FALSE_POSITIVE.value
    assert record.disposition is OperatorDisposition.USEFUL
    assert "prediction" not in record.__class__.model_fields


def test_review_does_not_delete_finding_and_next_item_advances():
    items = [ReviewItem(reference=reference(n)) for n in range(1, 4)]
    reviewed, _ = apply_disposition(items[0], OperatorDisposition.USEFUL, provenance())
    remaining = [reviewed, *items[1:]]
    assert len(remaining) == 3
    assert next_unreviewed(remaining, after=reviewed.reference).reference == reference(2)


def test_queue_supports_items_beyond_initial_display_capacity():
    items = [ReviewItem(reference=reference(n)) for n in range(1, 124)]
    assert next_unreviewed(items, after=reference(40)).reference == reference(41)
    assert next_unreviewed(items, after=reference(123)).reference == reference(1)


def test_progress_counts_are_explicit_and_measured():
    items = [ReviewItem(reference=reference(n)) for n in range(1, 5)]
    reviewed, _ = apply_disposition(items[0], OperatorDisposition.USEFUL, provenance())
    false_positive, _ = apply_disposition(
        items[1], OperatorDisposition.FALSE_POSITIVE, provenance()
    )
    progress = ReviewProgress.from_items([reviewed, false_positive, *items[2:]])
    assert progress.total == 4
    assert progress.reviewed == 2
    assert progress.unreviewed == 2
    assert progress.useful == 1
    assert progress.false_positive == 1
    assert progress.not_useful == 0
    assert progress.out_of_stock == 0


def test_invalid_unreviewed_disposition_is_rejected():
    with pytest.raises(ValueError, match="non-UNREVIEWED"):
        ReviewItem(
            reference=reference(1),
            review_state=ReviewState.UNREVIEWED,
            disposition=OperatorDisposition.USEFUL,
        )


def test_later_feedback_can_supersede_without_overwriting_history():
    items = ReviewItem(reference=reference(1))
    _, first = apply_disposition(
        items, OperatorDisposition.OUT_OF_STOCK, provenance()
    )
    _, second = apply_disposition(
        items, OperatorDisposition.USEFUL, provenance(), supersedes_feedback_id=first.feedback_id
    )
    assert second.supersedes_feedback_id == first.feedback_id
    assert first.disposition is OperatorDisposition.OUT_OF_STOCK


def test_capability_supports_future_and_legacy_clanks():
    declaration = HumanQCCapabilityDeclaration(
        capability=HumanQCCapability.HUMAN_QC_FEEDBACK,
        support=CapabilitySupport.PARTIAL,
    )
    legacy = HumanQCCapabilityDeclaration(support=CapabilitySupport.UNSUPPORTED)
    assert declaration.capability is HumanQCCapability.HUMAN_QC_FEEDBACK
    assert declaration.support is CapabilitySupport.PARTIAL
    assert legacy.support is CapabilitySupport.UNSUPPORTED
