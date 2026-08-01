import os

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_chroma import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
if not key:
    print("ERR: no google key found in secrets!")


def load_and_prep_data(file_path):
    loader = PyPDFLoader(file_path)
    raw_docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    docs = splitter.split_documents(raw_docs)
    return docs


def init_vectorstore(chunks):
    embed_fn = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma.from_documents(
        documents=chunks, embedding=embed_fn, persist_directory="./chroma_db"
    )
    return db


if __name__ == "__main__":
    pdf_file = "sample.pdf"

    if not os.path.exists(pdf_file):
        print(f"Error: {pdf_file} doesn't exist!")
        exit()

    doc_chunks = load_and_prep_data(pdf_file)
    vector_db = init_vectorstore(doc_chunks)

    retriever = vector_db.as_retriever(search_kwargs={"k": 3})

    template = """Answer the question based ONLY on the context below.
    If you don't know, just say "I cannot find the answer in the provided PDF."

    Context:
    {context}

    Question:
    {question}
    """

    prompt = ChatPromptTemplate.from_template(template)
    model = ChatGoogleGenerativeAI(
        model="gemini-3.6-flash", google_api_key=key, temperature=0
    )

    def combine_docs(docs):
        return "\n\n".join(d.page_content for d in docs)

    chain = (
        {"context": retriever | combine_docs, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    print("\nReady! Type 'q' to quit.\n")

    while True:
        try:
            query = input("You: ")
            if query.strip().lower() in ["exit", "quit", "q"]:
                break
            if not query.strip():
                continue

            ans = chain.invoke(query)
            print(f"\nBot: {ans}\n" + "-" * 30)

        except Exception as e:
            print(f"Error: {e}")
