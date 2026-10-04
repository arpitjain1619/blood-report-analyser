import os
import tempfile
import pymupdf  # PyMuPDF


def pdf_to_images(pdf_path: str, dpi: int = 200) -> list:
    """
    Renders every page of a PDF to a PNG image on disk and returns the list
    of image file paths (one per page), in page order.

    The caller is responsible for deleting these temp files when done.
    dpi controls render resolution — higher = sharper but larger/slower.
    """
    image_paths = []
    doc = pymupdf.open(pdf_path)
    try:
        for page_index in range(len(doc)):
            page = doc[page_index]
            pix = page.get_pixmap(dpi=dpi)

            fd, img_path = tempfile.mkstemp(suffix=f"_page{page_index}.png")
            os.close(fd)  # we only want the path; close the OS file handle
            pix.save(img_path)
            image_paths.append(img_path)
    finally:
        doc.close()

    return image_paths