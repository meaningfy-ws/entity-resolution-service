from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase


class MongoClientManager:
    """Manages the lifecycle of an AsyncMongoClient."""

    def __init__(self, mongo_uri: str, database_name: str) -> None:
        self._mongo_uri = mongo_uri
        self._database_name = database_name
        self._client: AsyncMongoClient | None = None

    async def connect(self) -> None:
        """Create the async MongoDB client."""
        self._client = AsyncMongoClient(self._mongo_uri)

    async def close(self) -> None:
        """Close the client and release connections."""
        if self._client is not None:
            await self._client.close()
            self._client = None

    def get_database(self) -> AsyncDatabase:
        """Return the database instance. Must be called after connect()."""
        if self._client is None:
            raise RuntimeError(
                "MongoClientManager is not connected. Call connect() first."
            )
        return self._client[self._database_name]
