# PDF Chat Assistant

A multimodal RAG (Retrieval-Augmented Generation) application built with Streamlit, LangChain, and Gemini 3.6 Flash. This tool enables users to upload PDF documents, ask complex questions, review auto-generated summaries, and dynamically generate contextual visual diagrams.

Created by Shayan Haider on 1st august 2026.

## Features

- Multimodal Document Processing: Handles both standard text-based PDFs and visual/image-heavy documents.
- Vector Search RAG Pipeline: Powered by FAISS vector store and HuggingFace MiniLM embeddings for fast and relevant passage retrieval.
- Conversational Memory: Retains recent chat history to allow natural follow-up questions.
- One-Click Summarization: Automatically extracts core themes and key takeaways from documents.
- On-Demand Image Generation: Seamlessly routes requests to generate illustrative diagrams and visuals directly in the chat interface.

## Tech Stack

- Frontend / UI: Streamlit
- LLM / Vision Model: Google Gemini 3.6 Flash (langchain-google-genai)
- Embeddings: HuggingFace all-MiniLM-L6-v2
- Vector Store: FAISS
- PDF & Image Processing: PyPDF, pdf2image, Pillow
- Orchestration: LangChain Core / Expression Language (LCEL)

## Installation & Setup

1. Clone the repository:
   git clone https://github.com/YOUR_USERNAME/pdf-chat-assistant.git
   cd pdf-chat-assistant

2. Install dependencies:
   pip install -r requirements.txt

3. Set your Google Gemini API Key:
   export GOOGLE_API_KEY="your_gemini_api_key_here"

4. Run the application:
   streamlit run app.py

## Author

Shayan Haider 