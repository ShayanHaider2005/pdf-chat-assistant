import os
import io
import sys
import tempfile
import urllib.parse
import subprocess
import requests
import streamlit as st
from PIL import Image

try:
    import pypdf
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pypdf"])
    import pypdf

def convert_from_path(pdf_path, first_page=1, last_page=None):
    reader = pypdf.PdfReader(pdf_path)
    images = []
    
    start_idx = max(0, first_page - 1)
    end_idx = len(reader.pages) if last_page is None else min(len(reader.pages), last_page)
    
    for page_num in range(start_idx, end_idx):
        page = reader.pages[page_num]
        for image_file_object in page.images:
            image = Image.open(io.BytesIO(image_file_object.data))
            images.append(image)
    return images

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import HumanMessage

st.set_page_config(page_title="PDF Chat Assistant", layout="wide")
st.title("Chat with Your PDF")

api_key = os.getenv("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("GOOGLE_API_KEY secret is missing! Please set it in Streamlit / Replit Secrets.")
    st.stop()


@st.cache_resource
def load_llm(key):
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", google_api_key=key, temperature=0.3
    )


@st.cache_resource
def load_embeddings():
    return HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")


def generate_image_bytes(prompt):
    encoded_prompt = urllib.parse.quote(prompt)
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=800&height=800&nologo=true"
    response = requests.get(url, timeout=15)
    if response.status_code == 200:
        return response.content
    return None


llm = load_llm(api_key)
embeddings = load_embeddings()

if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "pdf_processed" not in st.session_state:
    st.session_state.pdf_processed = False
if "pdf_images" not in st.session_state:
    st.session_state.pdf_images = []

with st.sidebar:
    st.header("1. Upload Document")
    uploaded_file = st.file_uploader("Upload a PDF file", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Process PDF", type="primary"):
            with st.spinner("Processing text and rendering images..."):
                try:
                    with tempfile.NamedTemporaryFile(
                        delete=False, suffix=".pdf"
                    ) as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_filepath = tmp_file.name
                        
                    loader = PyPDFLoader(tmp_filepath)
                    documents = loader.load()
                    st.session_state.pdf_images = convert_from_path(
                        tmp_filepath, first_page=1, last_page=5
                    )
                    
                    if os.path.exists(tmp_filepath):
                        os.remove(tmp_filepath)
                        
                    if documents:
                        text_splitter = RecursiveCharacterTextSplitter(
                            chunk_size=1000, chunk_overlap=200, length_function=len
                        )
                        chunks = text_splitter.split_documents(documents)
                        st.session_state.vectorstore = FAISS.from_documents(
                            chunks, embeddings
                        )
                    st.session_state.pdf_processed = True
                    st.session_state.messages = []
                    st.success(f"Indexed {len(documents)} pages! Ready for queries.")
                except Exception as e:
                    st.error(f"Error processing PDF: {e}")
    st.divider()
    if st.session_state.pdf_processed:
        st.info("Status: PDF loaded and ready.")
        if st.button("Summarize Document"):
            with st.spinner("Generating document summary..."):
                try:
                    if st.session_state.vectorstore:
                        summary_docs = st.session_state.vectorstore.similarity_search(
                            "summary main points overview", k=6
                        )
                        summary_context = "\n\n".join(
                            [doc.page_content for doc in summary_docs]
                        )
                        summary_prompt = f"Provide a clear, structured summary and key takeaways from this text:\n{summary_context}"
                        raw_summary = llm.invoke(summary_prompt)
                    else:
                        raw_summary = llm.invoke(
                            [
                                HumanMessage(
                                    content=[
                                        {
                                            "type": "text",
                                            "text": "Summarize the key information visible across these PDF page images:",
                                        },
                                        *[
                                            {"type": "image_url", "image_url": img}
                                            for img in st.session_state.pdf_images
                                        ],
                                    ]
                                )
                            ]
                        )
                    summary_text = (
                        raw_summary.content
                        if hasattr(raw_summary, "content")
                        else str(raw_summary)
                    )
                    st.session_state.messages.append(
                        {"role": "assistant", "type": "text", "content": summary_text}
                    )
                    st.rerun()
                except Exception as e:
                    st.error(f"Error generating summary: {e}")
    else:
        st.warning("Status: Please upload and process a PDF.")
    st.divider()
    st.caption("Created by Shayan Haider")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        if message.get("type") == "image":
            st.image(message["content"], caption="Generated Image")
        else:
            st.markdown(message["content"])

if user_question := st.chat_input("Ask a question or request an image..."):
    if not st.session_state.pdf_processed:
        st.warning("Please upload and process a PDF file from the sidebar first.")
    else:
        st.session_state.messages.append(
            {"role": "user", "type": "text", "content": user_question}
        )
        with st.chat_message("user"):
            st.markdown(user_question)

        with st.chat_message("assistant"):
            lowered_input = user_question.lower()
            if any(
                keyword in lowered_input
                for keyword in [
                    "generate image",
                    "create image",
                    "draw",
                    "make image",
                    "picture of",
                ]
            ):
                with st.spinner("Generating image..."):
                    img_bytes = generate_image_bytes(user_question)
                    if img_bytes:
                        st.image(img_bytes, caption="Generated Image")
                        st.session_state.messages.append(
                            {"role": "assistant", "type": "image", "content": img_bytes}
                        )
                    else:
                        st.error("Failed to generate image. Please try again.")
            else:
                with st.spinner("Searching document & analyzing with Gemini..."):
                    try:
                        chat_history_str = ""
                        recent_messages = st.session_state.messages[:-1][-6:]
                        for msg in recent_messages:
                            if msg.get("type") == "text":
                                chat_history_str += (
                                    f"{msg['role'].capitalize()}: {msg['content']}\n"
                                )
                        if st.session_state.vectorstore:
                            retriever = st.session_state.vectorstore.as_retriever(
                                search_kwargs={"k": 4}
                            )
                            relevant_docs = retriever.invoke(user_question)
                            context_text = "\n\n---\n\n".join(
                                [doc.page_content for doc in relevant_docs]
                            )
                            qa_prompt = ChatPromptTemplate.from_messages(
                                [
                                    (
                                        "system",
                                        "You are an expert document assistant. Use the provided context and "
                                        "chat history to answer the question.\n\n"
                                        "Recent Chat History:\n{chat_history}\n\n"
                                        "Context from PDF:\n{context}",
                                    ),
                                    ("human", "{input}"),
                                ]
                            )
                            chain = qa_prompt | llm
                            raw_response = chain.invoke(
                                {
                                    "chat_history": chat_history_str
                                    if chat_history_str
                                    else "None",
                                    "context": context_text,
                                    "input": user_question,
                                }
                            )
                        else:
                            raw_response = llm.invoke(
                                [
                                    HumanMessage(
                                        content=[
                                            {
                                                "type": "text",
                                                "text": f"Question: {user_question}\nAnswer using the provided page images:",
                                            },
                                            *[
                                                {"type": "image_url", "image_url": img}
                                                for img in st.session_state.pdf_images[
                                                    :3
                                                ]
                                            ],
                                        ]
                                    )
                                ]
                            )
                        raw_content = (
                            raw_response.content
                            if hasattr(raw_response, "content")
                            else str(raw_response)
                        )
                        if isinstance(raw_content, list):
                            clean_parts = [
                                item.get("text", "")
                                if isinstance(item, dict)
                                else str(item)
                                for item in raw_content
                            ]
                            answer_text = "\n".join(clean_parts)
                        else:
                            answer_text = str(raw_content)
                        st.markdown(answer_text)
                        st.session_state.messages.append(
                            {
                                "role": "assistant",
                                "type": "text",
                                "content": answer_text,
                            }
                        )
                    except Exception as e:
                        st.error(f"Error generating answer: {e}")
