
import streamlit as st
from google import genai
from google.genai import types

# ---------------- PAGE CONFIGURATION ----------------

st.set_page_config(
    page_title="AI Research Paper Assistant",
    page_icon="📚",
    layout="wide"
)

MODEL_NAME = "gemini-3.8-flash"

# ---------------- GEMINI CONNECTION ----------------

@st.cache_resource
def get_gemini_client():
    api_key = st.secrets["GEMINI_API_KEY"]
    return genai.Client(api_key=api_key)


# ---------------- PAGE DESIGN ----------------

st.title("📚 AI Research Paper Assistant")

st.write(
    "Understand research papers easily with the power of AI."
)

st.divider()

# ---------------- PDF UPLOAD ----------------

st.header("📄 Upload Your Research Paper")

uploaded_file = st.file_uploader(
    "Choose a PDF file",
    type=["pdf"]
)

if uploaded_file is None:
    st.info("Please upload a research paper PDF to get started.")
    st.stop()

pdf_bytes = uploaded_file.getvalue()

if not pdf_bytes.startswith(b"%PDF"):
    st.error("The uploaded file does not appear to be a valid PDF.")
    st.stop()

if len(pdf_bytes) > 20 * 1024 * 1024:
    st.error("Please upload a PDF smaller than 20 MB.")
    st.stop()

st.success(f"PDF uploaded successfully: {uploaded_file.name}")

# ---------------- PREPARE PDF FOR GEMINI ----------------

pdf_part = types.Part.from_bytes(
    data=pdf_bytes,
    mime_type="application/pdf"
)

try:
    client = get_gemini_client()
except Exception as e:
    st.error(f"Gemini connection error: {e}")
    st.stop()


# ---------------- SUMMARY SECTION ----------------

st.divider()

st.header("📝 Research Paper Summary")

if st.button("Generate Summary", use_container_width=True):
    with st.spinner("Gemini is reading your research paper..."):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    "Read this research paper carefully. "
                    "Provide a clear summary covering the research "
                    "topic, objectives, methodology, major findings, "
                    "conclusion, and limitations. Only report information "
                    "supported by the paper.",
                    pdf_part
                ]
            )

            st.subheader("Paper Summary")
            st.markdown(response.text or "No text response was returned.")

        except Exception as e:
            st.error(f"Could not generate summary: {e}")


# ---------------- KEY POINTS SECTION ----------------

st.divider()

st.header("🔑 Important Key Points")

if st.button("Extract Key Points", use_container_width=True):
    with st.spinner("Extracting important points..."):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=[
                    "Analyze this research paper and extract its "
                    "10 most important key points. Include important "
                    "concepts, methodology, findings, and conclusions. "
                    "Do not invent information.",
                    pdf_part
                ]
            )

            st.subheader("Key Points to Remember")
            st.markdown(response.text or "No text response was returned.")

        except Exception as e:
            st.error(f"Could not extract key points: {e}")


# ---------------- CHAT SECTION ----------------

st.divider()

st.header("💬 Chat with Your Research Paper")

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# Display previous conversation
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

question = st.chat_input(
    "Ask anything about your research paper..."
)

if question:

    st.session_state.chat_history.append({
        "role": "user",
        "content": question
    })

    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        with st.spinner("Gemini is thinking..."):

            try:
                # Include recent conversation for context
                conversation = st.session_state.chat_history[-11:]

                chat_prompt = (
                    "Answer the user's questions using the uploaded "
                    "research paper as your primary source. "
                    "If the answer is not available in the paper, "
                    "clearly say so. Do not invent facts.\n\n"
                )

                for message in conversation:
                    chat_prompt += (
                        message["role"].upper()
                        + ": "
                        + message["content"]
                        + "\n"
                    )

                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=[
                        chat_prompt,
                        pdf_part
                    ]
                )

                answer = response.text or "No answer was returned."

                st.markdown(answer)

                st.session_state.chat_history.append({
                    "role": "assistant",
                    "content": answer
                })

            except Exception as e:
                st.error(f"Gemini could not answer: {e}")

st.divider()

st.caption(
    "Powered by Google Gemini AI | Built with Python and Streamlit"
)
