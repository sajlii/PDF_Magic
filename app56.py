from flask import Flask, request, jsonify
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
from flask_cors import CORS
import tempfile
import traceback
from langchain_community.vectorstores import FAISS as CommunityFAISS

# Load environment variables and configure GenAI
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for React or other frontends

# === Keep your logic exactly as-is ===

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
    try:
        print("Creating embeddings...")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        print("Creating FAISS vector store...")
        vector_store = CommunityFAISS.from_texts(text_chunks, embedding=embeddings)
        
        print("Saving vector store locally...")
        vector_store.save_local("faiss_index")
        print("Vector store saved successfully")
        
    except Exception as e:
        print(f"Error in get_vector_store: {str(e)}")
        raise

def get_conversational_chain():
    try:
        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure provide all the details, if the answer is not in context just say, "answer is not available in the context", don't provide the wrong answer.
        Context:\n{context}?\n
        Question:\n{question}\n   
        Answer:
        """
        
        # Try different model names in case one doesn't work
        model_names = [
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-1.5-flash-latest",
            "gemini-1.5-pro-latest",
            "gemini-pro"
        ]
        
        model = None
        for model_name in model_names:
            try:
                print(f"Trying model: {model_name}")
                model = ChatGoogleGenerativeAI(model=model_name, temperature=0.3)
                print(f"Successfully initialized model: {model_name}")
                break
            except Exception as e:
                print(f"Failed to initialize model {model_name}: {str(e)}")
                continue
        
        if model is None:
            raise Exception("Could not initialize any Google AI model. Check your API key and quota.")
        
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        return chain
        
    except Exception as e:
        print(f"Error in get_conversational_chain: {str(e)}")
        raise

# === Flask endpoints (React can hit these) ===

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({"message": "PDF Chat API is running!", "success": True})

@app.route('/test-api', methods=['GET'])
def test_api():
    try:
        # Test Google API key
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        test_result = embeddings.embed_query("test")
        
        # Test model initialization
        model = ChatGoogleGenerativeAI(model="gemini-1.5-flash", temperature=0.3)
        
        return jsonify({
            "success": True,
            "message": "Google API key is working!",
            "embedding_length": len(test_result)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/upload', methods=['POST'])
def upload():
    temp_files = []
    pdf_file_objects = []
    
    try:
        print("Upload endpoint called")
        
        if 'pdfs' not in request.files:
            print("No 'pdfs' in request.files")
            return jsonify({'success': False, 'error': 'No files part in the request'}), 400

        files = request.files.getlist('pdfs')
        print(f"Number of files received: {len(files)}")
        
        if not files or (len(files) == 1 and files[0].filename == ''):
            print("No files uploaded or empty filename")
            return jsonify({'success': False, 'error': 'No files uploaded'}), 400

        # Validate files are PDFs
        for file in files:
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({'success': False, 'error': f'File {file.filename} is not a PDF'}), 400

        # Save uploaded PDFs to temp files
        for pdf in files:
            print(f"Processing file: {pdf.filename}")
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            pdf.save(temp_file.name)
            temp_files.append(temp_file.name)
            pdf_file_objects.append(open(temp_file.name, 'rb'))

        print("Starting text extraction...")
        # Process the PDFs
        raw_text = get_pdf_text(pdf_file_objects)
        print(f"Extracted text length: {len(raw_text)}")
        
        # Close file objects
        for pdf_obj in pdf_file_objects:
            pdf_obj.close()
        pdf_file_objects = []
        
        if not raw_text.strip():
            return jsonify({'success': False, 'error': 'No text could be extracted from the PDFs'}), 400
            
        print("Creating text chunks...")
        text_chunks = get_pdf_chunks(raw_text)
        print(f"Number of chunks created: {len(text_chunks)}")
        
        print("Creating vector store...")
        get_vector_store(text_chunks)
        print("Vector store created successfully")

        return jsonify({
            "success": True,
            "message": "PDFs processed successfully",
            "num_chunks": len(text_chunks)
        })

    except Exception as e:
        print(f"Error in upload: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500
    
    finally:
        # Cleanup file objects
        for pdf_obj in pdf_file_objects:
            try:
                pdf_obj.close()
            except:
                pass
        
        # Cleanup temp files
        for temp_file_path in temp_files:
            try:
                os.unlink(temp_file_path)
            except:
                pass

@app.route('/ask', methods=['POST'])
def ask_question():
    try:
        print("Ask endpoint called")
        
        data = request.get_json()
        if not data or 'question' not in data:
            return jsonify({"success": False, "error": "Question is required"}), 400
        
        question = data['question']
        print(f"Question received: {question}")
        
        # Check if FAISS index exists
        if not os.path.exists("faiss_index"):
            return jsonify({"success": False, "error": "No documents processed yet. Please upload PDFs first."}), 400
        
        # Test API key first
        try:
            print("Testing Google API key...")
            test_embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
            # Simple test to see if API key works
            test_result = test_embeddings.embed_query("test")
            print("API key test successful")
        except Exception as e:
            print(f"API key test failed: {str(e)}")
            return jsonify({"success": False, "error": f"Google API key issue: {str(e)}"}), 500
        
        print("Loading embeddings...")
        embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")
        
        print("Loading FAISS index...")
        try:
            db = CommunityFAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
        except Exception as e:
            print(f"Error loading FAISS index: {str(e)}")
            return jsonify({"success": False, "error": f"Error loading document index: {str(e)}"}), 500
        
        print("Searching for similar documents...")
        try:
            docs = db.similarity_search(question, k=3)  # Limit to 3 documents
            print(f"Found {len(docs)} similar documents")
        except Exception as e:
            print(f"Error in similarity search: {str(e)}")
            return jsonify({"success": False, "error": f"Error searching documents: {str(e)}"}), 500
        
        if not docs:
            return jsonify({
                "success": True,
                "answer": "I couldn't find relevant information in the uploaded documents to answer your question."
            })
        
        print("Getting conversational chain...")
        try:
            chain = get_conversational_chain()
        except Exception as e:
            print(f"Error getting conversational chain: {str(e)}")
            return jsonify({"success": False, "error": f"Error initializing AI model: {str(e)}"}), 500
        
        print("Generating response...")
        try:
            response = chain(
                {"input_documents": docs, "question": question},
                return_only_outputs=True
            )
            print("Response generated successfully")
            
            return jsonify({
                "success": True,
                "answer": response["output_text"]
            })
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return jsonify({"success": False, "error": f"Error generating response: {str(e)}"}), 500
        
    except Exception as e:
        print(f"Unexpected error in ask_question: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": f"Unexpected error: {str(e)}"}), 500

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True)