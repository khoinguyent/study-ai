import React from 'react';
import './App.css';

function App() {
  return (
    <div className="App">
      <header className="App-header">
        <h1>Study AI Platform</h1>
        <p>AI-powered learning platform</p>
        <div className="status">
          <h3>Service Status</h3>
          <ul>
            <li>API Gateway: <span className="status-ok">Running</span></li>
            <li>Auth Service: <span className="status-ok">Running</span></li>
            <li>Document Service: <span className="status-ok">Running</span></li>
            <li>Indexing Service: <span className="status-ok">Running</span></li>
            <li>Quiz Service: <span className="status-ok">Running</span></li>
            <li>Notification Service: <span className="status-ok">Running</span></li>
          </ul>
        </div>
        <div className="links">
          <a href="http://localhost:8000/docs" target="_blank" rel="noopener noreferrer">
            API Documentation
          </a>
          <a href="http://localhost:9001" target="_blank" rel="noopener noreferrer">
            MinIO Console
          </a>
        </div>
      </header>
    </div>
  );
}

export default App; 