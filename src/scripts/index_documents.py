import os
import glob
import logging
import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client.models import PointStruct

from ..utils import embedding_model
from ..services import Qdrant_Service

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

logger = logging.getLogger("indexer")

COLLECTION_NAME = "compliance_docs"


def index_docs():
    """
    Reads the compliance PDFs, chunks them, embeds them,
    and uploads to Qdrant cloud.
    """

    BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    DOCS_DIR = os.path.join(BASE_DIR, "data", "compliance_docs")

    # Step 1: Find all PDFs
    pdf_files = glob.glob(os.path.join(DOCS_DIR, "*.pdf"))

    if not pdf_files:
        logger.warning(f"No PDF files found in {DOCS_DIR}")
        return

    logger.info(f"Found {len(pdf_files)} PDF(s): {[os.path.basename(f) for f in pdf_files]}")

    # Step 2: Load and split all PDFs into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )

    all_chunks = []
    for pdf_path in pdf_files:
        logger.info(f"Loading: {os.path.basename(pdf_path)}")
        loader = PyPDFLoader(pdf_path)
        pages = loader.load()
        chunks = text_splitter.split_documents(pages)
        all_chunks.extend(chunks)
        logger.info(f"  → {len(pages)} pages → {len(chunks)} chunks")

    logger.info(f"Total chunks across all documents: {len(all_chunks)}")

    # Step 3: Embed all chunks
    logger.info("Embedding chunks (this may take a moment)...")
    chunk_texts = [chunk.page_content for chunk in all_chunks]
    embeddings = embedding_model.embed_documents(chunk_texts)
    logger.info(f"Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")

    # Step 4: Build PointStruct objects for Qdrant
    points = []
    for i, (chunk, vector) in enumerate(zip(all_chunks, embeddings)):
        point = PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "page_content": chunk.page_content,
                "source": os.path.basename(chunk.metadata.get("source", "")),
                "page": chunk.metadata.get("page", 0),
            }
        )
        points.append(point)

    # Step 5: Create collection and upsert into Qdrant
    qdrant = Qdrant_Service(collection_name=COLLECTION_NAME)
    qdrant.create_collection()
    logger.info(f"Collection '{COLLECTION_NAME}' ready")

    # Upsert in batches of 100 to avoid payload limits
    batch_size = 100
    for i in range(0, len(points), batch_size):
        batch = points[i:i + batch_size]
        qdrant.upsert(batch)
        logger.info(f"  Upserted batch {i // batch_size + 1} ({len(batch)} points)")

    total = qdrant.count()
    logger.info(f"Done! {total} total points in '{COLLECTION_NAME}'")
