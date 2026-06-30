from langchain_huggingface import HuggingFaceEndpointEmbeddings
from ..config import settings

embedding_model = HuggingFaceEndpointEmbeddings(
    repo_id="BAAI/bge-large-en-v1.5",
    huggingfacehub_api_token=settings.HUGGINGFACEHUB_API_TOKEN
)