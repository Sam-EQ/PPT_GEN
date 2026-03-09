from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import (
    PdfPipelineOptions,
    EasyOcrOptions,
    TesseractCliOcrOptions,
)
from docling.pipeline.standard_pdf_pipeline import StandardPdfPipeline


def _build_pipeline_options(force_ocr: bool = False) -> PdfPipelineOptions:
    opts = PdfPipelineOptions()

    opts.images_scale = 2.0                 
    opts.generate_page_images = True
    opts.generate_picture_images = True     

    if force_ocr:
        opts.do_ocr = True
        opts.ocr_options = EasyOcrOptions(force_full_page_ocr=True)
    else:
        opts.do_ocr = False

    opts.do_table_structure = True           
    return opts


def get_converter(force_ocr: bool = False) -> DocumentConverter:

    pipeline_opts = _build_pipeline_options(force_ocr=force_ocr)

    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(
                pipeline_options=pipeline_opts,
                pipeline_cls=StandardPdfPipeline,
            )
        }
    )


_CONVERTER = get_converter(force_ocr=False)

_CONVERTER_OCR = get_converter(force_ocr=True)