import tempfile
from pathlib import Path

from pydantic import Secret
from unstructured_ingest.v2.interfaces import ProcessorConfig
from unstructured_ingest.v2.pipeline.pipeline import Pipeline
from unstructured_ingest.v2.processes.chunker import ChunkerConfig
from unstructured_ingest.v2.processes.connectors.fsspec.s3 import (
    S3AccessConfig,
    S3ConnectionConfig,
    S3DownloaderConfig,
    S3IndexerConfig,
)
from unstructured_ingest.v2.processes.connectors.weaviate.local import (
    LocalWeaviateAccessConfig,
    LocalWeaviateConnectionConfig,
    LocalWeaviateUploaderConfig,
    LocalWeaviateUploadStagerConfig,
)
from unstructured_ingest.v2.processes.embedder import EmbedderConfig
from unstructured_ingest.v2.processes.partitioner import PartitionerConfig

from wallstr.conf import settings
from wallstr.documents.weaviate import get_weaviate_client


async def upload_document_to_weaviate(remote_url: str, collection_name: str) -> None:
    """
    Unstructured ingest doesnt support uploading to self-hosted weaviate with custom endpoints.
    So this version works only with api=localhost:8080 grpc=localhost:50051

    https://github.com/Unstructured-IO/unstructured-ingest/issues/365
    """
    """
    wvc = get_weaviate_client()
    await wvc.connect()
    if not await wvc.collections.exists(collection_name):
        await wvc.close()
        raise Exception(f"Collection {collection_name} does not exist, run `task migrate_weaviate` first")
    await wvc.close()
    """

    with tempfile.TemporaryDirectory() as temp_dir:
        Pipeline.from_configs(
            context=ProcessorConfig(verbose=True),
            indexer_config=S3IndexerConfig(remote_url=remote_url),
            downloader_config=S3DownloaderConfig(
                download_dir=Path(temp_dir),
            ),
            source_connection_config=S3ConnectionConfig(
                access_config=Secret(
                    S3AccessConfig(
                        key=settings.STORAGE_ACCESS_KEY.get_secret_value(),
                        secret=settings.STORAGE_SECRET_KEY.get_secret_value(),
                    ),
                ),
                endpoint_url=str(settings.STORAGE_URL),
            ),
            partitioner_config=PartitionerConfig(
                partition_by_api=False,
                additional_partition_args={
                    "split_pdf_page": True,
                    "split_pdf_allow_failed": True,
                    "split_pdf_concurrency_level": 15,
                },
            ),
            chunker_config=ChunkerConfig(chunking_strategy="basic"),
            embedder_config=EmbedderConfig(
                embedding_provider="openai",
                embedding_model_name="text-embedding-3-small",
                embedding_api_key=settings.OPENAI_API_KEY,
            ),
            destination_connection_config=LocalWeaviateConnectionConfig(
                access_config=Secret(LocalWeaviateAccessConfig()),
            ),
            stager_config=LocalWeaviateUploadStagerConfig(),
            uploader_config=LocalWeaviateUploaderConfig(collection=collection_name),
        ).run()
