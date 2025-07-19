import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import KawaiiHomepage from './KawaiiHomepage.jsx';
import KawaiiPDFChatbot from './multi_pdf.js'; 
import PDFCreator from './pdf'; // NEW
import './multi_pdf.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<KawaiiHomepage />} />
        <Route path="/chat" element={<KawaiiPDFChatbot />} />
        <Route path="/create" element={<PDFCreator />} />
      </Routes>
    </Router>
  );
}

export default App;
