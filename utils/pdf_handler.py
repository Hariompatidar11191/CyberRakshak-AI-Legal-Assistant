
import pymupdf


def extract_text_from_pdf(uploaded_file):

    text = ""

    try:
        pdf_bytes = uploaded_file.read()

        pdf = pymupdf.open(
            stream=pdf_bytes,
            filetype="pdf"
        )

        for page_number, page in enumerate(pdf, start=1):

            page_text = page.get_text("text")

            if page_text.strip():
                text += (
                    f"\n--- Page {page_number} ---\n"
                    f"{page_text}\n"
                )

        pdf.close()

        return text.strip()

    except Exception as e:
        raise RuntimeError(f"PDF extraction failed: {e}")
