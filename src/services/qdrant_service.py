from ..utils import qdrant_cloud
from qdrant_client.models import Distance, VectorParams, PointStruct

class Qdrant_Service():

    def __init__(self, collection_name: str):
        self.client = qdrant_cloud
        self.collection_name = collection_name
    
    def collection_exists(self) -> bool:
        return self.client.collection_exists(self.collection_name)

    def create_collection(self):
        if not self.collection_exists():
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=1024,
                    distance=Distance.COSINE
                )
            )

    def upsert(self, points: list[PointStruct]):
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )

    def search(self, query_vector, limit: int = 3):
        search_result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            limit=limit
        )
        return search_result

    def delete_collection(self):
        """Deletes the entire collection from Qdrant."""
        if self.collection_exists():
            self.client.delete_collection(collection_name=self.collection_name)

    def delete_points(self, point_ids: list[str | int]):
        """Deletes specific points by their IDs."""
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=point_ids
        )

    def clear_collection(self):
        """Removes all points but keeps the collection schema."""
        from qdrant_client.models import Filter
        self.client.delete(
            collection_name=self.collection_name,
            points_selector=Filter()
        )

    def count(self) -> int:
        """Returns the total number of vectors in the collection."""
        if not self.collection_exists():
            return 0
        response = self.client.count(collection_name=self.collection_name)
        return response.count
