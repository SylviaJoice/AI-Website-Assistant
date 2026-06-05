from pypdf import PdfReader


def extract_pdf_text(pdf_file):

    reader = PdfReader(pdf_file)

    text = ""

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


if __name__ == "__main__":

    text = extract_pdf_text("AI Website Chatbot Platform Guide.pdf")

    print(text[:1000])