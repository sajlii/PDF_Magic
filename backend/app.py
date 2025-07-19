from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import tempfile
import traceback
import time
import random
import unicodedata
from io import BytesIO
import urllib.parse
from dotenv import load_dotenv

# PDF Chatbot imports
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from langchain.vectorstores import FAISS
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores import FAISS as CommunityFAISS

# PDF Creator imports
import requests
from bs4 import BeautifulSoup
from fpdf import FPDF

# Load environment variables and configure GenAI
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Initialize Flask
app = Flask(__name__)
CORS(app)  # Enable CORS for React or other frontends

# =============================================================================
# PDF CHATBOT FUNCTIONS
# =============================================================================

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

# =============================================================================
# PDF CREATOR FUNCTIONS
# =============================================================================

def get_random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:89.0) Gecko/20100101 Firefox/89.0"
    ]
    return random.choice(user_agents)

def search_google_improved(topic, num_results=5):
    """Improved Google search with better scraping"""
    query = topic.replace(" ", "+")
    url = f"https://www.google.com/search?q={query}&num={num_results}"
    
    headers = {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    try:
        print(f"Searching Google for: {topic}")
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Look for search result links
        links = []
        search_results = soup.find_all('div', class_='g')
        
        for result in search_results:
            link_tag = result.find('a')
            if link_tag and link_tag.get('href'):
                href = link_tag.get('href')
                if href.startswith('/url?q='):
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    actual_url = urllib.parse.unquote(actual_url)
                    if actual_url.startswith('http') and 'google.com' not in actual_url:
                        links.append(actual_url)
                        if len(links) >= num_results:
                            break
        
        # Alternative method if first one fails
        if not links:
            for link in soup.find_all('a'):
                href = link.get('href')
                if href and href.startswith('/url?q='):
                    actual_url = href.split('/url?q=')[1].split('&')[0]
                    actual_url = urllib.parse.unquote(actual_url)
                    if actual_url.startswith('http') and 'google.com' not in actual_url:
                        links.append(actual_url)
                        if len(links) >= num_results:
                            break
        
        print(f"Found {len(links)} URLs: {links}")
        return links
        
    except Exception as e:
        print(f"Error searching Google: {e}")
        return []

def extract_article_content(url):
    """Extract meaningful content from a webpage"""
    try:
        headers = {"User-Agent": get_random_user_agent()}
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try to find main content areas
        content_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.main-content',
            '.post-content',
            '.entry-content',
            '.article-content',
            'main',
            '.container'
        ]
        
        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content = elements[0].get_text()
                break
        
        # If no specific content area found, get body text
        if not content:
            body = soup.find('body')
            if body:
                content = body.get_text()
        
        # Clean up the text
        lines = (line.strip() for line in content.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        clean_content = ' '.join(chunk for chunk in chunks if chunk)
        
        # Return first 2000 characters to keep it manageable
        return clean_content[:2000] if clean_content else ""
        
    except Exception as e:
        print(f"Error extracting content from {url}: {e}")
        return ""

def generate_ai_content(topic, scraped_content=""):
    """Generate content using local Ollama model"""
    try:
        prompt = f"""
        Create a comprehensive, informative article about "{topic}". 

        The article should include:
        1. An introduction explaining what {topic} is
        2. Key concepts and definitions
        3. Main applications and use cases
        4. Benefits and advantages
        5. Challenges or limitations
        6. Current trends and future outlook
        7. Conclusion

        Additional context from web sources:
        {scraped_content[:1000] if scraped_content else "No additional context available"}

        Make the content educational, well-structured, and approximately 800-1000 words.
        """

        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "llama3",
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )

        if response.status_code == 200:
            result = response.json()
            return result.get("response", generate_fallback_content(topic, scraped_content))
        else:
            return generate_fallback_content(topic, scraped_content)

    except Exception as e:
        print(f"Error using local model: {e}")
        return generate_fallback_content(topic, scraped_content)

def generate_fallback_content(topic, scraped_content=""):
    """Generate content without AI when API is not available"""
    if scraped_content:
        return f"""
{topic.upper()}

Overview:
This document provides comprehensive information about {topic} based on available sources and research.

Introduction:
{topic} is a significant subject that encompasses various concepts, applications, and developments in its field. Understanding {topic} is crucial for professionals, students, and anyone interested in this domain.

Key Concepts and Definitions:
{topic} involves several fundamental concepts that form the foundation of understanding in this area. These concepts are essential for grasping the broader implications and applications of {topic}.

Content Summary from Research:
{scraped_content[:800]}

Main Applications and Use Cases:
{topic} finds applications across multiple industries and sectors. The versatility of {topic} makes it valuable in various contexts, from theoretical research to practical implementation.

Benefits and Advantages:
• Enhanced understanding of complex systems
• Improved efficiency in relevant processes
• Better decision-making capabilities
• Innovation opportunities
• Competitive advantages in the market

Current Trends and Future Outlook:
The field of {topic} continues to evolve with technological advances and changing market demands. Current research and development efforts are focused on improving existing methodologies and exploring new possibilities.

Challenges and Limitations:
While {topic} offers numerous benefits, there are also challenges that need to be addressed. These include technical limitations, resource constraints, and implementation difficulties.

Conclusion:
{topic} represents an important area of study and application with significant practical implications. As the field continues to evolve, it will likely play an increasingly important role in various industries and sectors. For more comprehensive information, consulting specialized resources and current literature is recommended.

Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """
    else:
        return f"""
{topic.upper()}

Introduction:
{topic} is a significant subject that encompasses various concepts and applications across multiple domains. This comprehensive guide provides an overview of the key aspects of {topic}.

Fundamental Concepts:
Understanding {topic} requires familiarity with its core principles and theoretical foundations. These concepts form the basis for more advanced applications and developments in the field.

Historical Context:
The development of {topic} has been shaped by various factors including technological advances, research breakthroughs, and practical needs across different industries.

Current Applications:
{topic} finds applications in numerous sectors and continues to evolve with technological advances. Key areas include:
• Research and development
• Industrial applications
• Educational purposes
• Commercial implementations
• Innovation initiatives

Technical Aspects:
The technical components of {topic} involve various methodologies, tools, and approaches that contribute to its effectiveness and applicability.

Benefits and Advantages:
• Improved understanding of complex systems
• Enhanced problem-solving capabilities
• Better resource utilization
• Innovation opportunities
• Competitive advantages

Challenges and Considerations:
While {topic} offers numerous benefits, there are challenges that need to be addressed including technical limitations, resource requirements, and implementation complexities.

Future Prospects:
Research and development in {topic} are ongoing, with new discoveries and innovations being made regularly. The future outlook appears promising with continued advances expected.

Best Practices:
Successful implementation of {topic} requires adherence to established best practices and continuous learning to stay current with developments.

Conclusion:
{topic} represents an important area of study with significant practical implications. As the field continues to evolve, it will likely play an increasingly important role in various applications and industries.

Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}
        """

def clean_text_for_pdf(text):
    """Clean text for PDF generation"""
    replacements = {
        '\u2013': '-',  # en dash
        '\u2014': '-',  # em dash
        '\u2018': "'",  # left single quote
        '\u2019': "'",  # right single quote
        '\u201c': '"',  # left double quote
        '\u201d': '"',  # right double quote
        '\u2022': '•',  # bullet
        '\u00a0': ' ',  # non-breaking space
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    text = unicodedata.normalize("NFKD", text)
    return text.encode("latin-1", errors="ignore").decode("latin-1")

def create_pdf_with_content(title, content):
    """Create a well-formatted PDF"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_auto_page_break(auto=True, margin=15)

        # Use built-in fonts
        pdf.set_font("Arial", "B", 18)
        
        # Title
        pdf.cell(0, 15, clean_text_for_pdf(title), ln=True, align='C')
        pdf.ln(10)

        # Set default font for body
        pdf.set_font("Arial", "", 11)

        # Clean content
        content = clean_text_for_pdf(content)
        
        # Split content into paragraphs
        paragraphs = content.split('\n\n')

        for paragraph in paragraphs:
            if paragraph.strip():
                text = paragraph.strip()
                # Handle bullet points
                if text.startswith('•'):
                    pdf.set_font("Arial", "", 10)
                    pdf.multi_cell(0, 6, text)
                    pdf.ln(2)
                # Handle headers (all caps or starting with numbers)
                elif text.isupper() or (text and text[0].isdigit()):
                    pdf.set_font("Arial", "B", 12)
                    pdf.multi_cell(0, 8, text)
                    pdf.ln(3)
                else:
                    pdf.set_font("Arial", "", 11)
                    pdf.multi_cell(0, 6, text)
                    pdf.ln(4)

        # Footer
        pdf.ln(10)
        pdf.set_font("Arial", "", 8)
        pdf.cell(0, 10, f"Generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align='C')

        # Create BytesIO and return the PDF bytes
        output = BytesIO()
        pdf_content = pdf.output(dest='S')
        
        # Handle both string and bytes output
        if isinstance(pdf_content, str):
            output.write(pdf_content.encode('latin-1'))
        else:
            output.write(pdf_content)
        
        output.seek(0)
        return output

    except Exception as e:
        print(f"Error creating PDF: {e}")
        import traceback
        traceback.print_exc()
        return None

# =============================================================================
# COMMON ENDPOINTS
# =============================================================================

@app.route('/', methods=['GET'])
def health_check():
    return jsonify({
        "message": "Combined PDF Chat & Creator API is running!",
        "success": True,
        "endpoints": {
            "pdf_chatbot": {
                "upload": "/chatbot/upload",
                "ask": "/chatbot/ask",
                "test": "/chatbot/test-api"
            },
            "pdf_creator": {
                "generate": "/creator/generate_pdf",
                "test": "/creator/test_pdf"
            }
        }
    })

# =============================================================================
# PDF CHATBOT ENDPOINTS
# =============================================================================

@app.route('/chatbot/test-api', methods=['GET'])
def test_chatbot_api():
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

@app.route('/chatbot/upload', methods=['POST'])
def upload_pdfs():
    temp_files = []
    pdf_file_objects = []
    
    try:
        print("PDF Chatbot upload endpoint called")
        
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

@app.route('/chatbot/ask', methods=['POST'])
def ask_question():
    try:
        print("PDF Chatbot ask endpoint called")
        
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

# =============================================================================
# PDF CREATOR ENDPOINTS
# =============================================================================

@app.route("/creator/generate_pdf", methods=["POST"])
def create_pdf():
    try:
        data = request.get_json()
        topic = data.get("topic", "").strip()
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        print(f"Starting PDF generation for: {topic}")
        
        # Step 1: Search Google for URLs
        urls = search_google_improved(topic)
        
        # Step 2: Extract content from URLs
        scraped_content = ""
        successful_scrapes = 0
        
        for i, url in enumerate(urls[:3]):  # Limit to first 3 URLs
            print(f"Scraping URL {i+1}: {url}")
            content = extract_article_content(url)
            if content and len(content) > 200:
                scraped_content += content + "\n\n"
                successful_scrapes += 1
                print(f"Successfully scraped {len(content)} characters")
            
            # Add delay to avoid being blocked
            time.sleep(random.uniform(1, 3))
        
        print(f"Successfully scraped {successful_scrapes} sources")
        
        # Step 3: Generate comprehensive content using AI
        print("Generating AI content...")
        final_content = generate_ai_content(topic, scraped_content)
        
        # Step 4: Create PDF
        pdf_file = create_pdf_with_content(topic, final_content)
        
        if pdf_file and len(pdf_file.getvalue()) > 0:
            print(f"PDF created successfully. Size: {len(pdf_file.getvalue())} bytes")
            pdf_file.seek(0)
            return send_file(
                pdf_file,
                download_name=f"{topic.replace(' ', '_')}_comprehensive.pdf",
                as_attachment=True,
                mimetype='application/pdf'
            )
        else:
            return jsonify({"error": "Failed to generate PDF"}), 500
            
    except Exception as e:
        print(f"Error in PDF generation: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@app.route("/creator/test_pdf", methods=["GET"])
def test_pdf():
    try:
        test_content = """
TEST DOCUMENT

Introduction:
This is a test PDF to verify that the PDF generation system is working correctly.

Features:
• Proper formatting
• Multiple paragraphs
• Bullet points
• Headers and sections

Technical Details:
The PDF generation uses FPDF library with proper text encoding to ensure compatibility across different systems.

Conclusion:
If you can see this formatted text, the PDF generation is working properly.
        """
        
        pdf_file = create_pdf_with_content("Test Document", test_content)
        
        if pdf_file:
            return send_file(
                pdf_file,
                download_name="test_document.pdf",
                as_attachment=True,
                mimetype='application/pdf'
            )
        else:
            return jsonify({"error": "Test PDF generation failed"}), 500
            
    except Exception as e:
        return jsonify({"error": f"Test failed: {str(e)}"}), 500

# Run Flask app
if __name__ == '__main__':
    app.run(debug=True, port=5000)