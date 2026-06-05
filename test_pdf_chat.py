from pdf_reader import extract_pdf_text
from knowledge_base import split_into_chunks, find_relevant_chunks

pdf_text = extract_pdf_text(
    "AI Website Chatbot Platform Guide.pdf"
)

question = "What is the goal of this project?"

chunks = split_into_chunks(pdf_text)

relevant_chunks = find_relevant_chunks(
    chunks,
    question
)

context = "\n\n".join(relevant_chunks)

print("QUESTION:")
print(question)

print("\nRELEVANT CONTENT:")
print(context[:1000])