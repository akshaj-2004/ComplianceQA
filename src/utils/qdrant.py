from qdrant_client import QdrantClient
from ..config import settings

qdrant_cloud = QdrantClient(
    api_key=settings.QDRANT_API_KEY, 
    url=settings.QDRANT_CLUSTER_ENDPOINT
)