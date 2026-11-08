
from PIL import Image
import pytesseract


def extract_text_from_image(uploaded_file):

    try:
        image = Image.open(uploaded_file)

        # Extract English text from image
        text = pytesseract.image_to_string(
            image,
            lang="eng"
        )

        return text.strip()

    except Exception as e:
        raise RuntimeError(
            f"Image OCR extraction failed: {e}"
        )
