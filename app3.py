import streamlit as st
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def get_pdf_text(pdf_docs):
    text = ""
    for pdf in pdf_docs:
        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
    return text

def get_pdf_chunks(text):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
    chunks = text_splitter.split_text(text)
    return chunks

def get_vector_store(text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
    vector_store.save_local("faiss index")

def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, make sure provide all the details ,if the answer is not in context just say,"answer is not available in the context",don't provide the wrong answer.
    Context:\n{context}?\n
    Question:\n{question}\n   

    Answer:
    """
    #model = ChatGoogleGenerativeAI(model="gemini-1.5-pro-latest", temperature=0.3)
    model = ChatGoogleGenerativeAI(model="gemini-1.5-flash-latest",temperature=0.3)
    prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
    chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
    return chain

def user_input(user_question, text_chunks):
    embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
    new_db = FAISS.from_texts(text_chunks, embedding=embeddings)
    docs = new_db.similarity_search(user_question)
    chain = get_conversational_chain()

    response = chain(
        {"input_documents": docs, "question": user_question},
        return_only_outputs=True
    )

    print(response)
    st.write("Reply:", response["output_text"])

def main():
    st.set_page_config(page_title="📚 Chat with your PDFs", page_icon="🤖", layout="wide")
    st.markdown("<h1 style='text-align: center;'>📄 PDF Chatbot Assistant</h1>", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("### 📤 Upload your PDFs")
        pdf_docs = st.file_uploader("Choose PDF files", type="pdf", accept_multiple_files=True)
        if pdf_docs and st.button("🔍 Process PDFs"):
            with st.spinner("🔄 Reading and processing..."):
                raw_text = get_pdf_text(pdf_docs)
                text_chunks = get_pdf_chunks(raw_text)
                get_vector_store(text_chunks)
                st.session_state.text_chunks = text_chunks
            st.success("✅ PDFs processed!")

    if "text_chunks" in st.session_state:
        user_question = st.text_input("💬 Ask a question about your documents:")
        if user_question:
            with st.spinner("🧠 Generating answer..."):
                response = user_input(user_question, st.session_state.text_chunks)
                

if __name__ == "__main__":
    main()