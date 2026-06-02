from flask import Flask, render_template, request, redirect, url_for, session
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import os
from openai import OpenAI
from urllib.parse import urljoin, urlparse
import markdown
load_dotenv()

app = Flask(__name__)
app.secret_key = "website-assistant-secret-key"
stored_url = ""
stored_website_text = ""
chat_messages = []
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)


def get_website_text(url):
    print("Reading website now...")
    headers = {
    "User-Agent": "Mozilla/5.0"
      }

    response = requests.get(url, headers=headers, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    print("HTML LENGTH:", len(response.text))
    print(response.text[:500])
    for tag in soup(["script", "style"]):
        tag.decompose()

    main_text = soup.get_text(separator=" ", strip=True)

    important_links = get_important_links(url, soup)
    print("IMPORTANT LINKS FOUND:")
    for link in important_links:
    
     print(link)
    combined_text = main_text + "\n\nImportant related pages:\n"

    for link in important_links:
        try:
            page_response = requests.get(link, timeout=10)
            page_soup = BeautifulSoup(page_response.text, "html.parser")

            for tag in page_soup(["script", "style"]):
                tag.decompose()

            page_text = page_soup.get_text(separator=" ", strip=True)
            combined_text += f"\n\nContent from {link}:\n{page_text[:3000]}"

        except:
            continue

    return combined_text[:20000]

def get_important_links(base_url, soup):
    links = []

    for a in soup.find_all("a", href=True):
        href = a["href"].strip()

        if (
            href.startswith("#")
            or href.startswith("javascript:")
            or href.startswith("mailto:")
            or href.startswith("tel:")
        ):
            continue

        full_url = urljoin(base_url, href)

        if urlparse(full_url).netloc == urlparse(base_url).netloc:
            clean_url = full_url.split("#")[0]

            if clean_url not in links:
                links.append(clean_url)

    return links[:10]

def ask_ai(website_text, question):
    prompt = f"""
You are a helpful website assistant.

Answer the user's question using only the website content below.
If the answer is clearly visible in the website content, answer directly.
If the user asks about registration, application, steps, process, fees, dates, links, or requirements, guide them step by step from the page content.
If the information is unavailable, simply say:
"I couldn't find that information on this page."

Do not give long explanations about missing content, website structure, navigation menus, or extraction limitations.
Do not explain your limitations in long paragraphs.
If information is missing, give a short and clear response.
Do not repeatedly mention website extraction issues.
Website content:
{website_text}

User question:
{question}
"""

    response = client.chat.completions.create(
        model="openrouter/free",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    answer = response.choices[0].message.content
    answer = answer.replace("</assistant>", "").strip()
    return markdown.markdown(answer)


@app.route("/", methods=["GET", "POST"])
def home():
    global stored_url, stored_website_text, chat_messages

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        question = request.form.get("question", "").strip()

        if url and question:
            try:
                if stored_url != url or stored_website_text == "":
                    stored_website_text = get_website_text(url)
                    stored_url = url

                answer = ask_ai(stored_website_text, question)

            except Exception as e:
                print("ERROR:", e)
                answer = "Sorry, something went wrong. Please try again."

            chat_messages.append({"sender": "You", "text": question})
            chat_messages.append({"sender": "Bot", "text": answer})

        return redirect(url_for("home"))

    return render_template(
        "index.html",
        url=stored_url,
        messages=chat_messages
    )


@app.route("/clear")
def clear_chat():
    global stored_url, stored_website_text, chat_messages

    stored_url = ""
    stored_website_text = ""
    chat_messages = []

    return redirect(url_for("home"))

if __name__ == "__main__":
    app.run(debug=True)