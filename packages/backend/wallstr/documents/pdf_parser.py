import asyncio
import base64
import io
from hashlib import sha256
from pathlib import Path
from typing import Any, Literal, cast

import pdf2image
import structlog
from langchain_core.messages import HumanMessage
from PIL import Image
from pydantic import BaseModel, Field
from unstructured.chunking import dispatch
from unstructured.partition.pdf import document_to_element_list
from unstructured.partition.pdf_image.pdfminer_processing import (
    clean_pdfminer_inner_elements,
    merge_inferred_with_extracted_layout,
    process_data_with_pdfminer,
)
from unstructured_inference.inference.layout import (
    DocumentLayout,
    process_data_with_model,
)
from unstructured_inference.utils import LayoutElement
from unstructured_ingest.utils.chunking import assign_and_map_hash_ids

from wallstr.conf import settings
from wallstr.core.llm import LLMModel
from wallstr.core.utils import tiktok

logger = structlog.get_logger()

DETECTION_MODEL: (
    Literal["yolox"]
    | Literal["yolox_tiny"]
    # unsupported yet
    | Literal["yolox_quantized"]
    | Literal["detectron2_onnx"]
    | Literal["detectron2_quantized"]
    | Literal["detectron2_mask_rcnn"]
    | Literal["yolox_quantized"]
) = "yolox_tiny"


class Table(BaseModel):
    title: str | None = Field(description="Title of the table")
    data: str = Field(description="Table data in json format")
    content: str = Field(
        description="Summary of the table content that could be used for embedding, explaining the table, omitting the data"
    )


class PdfParser:
    def __init__(self, llm: LLMModel, llm_with_vision: LLMModel) -> None:
        self.llm = llm
        self.llm_with_vision = llm_with_vision

    async def parse(self, file_buffer: io.BytesIO) -> list[dict[str, Any]]:
        file_buffer.seek(0)

        model_name = DETECTION_MODEL
        async with tiktok(f"Infer the layout with {model_name} model"):
            loop = asyncio.get_event_loop()
            file_buffer.seek(0)
            inferred_document_layout = await loop.run_in_executor(
                None,
                lambda: process_data_with_model(
                    file_buffer,
                    model_name=model_name,
                    pdf_image_dpi=200,
                ),
            )

        logger.info("Extract the layout with pdfminer")
        extracted_layout, layouts_links = process_data_with_pdfminer(
            file=file_buffer,
            dpi=200,
        )

        merged_document_layout = merge_inferred_with_extracted_layout(
            inferred_document_layout=inferred_document_layout,
            extracted_layout=extracted_layout,  # type: ignore
            hi_res_model_name=model_name,
        )
        cleaned_document_layout = clean_pdfminer_inner_elements(merged_document_layout)
        logger.info("Parsing document tables")
        final_document_layout = await self._parse_tables_with_llm(
            file_buffer, cleaned_document_layout
        )
        elements = document_to_element_list(
            final_document_layout,
            sortable=True,
            include_page_breaks=False,
            infer_list_items=False,
            layouts_links=layouts_links,
        )
        logger.info("Chunking the file...")
        chunked_elements = dispatch.chunk(
            elements=elements, chunking_strategy="basic", max_characters=2000
        )

        chunked_elements_dicts = [e.to_dict() for e in chunked_elements]
        chunked_elements_dicts = assign_and_map_hash_ids(
            elements=chunked_elements_dicts
        )
        return chunked_elements_dicts

    async def _parse_tables_with_llm(
        self, file_buffer: io.BytesIO, layout: DocumentLayout
    ) -> DocumentLayout:
        async def extract_table_text(
            image: Image.Image, element: LayoutElement
        ) -> None:
            element.text = await self._extract_table_text(image, element)

        async with tiktok("Extracting tables from layout"):
            tasks = []
            for page in layout.pages:
                table_elements = [
                    element for element in page.elements if element.type == "Table"
                ]
                if not table_elements:
                    continue

                image = pdf2image.convert_from_bytes(
                    file_buffer.getvalue(),
                    dpi=200,
                    first_page=page.number,
                    last_page=page.number,
                )[0]

                for element in table_elements:
                    tasks.append(extract_table_text(image, element))

            try:
                # TODO: add rate limiting per user
                await asyncio.gather(*tasks)
            except Exception as e:
                logger.exception(f"Failed to extract table text: {e}")
        return layout

    async def _extract_table_text(
        self, image: Image.Image, element: LayoutElement
    ) -> str:
        padding = 1
        cropped_image = image.crop(
            (
                element.bbox.x1 + padding,
                element.bbox.y1 + padding,
                element.bbox.x2 + padding,
                element.bbox.y2 + padding,
            )
        )

        if settings.DEBUG:
            debug_dir = Path(".debug")
            debug_dir.mkdir(exist_ok=True)
            filename = f"table_{sha256(image.tobytes()).hexdigest()}.png"
            cropped_image.save(debug_dir / filename)
            logger.info(f"Saved table image to {filename}")

        image_buffer = io.BytesIO()
        cropped_image.save(image_buffer, format="PNG")
        image_base64 = base64.b64encode(image_buffer.getvalue()).decode("utf-8")
        messages = [
            HumanMessage(
                [
                    {
                        "type": "text",
                        "text": "Extract all data from the image in json format",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_base64}"},
                    },
                ]
            ),
        ]
        try:
            response = await self.llm_with_vision.with_structured_output(Table).ainvoke(
                messages
            )
            logger.info(f"Extracted table text: {response}")
        except Exception as e:
            logger.error(f"Failed to extract table text: {e}")
            return ""

        response = cast(Table, response)
        text = f"""
        Table: {response.title}
        Description:
        {response.content}
        Data:
        {response.data}
        """
        return text
