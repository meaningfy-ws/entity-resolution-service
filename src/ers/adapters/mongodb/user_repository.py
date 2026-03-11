from ers.adapters.mongodb.base import BaseMongoRepository
from ers.application.ports.user_repository import UserRepository
from ers.domain.user import User


class MongoUserRepository(BaseMongoRepository[User, str], UserRepository):
    """MongoDB-backed user repository."""

    _model_class = User
    _id_field = "id"

    async def find_by_email(self, email: str) -> User | None:
        doc = await self._collection.find_one({"email": email})
        if doc is None:
            return None
        return self._from_document(doc)

    async def find_all(self) -> list[User]:
        cursor = self._collection.find()
        return [self._from_document(doc) async for doc in cursor]

    async def delete(self, user_id: str) -> bool:
        result = await self._collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
