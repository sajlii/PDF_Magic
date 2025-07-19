import { useState, useEffect } from 'react';
import './pdf.css';

function App() {
  const [topic, setTopic] = useState('');
  const [pdfUrl, setPdfUrl] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPreview, setShowPreview] = useState(false);

  useEffect(() => {
    const emojis = ['🌸', '✨', '🦋', '💫', '🌙', '⭐', '🌈', '🎀', '🧸', '💖', '🌺', '🦄', '🍀', '🌟', '🎭'];
    const emojiElements = [];

    // Position data for each emoji
    const positions = [
      { top: '10%', left: '15%' },
      { top: '20%', left: '80%' },
      { top: '30%', left: '5%' },
      { top: '40%', left: '70%' },
      { top: '50%', left: '25%' },
      { top: '60%', left: '90%' },
      { top: '70%', left: '10%' },
      { top: '80%', left: '60%' },
      { top: '15%', left: '45%' },
      { top: '35%', left: '35%' },
      { top: '55%', left: '75%' },
      { top: '75%', left: '30%' },
      { top: '5%', left: '55%' },
      { top: '25%', left: '20%' },
      { top: '45%', left: '85%' }
    ];

    emojis.forEach((emoji, index) => {
      const emojiDiv = document.createElement('div');
      emojiDiv.textContent = emoji;
      emojiDiv.className = `floating-emoji emoji-${index + 1}`;
      emojiDiv.style.fontSize = Math.random() * 1 + 1.5 + 'rem';
      emojiDiv.style.color = `rgba(255, 255, 255, ${Math.random() * 0.3 + 0.2})`;
      emojiDiv.style.position = 'fixed';
      emojiDiv.style.top = positions[index].top;
      emojiDiv.style.left = positions[index].left;
      emojiDiv.style.zIndex = '-1';
      emojiDiv.style.pointerEvents = 'none';
      emojiDiv.style.userSelect = 'none';
      
      // Add a unique identifier to track elements
      emojiDiv.setAttribute('data-emoji-id', `emoji-${index}`);
      
      document.body.appendChild(emojiDiv);
      emojiElements.push(emojiDiv);
    });

    // Cleanup function with better error handling
    return () => {
      emojiElements.forEach((el) => {
        try {
          if (el && el.parentNode && el.parentNode === document.body) {
            document.body.removeChild(el);
          }
        } catch (error) {
          // Silently ignore errors - element might already be removed
          console.debug('Element already removed or not found:', error);
        }
      });
    };
  }, []);

  const handleGenerate = async () => {
    if (!topic.trim()) {
      setError('Please enter a topic');
      return;
    }

    setLoading(true);
    setError('');
    setPdfUrl(null);
    setShowPreview(false);

    try {
      const response = await fetch('http://localhost:5000/generate_pdf', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to generate PDF');
      }

      // Get the PDF as blob
      const blob = await response.blob();
      
      // Create URL for the blob
      const url = URL.createObjectURL(blob);
      setPdfUrl(url);
      
    } catch (err) {
      console.error('Error generating PDF:', err);
      setError(err.message || 'Failed to generate PDF. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const downloadPdf = () => {
    if (!pdfUrl) return;

    try {
      const link = document.createElement('a');
      link.href = pdfUrl;
      link.download = `${topic.replace(/[^a-z0-9]/gi, '_')}_comprehensive.pdf`;
      link.style.display = 'none';
      
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (error) {
      console.error('Error downloading PDF:', error);
      setError('Failed to download PDF. Please try again.');
    }
  };

  const togglePreview = () => {
    setShowPreview(!showPreview);
  };

  // Cleanup URL when component unmounts or new PDF is generated
  useEffect(() => {
    return () => {
      if (pdfUrl) {
        URL.revokeObjectURL(pdfUrl);
      }
    };
  }, [pdfUrl]);

  return (
    <div className="container">
      <div className="pdf-generator">
        <div className="header">
          <h1>AI PDF Generator</h1>
          <p>Enter a topic and generate a comprehensive PDF document</p>
        </div>

        {/* Input Section */}
        <div className="input-section">
          <div className="input-group">
            <input
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="Enter topic (e.g., Artificial Intelligence, Climate Change, etc.)"
              className="topic-input"
              disabled={loading}
              onKeyPress={(e) => e.key === 'Enter' && handleGenerate()}
            />
            <button
              onClick={handleGenerate}
              disabled={loading || !topic.trim()}
              className="generate-btn"
            >
              {loading ? 'Generating...' : 'Generate PDF'}
            </button>
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <span>⚠️ {error}</span>
          </div>
        )}

        {/* Loading Progress */}
        {loading && (
          <div className="loading-section">
            <div className="loading-text">
              <span>🔄 Generating your PDF...</span>
            </div>
            <div className="progress-bar">
              <div className="progress-fill"></div>
            </div>
            <p className="loading-note">
              This may take 30-60 seconds as we research and compile your document.
            </p>
          </div>
        )}

        {/* Success Section */}
        {pdfUrl && (
          <div className="success-section">
            <div className="success-header">
              <span>📄 PDF Generated Successfully!</span>
            </div>
            
            <div className="action-buttons">
              <button
                onClick={downloadPdf}
                className="download-btn"
              >
                📥 Download PDF
              </button>
              
              <button
                onClick={togglePreview}
                className="preview-btn"
              >
                👁️ {showPreview ? 'Hide Preview' : 'Show Preview'}
              </button>
            </div>
          </div>
        )}

        {/* PDF Preview */}
        {pdfUrl && showPreview && (
          <div className="preview-section">
            <div className="preview-container">
              <h3>PDF Preview</h3>
              <div className="pdf-frame">
                <iframe
                  src={pdfUrl}
                  width="100%"
                  height="600"
                  title="PDF Preview"
                />
              </div>
              <p className="preview-note">
                If the preview doesn't load, try downloading the PDF directly.
              </p>
            </div>
          </div>
        )}

        {/* Instructions */}
        <div className="instructions">
          <h3>How it works:</h3>
          <ol>
            <li>
              <span className="step-number">1</span>
              <span>Enter any topic you want to learn about</span>
            </li>
            <li>
              <span className="step-number">2</span>
              <span>Our AI searches the web for relevant information</span>
            </li>
            <li>
              <span className="step-number">3</span>
              <span>Generates a comprehensive PDF document</span>
            </li>
            <li>
              <span className="step-number">4</span>
              <span>Preview and download your document</span>
            </li>
          </ol>
        </div>
      </div>
    </div>
  );
}

export default App;