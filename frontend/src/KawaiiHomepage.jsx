import React, { useState, useEffect } from 'react';
import {
  FileText, Plus, Sparkles, Heart, Star, Zap
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';


import './KawaiiHomepage.css';

const KawaiiHomepage = () => {
const navigate = useNavigate();


  const [mousePosition, setMousePosition] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      setMousePosition({
        x: (e.clientX / window.innerWidth) * 100,
        y: (e.clientY / window.innerHeight) * 100,
      });
    };

    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  

  return (
    <div className="kawaii-homepage">
      {/* Animated Background Elements */}
      <div className="kawaii-bg-wrapper">
        {/* Floating Doodles */}
        <div className="kawaii-doodles">
          {[...Array(20)].map((_, i) => (
            <div
              key={i}
              className={`kawaii-doodle doodle-${i % 8}`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 5}s`,
                animationDuration: `${3 + Math.random() * 4}s`,
              }}
            >
              {['♡', '✨', '🌸', '⭐', '🎀', '🌙', '🦋', '🌈'][i % 8]}
            </div>
          ))}
        </div>

        {/* 3D Geometric Shapes */}
        <div className="kawaii-shapes">
          {[...Array(8)].map((_, i) => (
            <div
              key={i}
              className={`kawaii-shape shape-${i % 4}`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 3}s`,
              }}
            />
          ))}
        </div>

        {/* Animated Gradient Orbs */}
        <div className="kawaii-orbs">
          {[...Array(5)].map((_, i) => (
            <div
              key={i}
              className={`kawaii-orb orb-${i + 1}`}
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
                animationDelay: `${Math.random() * 4}s`,
              }}
            />
          ))}
        </div>

        {/* Mouse Follower */}
        <div
          className="kawaii-mouse-follower"
          style={{
            left: `${mousePosition.x}%`,
            top: `${mousePosition.y}%`,
          }}
        />
      </div>

      {/* Main Content */}
      <div className="kawaii-homepage-content">
        {/* Header */}
        <header className="kawaii-homepage-header">
          <div className="kawaii-logo-container">
            <div className="kawaii-logo-3d">
              <div className="kawaii-logo-face">
                <div className="kawaii-eyes">
                  <div className="kawaii-eye left">◕</div>
                  <div className="kawaii-eye right">◕</div>
                </div>
                <div className="kawaii-mouth">‿</div>
              </div>
              <div className="kawaii-sparkles-around">
                <Sparkles className="sparkle sparkle-1" />
                <Sparkles className="sparkle sparkle-2" />
                <Sparkles className="sparkle sparkle-3" />
                <Sparkles className="sparkle sparkle-4" />
              </div>
            </div>
            <div className="kawaii-title-container">
              <h1 className="kawaii-main-title">
                <span className="kawaii-title-text">PDF Magic</span>
                <span className="kawaii-title-subtitle">✨ Document Assistant ✨</span>
              </h1>
              <p className="kawaii-tagline">
                Transform your PDF(◕‿◕) ♡
              </p>
            </div>
          </div>
        </header>

        {/* Cards Section */}
        <main className="kawaii-main-section">
          <div className="kawaii-cards-container">
            {/* PDF Chat Card */}
            <div
              className="kawaii-card kawaii-card-primary"
              onClick={() =>  navigate('/chat')}
            >
              <div className="kawaii-card-bg"></div>
              <div className="kawaii-card-content">
                <div className="kawaii-card-icon">
                  <FileText className="kawaii-icon-main" />
                  <div className="kawaii-icon-decorations">
                    <Heart className="kawaii-heart-1" />
                    <Star className="kawaii-star-1" />
                    <Zap className="kawaii-zap-1" />
                  </div>
                </div>
                <div className="kawaii-card-text">
                  <h2 className="kawaii-card-title">Know About Your PDF</h2>
                  <p className="kawaii-card-description">
                    Upload your PDFs and have magical conversations with them! 
                    Ask questions, get summaries, and discover insights! ✨
                  </p>
                  <div className="kawaii-card-features">
                    <span className="kawaii-feature">🔍 Smart Analysis</span>
                    <span className="kawaii-feature">💬 Natural Chat</span>
                    <span className="kawaii-feature">🎯 Instant Answers</span>
                  </div>
                </div>
                <div className="kawaii-card-button">
                  <span className="kawaii-button-text">Start Chatting!</span>
                  <div className="kawaii-button-trail">
                    <span>♡</span>
                    <span>✨</span>
                    <span>🌸</span>
                  </div>
                </div>
              </div>
              <div className="kawaii-card-glow"></div>
            </div>

            {/* Create PDF Card */}
            <div className="kawaii-card kawaii-card-secondary" onClick={() => navigate('/create')}>
              <div className="kawaii-card-bg"></div>
              <div className="kawaii-card-content">
                <div className="kawaii-card-icon">
                  <Plus className="kawaii-icon-main" />
                  <div className="kawaii-icon-decorations">
                    <Heart className="kawaii-heart-2" />
                    <Star className="kawaii-star-2" />
                    <Sparkles className="kawaii-sparkles-2" />
                  </div>
                </div>
                <div className="kawaii-card-text">
                  <h2 className="kawaii-card-title">Create Your Own PDF</h2>
                  <p className="kawaii-card-description">
                    Bring your ideas to life! Create beautiful PDFs with our 
                    kawaii-powered document generator! 🌈
                  </p>
                  <div className="kawaii-card-features">
                    <span className="kawaii-feature">🎨 Beautiful Templates</span>
                    <span className="kawaii-feature">✏️ Easy Editor</span>
                    <span className="kawaii-feature">📄 Instant Export</span>
                  </div>
                </div>
                <div className="kawaii-card-button">
                  <span className="kawaii-button-text">Create Magic!</span>
                  <div className="kawaii-button-trail">
                    <span>💫</span>
                    <span>🎀</span>
                    <span>🌟</span>
                  </div>
                </div>
              
              </div>
              <div className="kawaii-card-glow"></div>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="kawaii-footer">
          <div className="kawaii-footer-content">
            <p className="kawaii-footer-text">
              Made with 💖 and lots magic! ✨
            </p>
            <div className="kawaii-footer-hearts">
              <Heart className="kawaii-footer-heart" />
              <Heart className="kawaii-footer-heart" />
              <Heart className="kawaii-footer-heart" />
            </div>
          </div>
        </footer>
      </div>
    </div>
  );
};

export default KawaiiHomepage;
