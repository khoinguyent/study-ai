import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { Mail, Lock, Crown, Brain } from 'lucide-react';
import './LoginPage.css';

const LoginPage = () => {
  const [formData, setFormData] = useState({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    
    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (response.ok) {
        const data = await response.json();
        localStorage.setItem('token', data.access_token);
        // Redirect to dashboard or home page
        window.location.href = '/dashboard';
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Login failed');
      }
    } catch (error) {
      console.error('Login error:', error);
      alert('Login failed. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        {/* Header/Branding */}
        <div className="login-header">
          <div className="logo">
            <div className="logo-icon">
              <Brain size={24} />
            </div>
          </div>
          <h1 className="welcome-text">Welcome Back</h1>
          <p className="welcome-subtitle">Sign in to your StudyAI account</p>
        </div>

        {/* Login Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email" className="form-label">Email Address</label>
            <div className="input-container">
              <Mail className="input-icon" size={20} />
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                placeholder="Enter your email"
                className="form-input"
                required
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="password" className="form-label">Password</label>
            <div className="input-container">
              <Lock className="input-icon" size={20} />
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                placeholder="Enter your password"
                className="form-input"
                required
              />
            </div>
          </div>

          <button 
            type="submit" 
            className="signin-button"
            disabled={isLoading}
          >
            <Crown className="button-icon" size={20} />
            {isLoading ? 'Signing In...' : 'Sign In'}
          </button>
        </form>

        {/* Account Creation Link */}
        <div className="signup-link">
          <span>Don't have an account? </span>
          <Link to="/signup" className="signup-text">Sign Up</Link>
        </div>

        {/* Premium Features Section */}
        <div className="premium-features">
          <div className="premium-header">
            <Crown className="premium-icon" size={20} />
            <span className="premium-title">Premium Features</span>
          </div>
          <ul className="premium-list">
            <li>Organized document folders</li>
            <li>Unlimited question generation</li>
            <li>Advanced analytics & progress tracking</li>
            <li>Priority AI processing</li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default LoginPage; 