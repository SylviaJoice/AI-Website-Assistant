from flask import Flask, render_template, request, redirect, url_for, jsonify, session
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from openai import OpenAI
from urllib.parse import urljoin, urlparse
import markdown

from knowledge_base import split_into_chunks, find_relevant_chunks
from pdf_reader import extract_pdf_text

load_dotenv()

app = Flask(__name__)
app.secret_key = "website-assistant-secret-key"

stored_url = ""
stored_website_text = ""
stored_pdf_text = ""
print("PDF STORAGE INIT DONE")
chat_messages = []

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

# ---------------- WEBSITE SCRAPER ----------------
def get_website_text(url):
    headers = {"User-Agent": "Mozilla/5.0"}

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")

    for tag in soup(["script", "style"]):
        tag.decompose()

    main_text = soup.get_text(separator=" ", strip=True)

    return main_text[:20000]


# ---------------- AI FUNCTION ----------------
def ask_ai(website_text, question):

    chunks = split_into_chunks(website_text)
    relevant_chunks = find_relevant_chunks(chunks, question)
    context = "\n\n".join(relevant_chunks)

    memory_text = ""
    for msg in chat_messages[-6:]:
        role = "User" if msg["sender"] == "You" else "Assistant"
        memory_text += f"{role}: {msg['text']}\n"

    prompt = f"""
You are a helpful AI assistant.

Conversation Memory:
{memory_text}

Website / PDF Content:
{context}

User Question:
{question}

Answer clearly and helpfully.
"""
    print("PROMPT LENGTH:", len(prompt))
    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[{"role": "user", "content": prompt}]
    )

    return response.choices[0].message.content


# ---------------- HOME PAGE ----------------
@app.route("/", methods=["GET", "POST"])
def home():
    global stored_url, stored_website_text, stored_pdf_text, chat_messages

    if request.method == "POST":
        print("HOME ROUTE TRIGGERED")
        url = request.form.get("url", "").strip()
        question = request.form.get("question", "").strip()
        pdf_file = request.files.get("pdf_file")

        if question:

            try:
                knowledge_text = ""

                # PDF mode
                if pdf_file and pdf_file.filename:
                    session["pdf_text"] = extract_pdf_text(pdf_file)
                    print("PDF UPLOADED SUCCESSFULLY")
                    print("PDF LENGTH:", len(session["pdf_text"]))
                    print("PDF UPLOADED SUCCESSFULLY")
                    print("PDF LENGTH:", len(stored_pdf_text))
                    knowledge_text = stored_pdf_text

                # Website mode
                if stored_website_text:
                    knowledge_text = stored_website_text

                # PDF mode
                elif stored_pdf_text:
                    knowledge_text = stored_pdf_text

                else:
                    return jsonify({"answer": "Please upload a PDF or enter a website URL first."})

                # Ask AI
                answer = ask_ai(knowledge_text, question)

                # store chat
                chat_messages.append({"sender": "You", "text": question})
                chat_messages.append({"sender": "Bot", "text": answer})

            except Exception as e:
                print("ERROR:", e)
                answer = "Something went wrong."
                chat_messages.append({"sender": "Bot", "text": answer})

            except Exception as e:
                print("ERROR:", e)
                answer = "Something went wrong."
                chat_messages.append({"sender": "Bot", "text": answer})

        return redirect(url_for("home"))

    return render_template(
        "index.html",
        url=stored_url,
        messages=chat_messages
    )


# ---------------- CHAT API (AJAX) ----------------
@app.route("/chat", methods=["POST"])
def chat():
    global stored_url, stored_website_text, stored_pdf_text, chat_messages

    try:
        data = request.get_json()
        print("SESSION PDF EXISTS:", "pdf_text" in session)
        question = data.get("question", "").strip()
        url = data.get("url", "").strip()

        if not question:
            return jsonify({"error": "No question"}), 400

        knowledge_text = ""

        # get stored data
        pdf_text = session.get("pdf_text", "")
        web_text = stored_website_text

        # WEBSITE loading (only if needed)
        if url and url.startswith("http"):
            if stored_url != url or not stored_website_text:
                web_text = get_website_text(url)
                stored_website_text = web_text
                stored_url = url

        # PRIORITY LOGIC (correct order)
        if pdf_text and len(pdf_text.strip()) > 50:
            knowledge_text = pdf_text

        elif web_text and len(web_text.strip()) > 50:
            knowledge_text = web_text

        else:
            return jsonify({"answer": "Please upload a PDF or enter a URL first."})

        print("FINAL KNOWLEDGE LENGTH:", len(knowledge_text))

        answer = ask_ai(knowledge_text, question)

        chat_messages.append({"sender": "You", "text": question})
        chat_messages.append({"sender": "Bot", "text": answer})

        return jsonify({"answer": answer})
    except Exception as e:
                print("REAL ERROR:", e)
                return jsonify({"error": str(e)}), 500

# ---------------- CLEAR CHAT ----------------
@app.route("/clear")
def clear_chat():
    global stored_url, stored_website_text, stored_pdf_text, chat_messages

    stored_url = ""
    stored_website_text = ""
    stored_pdf_text = ""
    chat_messages = []

    return redirect(url_for("home"))
@app.route("/upload_pdf", methods=["POST"])
def upload_pdf():
    pdf_file = request.files.get("pdf_file")

    if not pdf_file:
        return {"success": False}

    pdf_text = extract_pdf_text(pdf_file)

    session["pdf_text"] = pdf_text

    print("PDF UPLOADED SUCCESSFULLY")
    print("PDF LENGTH:", len(pdf_text))

    return {"success": True}

# ---------------- RUN APP ----------------
if __name__ == "__main__":
    app.run(debug=True)