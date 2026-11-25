
import streamlit as st
from groq import Groq
from pypdf import PdfReader
import io
import hashlib

# ==================================================
# 1. PAGE CONFIGURATION
# ==================================================

st.set_page_config(
    page_title="AI Research Paper Assistant",
    page_icon="📚",
    layout="wide"
)

MODEL_NAME = "openai/gpt-oss-20b"
MAX_FILE_SIZE = 20 * 1024 * 1024
MAX_DOCUMENT_CHARS = 40000

# ==================================================
# 2. GROQ API CONNECTION
# ==================================================

@st.cache_resource
def get_groq_client():
    api_key = st.secrets["GROQ_API_KEY"]

    return Groq(
        api_key=api_key,
        timeout=120.0
    )

def ask_groq(messages):
    client = get_groq_client()

    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=messages,
        max_completion_tokens=2048,
        reasoning_effort="low"
    )

    answer = response.choices[0].message.content

    if not answer:
        raise ValueError("The AI returned an empty response.")

    return answer

# ==================================================
# 3. MAIN PAGE DESIGN
# ==================================================

st.title("📚 AI Research Paper Assistant")

st.write(
    "Understand research papers, assignments, notes "
    "and other PDF documents easily with AI."
)

st.divider()

# ==================================================
# 4. PDF UPLOAD
# ==================================================

st.header("📄 Upload Your Document")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)

if uploaded_file is None:
    st.info("Please upload a PDF document to get started.")
    st.stop()

pdf_bytes = uploaded_file.getvalue()

if len(pdf_bytes) > MAX_FILE_SIZE:
    st.error("Please upload a PDF smaller than 20 MB.")
    st.stop()

# ==================================================
# 5. EXTRACT TEXT FROM PDF
# ==================================================

try:
    reader = PdfReader(io.BytesIO(pdf_bytes))

    if reader.is_encrypted:
        st.error(
            "This PDF is password protected. "
            "Please upload an unlocked PDF."
        )
        st.stop()

    paper_text = "\n\n".join(
        page.extract_text() or ""
        for page in reader.pages
    )

except Exception as e:
    st.error(f"Could not read the PDF: {e}")
    st.stop()

if not paper_text.strip():
    st.error(
        "No readable text was found in this PDF. "
        "It may be a scanned document. "
        "Please upload a PDF containing selectable text."
    )
    st.stop()

# ==================================================
# 6. PREPARE DOCUMENT
# ==================================================

document_text = paper_text[:MAX_DOCUMENT_CHARS]

document_id = hashlib.md5(pdf_bytes).hexdigest()

if st.session_state.get("document_id") != document_id:
    st.session_state.document_id = document_id
    st.session_state.chat_history = []

st.success(
    f"PDF uploaded successfully: {uploaded_file.name}"
)

st.caption(
    f"Total pages: {len(reader.pages)} | "
    f"Extracted characters: {len(paper_text):,}"
)

if len(paper_text) > MAX_DOCUMENT_CHARS:
    st.warning(
        "This is a long document. "
        "Only the first 40,000 characters are currently "
        "used for AI responses."
    )

# ==================================================
# 7. DOCUMENT INSTRUCTIONS
# ==================================================

document_instructions = (
    "You are an intelligent PDF assistant. "
    "You help users understand all kinds of documents, "
    "including research papers, assignments, textbooks, "
    "question banks, study materials, lecture notes "
    "and general PDF documents. "
    "First understand the type and subject of the document. "
    "Use the actual document content when answering. "
    "Explain difficult concepts in simple language. "
    "Do not invent facts or information. "
    "If the answer is not available in the document, "
    "clearly mention that."
)

# ==================================================
# 8. RESEARCH PAPER / DOCUMENT SUMMARY
# ==================================================

st.divider()

st.header("📝 Document Summary")

if st.button(
    "Generate Summary",
    use_container_width=True
):

    with st.spinner("Groq is reading your document..."):

        try:
            answer = ask_groq([
                {
                    "role": "system",
                    "content": document_instructions
                },
                {
                    "role": "user",
                    "content": (
                        "Analyze the following PDF and generate "
                        "a clear and detailed summary.\n\n"
                        "First identify the type of document.\n\n"
                        "Include the following where relevant:\n"
                        "1. Document type and main subject\n"
                        "2. Main topics and objectives\n"
                        "3. Important concepts and explanations\n"
                        "4. Methods or procedures, if applicable\n"
                        "5. Important findings or information\n"
                        "6. Conclusion or overall message\n\n"
                        "Use headings and simple language. "
                        "Adapt the summary to the actual document "
                        "instead of assuming it is a research paper.\n\n"
                        "DOCUMENT:\n"
                        + document_text
                    )
                }
            ])

            st.subheader("Document Summary")
            st.markdown(answer)

        except Exception as e:
            st.error(f"Summary generation failed: {e}")

# ==================================================
# 9. IMPORTANT KEY POINTS
# ==================================================

st.divider()

st.header("🔑 Important Key Points")

if st.button(
    "Extract Key Points",
    use_container_width=True
):

    with st.spinner("Extracting important points..."):

        try:
            answer = ask_groq([
                {
                    "role": "system",
                    "content": document_instructions
                },
                {
                    "role": "user",
                    "content": (
                        "Extract the 10 most important key points "
                        "from the following PDF.\n\n"
                        "Adapt the points to the document type. "
                        "Include important definitions, concepts, "
                        "facts, instructions, formulas or findings "
                        "where relevant.\n\n"
                        "Explain every point briefly and clearly. "
                        "Use numbered points and simple language.\n\n"
                        "DOCUMENT:\n"
                        + document_text
                    )
                }
            ])

            st.subheader("Important Points to Remember")
            st.markdown(answer)

        except Exception as e:
            st.error(f"Key point extraction failed: {e}")

# ==================================================
# 10. CHAT WITH YOUR DOCUMENT
# ==================================================

st.divider()

st.header("💬 Chat with Your Document")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous chat messages

for message in st.session_state.chat_history:

    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input

question = st.chat_input(
    "Ask anything about your uploaded document..."
)

if question:

    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):

        with st.spinner("Groq is thinking..."):

            try:
                messages = [
                    {
                        "role": "system",
                        "content": (
                            document_instructions
                            + "\n\nUPLOADED DOCUMENT:\n"
                            + document_text
                        )
                    }
                ]

                # Include recent conversation history

                messages.extend(
                    st.session_state.chat_history[-10:]
                )

                answer = ask_groq(messages)

                st.markdown(answer)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error(f"Chat response failed: {e}")

                # Remove unanswered question from history

                if st.session_state.chat_history:
                    if st.session_state.chat_history[-1]["role"] == "user":
                        st.session_state.chat_history.pop()

# ==================================================
# 11. FOOTER
# ==================================================

st.divider()

st.caption(
    "Powered by Groq AI | Built with Python and Streamlit"
)
