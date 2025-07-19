import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import {
  Upload, Send, FileText, MessageCircle, Sparkles, Bot,
  User, Loader2, CheckCircle, Heart, Star, X, Mic, MicOff
} from 'lucide-react';

const KawaiiPDFChatbot = () => {
  const [files, setFiles] = useState([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isProcessed, setIsProcessed] = useState(false);
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  
  // Voice recognition states
  const [isListening, setIsListening] = useState(false);
  const [recognition, setRecognition] = useState(null);
  const [isVoiceSupported, setIsVoiceSupported] = useState(false);
  
  const fileInputRef = useRef(null);
  const messagesEndRef = useRef(null);

  // Initialize speech recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      const recognitionInstance = new SpeechRecognition();
      
      recognitionInstance.continuous = false;
      recognitionInstance.interimResults = false;
      recognitionInstance.lang = 'en-US';
      
      recognitionInstance.onstart = () => {
        setIsListening(true);
      };
      
      recognitionInstance.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputMessage(prev => prev + transcript);
      };
      
      recognitionInstance.onerror = (event) => {
        console.error('Speech recognition error:', event.error);
        setIsListening(false);
        if (event.error === 'not-allowed') {
          alert('Microphone access denied. Please enable microphone permissions.');
        }
      };
      
      recognitionInstance.onend = () => {
        setIsListening(false);
      };
      
      setRecognition(recognitionInstance);
      setIsVoiceSupported(true);
    } else {
      setIsVoiceSupported(false);
    }
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = (event) => {
    const uploadedFiles = Array.from(event.target.files);
    const pdfFiles = uploadedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== uploadedFiles.length) {
      alert('Please upload only PDF files!');
    }
    
    setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
  };

  const removeFile = (indexToRemove) => {
    setFiles(prevFiles => prevFiles.filter((_, index) => index !== indexToRemove));
  };

  const handleProcessFiles = async () => {
    if (files.length === 0) {
      alert('Please upload at least one PDF file!');
      return;
    }
    
    setIsProcessing(true);
    setIsProcessed(false);

    try {
      const formData = new FormData();
      files.forEach(file => {
        formData.append("pdfs", file);
      });

      const response = await axios.post("http://localhost:5000/upload", formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 30000,
      });

      if (response.data.success) {
        setIsProcessed(true);
        setMessages([{
          type: 'system',
          content: `✨ Yay! Successfully processed ${files.length} PDF file${files.length > 1 ? 's' : ''}! (◕‿◕) Now you can ask me anything about your documents! ♡`,
          timestamp: new Date().toLocaleTimeString()
        }]);
        console.log('Upload successful:', response.data.message);
      } else {
        throw new Error(response.data.error || 'Upload failed');
      }
    } catch (error) {
      console.error("Upload failed:", error);
      const errorMessage = error.response?.data?.error || error.message || 'Upload failed';
      setMessages([{
        type: 'system',
        content: `❌ Oops! Upload failed: ${errorMessage}`,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } finally {
      setIsProcessing(false);
    }
  };

  const clearFiles = () => {
    setFiles([]);
    setIsProcessed(false);
    setMessages([]);
  };

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;
    
    if (!isProcessed) {
      alert('Please upload and process PDFs first!');
      return;
    }

    const userMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    const currentQuestion = inputMessage;
    setInputMessage('');
    setIsTyping(true);

    try {
      const response = await axios.post("http://localhost:5000/ask", {
        question: currentQuestion,
      }, {
        headers: {
          'Content-Type': 'application/json'
        },
        timeout: 30000,
      });

      if (response.data.success) {
        const aiMessage = {
          type: 'ai',
          content: response.data.answer,
          timestamp: new Date().toLocaleTimeString(),
        };
        setMessages(prev => [...prev, aiMessage]);
      } else {
        throw new Error(response.data.error || 'Failed to get answer');
      }
    } catch (error) {
      console.error("Error fetching answer:", error);
      const errorContent = error.response?.data?.error || 
                           error.message || 
                           "Oops! Something went wrong. (｡•́︿•̀｡)";
      const errorMessage = {
        type: 'ai',
        content: `❌ ${errorContent}`,
        timestamp: new Date().toLocaleTimeString(),
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  // Voice recognition handlers
  const startListening = () => {
    if (recognition && isVoiceSupported && !isListening) {
      try {
        recognition.start();
      } catch (error) {
        console.error('Error starting recognition:', error);
      }
    }
  };

  const stopListening = () => {
    if (recognition && isListening) {
      recognition.stop();
    }
  };

  const toggleListening = () => {
    if (isListening) {
      stopListening();
    } else {
      startListening();
    }
  };

  // Drag and drop functionality
  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFiles = Array.from(e.dataTransfer.files);
    const pdfFiles = droppedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length !== droppedFiles.length) {
      alert('Please upload only PDF files!');
    }
    
    setFiles(prevFiles => [...prevFiles, ...pdfFiles]);
  };

  return (
    <div className="kawaii-container">
      {/* Kawaii Background Elements */}
      <div className="kawaii-bg">
        {[...Array(15)].map((_, i) => (
          <div
            key={i}
            className={`kawaii-float kawaii-float-${i % 5}`}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 100}%`,
              animationDelay: `${Math.random() * 3}s`
            }}
          >
            {i % 5 === 0 && '♡'}
            {i % 5 === 1 && '✨'}
            {i % 5 === 2 && '🌸'}
            {i % 5 === 3 && '⭐'}
            {i % 5 === 4 && '🎀'}
          </div>
        ))}
      </div>

      {/* Kawaii Clouds */}
      <div className="kawaii-clouds">
        {[...Array(6)].map((_, i) => (
          <div
            key={i}
            className={`kawaii-cloud kawaii-cloud-${i + 1}`}
            style={{
              left: `${Math.random() * 100}%`,
              top: `${Math.random() * 30 + 10}%`,
              animationDelay: `${Math.random() * 5}s`
            }}
          >
            ☁️
          </div>
        ))}
      </div>

      <div className="kawaii-main">
        {/* Header */}
        <div className="kawaii-header">
          <div className="kawaii-header-content">
            <div className="kawaii-logo">
              <div className="kawaii-logo-icon">
                <Bot className="kawaii-bot-icon" />
                <div className="kawaii-sparkles">✨</div>
              </div>
              <div className="kawaii-title">
                <h1>PDF Assistant</h1>
                <p>Upload PDFs and chat with them!(◕‿◕) ♡</p>
              </div>
            </div>
          </div>
        </div>

        <div className="kawaii-content">
          {/* Sidebar */}
          <div className={`kawaii-sidebar ${sidebarOpen ? 'open' : 'closed'}`}>
            <div className="kawaii-sidebar-header">
              <h2 className="kawaii-sidebar-title">
                <Upload className="kawaii-icon" />
                Upload PDFs ♡
              </h2>
              <button 
                className="kawaii-sidebar-toggle"
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                {sidebarOpen ? '◀' : '▶'}
              </button>
            </div>

            <div className="kawaii-upload-area">
              <div 
                className="kawaii-dropzone"
                onClick={() => fileInputRef.current?.click()}
                onDragOver={handleDragOver}
                onDrop={handleDrop}
              >
                <div className="kawaii-dropzone-content">
                  <div className="kawaii-upload-icon">📁</div>
                  <div className="kawaii-upload-text">
                    <p className="kawaii-upload-main">Click to upload PDFs!</p>
                    <p className="kawaii-upload-sub">or drag and drop ♡</p>
                  </div>
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="kawaii-hidden"
                />
              </div>

              {files.length > 0 && (
                <div className="kawaii-files-section">
                  <div className="kawaii-files-header">
                    <h3>Uploaded Files ✨</h3>
                    <button onClick={clearFiles} className="kawaii-clear-btn">
                      Clear All
                    </button>
                  </div>
                  <div className="kawaii-files-list">
                    {files.map((file, index) => (
                      <div key={index} className="kawaii-file-item">
                        <FileText className="kawaii-file-icon" />
                        <span className="kawaii-file-name">{file.name}</span>
                        <button
                          onClick={() => removeFile(index)}
                          className="kawaii-remove-btn"
                        >
                          <X className="kawaii-x-icon" />
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              <button
                onClick={handleProcessFiles}
                disabled={files.length === 0 || isProcessing}
                className={`kawaii-process-btn ${isProcessing ? 'processing' : ''} ${isProcessed ? 'processed' : ''}`}
              >
                {isProcessing ? (
                  <>
                    <Loader2 className="kawaii-spinner" />
                    Processing... ♡
                  </>
                ) : isProcessed ? (
                  <>
                    <CheckCircle className="kawaii-check" />
                    Ready to chat! ✨
                  </>
                ) : (
                  <>
                    <Sparkles className="kawaii-sparkle" />
                    Process PDFs ♡
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Chat Area */}
          <div className="kawaii-chat-area">
            <div className="kawaii-chat-container">
              <div className="kawaii-chat-header">
                <MessageCircle className="kawaii-chat-icon" />
                <h2>Chat with your Documents ♡</h2>
                {isVoiceSupported && (
                  <div className="kawaii-voice-status">
                    <Mic className="kawaii-mic-icon" />
                    <span>Voice enabled ✨</span>
                  </div>
                )}
              </div>

              <div className="kawaii-messages">
                {messages.length === 0 && (
                  <div className="kawaii-welcome">
                    <div className="kawaii-welcome-icon">🤖</div>
                    <div className="kawaii-welcome-text">
                      <p className="kawaii-welcome-main">
                        {isProcessed ? "Ask me anything about your documents! (◕‿◕) ♡" : "Upload and process PDFs to start our chat! ✨"}
                      </p>
                      {isVoiceSupported && isProcessed && (
                        <p className="kawaii-welcome-sub">
                          You can type or use voice input! 🎤
                        </p>
                      )}
                    </div>
                  </div>
                )}

                {messages.map((message, index) => (
                  <div key={index} className={`kawaii-message ${message.type}`}>
                    <div className="kawaii-message-content">
                      <div className="kawaii-message-avatar">
                        {message.type === 'user' ? '👤' : message.type === 'system' ? '🎉' : '🤖'}
                      </div>
                      <div className="kawaii-message-bubble">
                        <p style={{ whiteSpace: 'pre-wrap' }}>{message.content}</p>
                        {message.timestamp && (
                          <span className="kawaii-timestamp">{message.timestamp}</span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}

                {isTyping && (
                  <div className="kawaii-message ai">
                    <div className="kawaii-message-content">
                      <div className="kawaii-message-avatar">🤖</div>
                      <div className="kawaii-message-bubble kawaii-typing">
                        <div className="kawaii-typing-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              <div className="kawaii-input-area">
                <div className="kawaii-input-container">
                  <input
                    type="text"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder={isProcessed ? "Ask me something about your docs! ♡" : "Process PDFs first... (◕‿◕)"}
                    disabled={!isProcessed || isTyping}
                    className="kawaii-input"
                  />
                  
                  {/* Voice Input Button */}
                  {isVoiceSupported && (
                    <button
                      onClick={toggleListening}
                      disabled={!isProcessed || isTyping}
                      className={`kawaii-voice-btn ${isListening ? 'listening' : ''}`}
                      title={isListening ? 'Stop listening' : 'Start voice input'}
                    >
                      {isListening ? (
                        <MicOff className="kawaii-mic-icon pulsing" />
                      ) : (
                        <Mic className="kawaii-mic-icon" />
                      )}
                    </button>
                  )}
                  
                  <button
                    onClick={handleSendMessage}
                    disabled={!inputMessage.trim() || !isProcessed || isTyping}
                    className="kawaii-send-btn"
                  >
                    <Send className="kawaii-send-icon" />
                  </button>
                </div>
                
                {/* Voice Status Indicator */}
                {isListening && (
                  <div className="kawaii-voice-indicator">
                    <div className="kawaii-voice-waves">
                      <span></span>
                      <span></span>
                      <span></span>
                    </div>
                    <p>Listening... Speak now! 🎤</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div> 
  );
};  
export default KawaiiPDFChatbot;