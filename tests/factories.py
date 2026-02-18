from datetime import datetime, timezone

from polyfactory.factories.pydantic_factory import ModelFactory

# TODO: replace with actual package imports once released
from erspec.models.core import (
    CanonicalEntityIdentifier,
    ClusterReference,
    DecisionStatus,
    EntityMention,
    EntityMentionIdentifier,
)

from ers.domain.models import CurationDecision


class EntityMentionIdentifierFactory(ModelFactory):
    __model__ = EntityMentionIdentifier

    @classmethod
    def source_id(cls) -> str:
        return f"source-{cls.__faker__.uuid4()[:8]}"

    @classmethod
    def request_id(cls) -> str:
        return f"request-{cls.__faker__.uuid4()[:8]}"

    @classmethod
    def entity_type(cls) -> str:
        return "ORGANISATION"


class ClusterReferenceFactory(ModelFactory):
    __model__ = ClusterReference

    @classmethod
    def cluster_id(cls) -> str:
        return f"cluster-{cls.__faker__.uuid4()}"

    @classmethod
    def confidence_score(cls) -> float:
        return round(cls.__faker__.pyfloat(min_value=0.0, max_value=1.0), 2)


class EntityMentionFactory(ModelFactory):
    __model__ = EntityMention

    @classmethod
    def identifier(cls) -> EntityMentionIdentifier:
        return EntityMentionIdentifierFactory.build()

    @classmethod
    def content_type(cls) -> str:
        return "application/ld+json"

    @classmethod
    def content(cls) -> str:
        return '{"name": "Example Entity"}'

    @classmethod
    def parsed_representation(cls) -> str:
        return '{"name": "Example Entity"}'


class CanonicalEntityIdentifierFactory(ModelFactory):
    __model__ = CanonicalEntityIdentifier

    @classmethod
    def identifier(cls) -> str:
        return f"canonical-{cls.__faker__.uuid4()[:8]}"

    @classmethod
    def equivalent_to(cls) -> list[EntityMentionIdentifier]:
        return EntityMentionIdentifierFactory.batch(3)


class CurationDecisionFactory(ModelFactory):
    __model__ = CurationDecision

    @classmethod
    def id(cls) -> str:
        return f"decision-{cls.__faker__.uuid4()[:8]}"

    @classmethod
    def about_entity_mention(cls) -> EntityMentionIdentifier:
        return EntityMentionIdentifierFactory.build()

    @classmethod
    def status(cls) -> DecisionStatus:
        return DecisionStatus.PENDING_MANUAL_REVIEW

    @classmethod
    def action(cls) -> None:
        return None

    @classmethod
    def accepted_candidate(cls) -> ClusterReference:
        return ClusterReferenceFactory.build()

    @classmethod
    def candidates(cls) -> list[ClusterReference]:
        return ClusterReferenceFactory.batch(3)

    @classmethod
    def created_at(cls) -> datetime:
        return datetime.now(timezone.utc)

    @classmethod
    def updated_at(cls) -> None:
        return None
