import React, { useState, useRef } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Mail, Lock, Crown, Brain } from "lucide-react";
import { LoginRequest } from "../types";
import apiService from "../services/api";
import authService from "../services/auth";
import "./LoginPage.css";

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const renderCount = useRef(0);
  renderCount.current += 1;

  console.log("🔄 LoginPage render #", renderCount.current);

  const [formData, setFormData] = useState<LoginRequest>({
    email: "",
    password: "",
  });
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [error, setError] = useState<string>("");

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>): void => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error when user starts typing
    if (error) {
      setError("");
    }
  };

  const handleSubmit = async (
    e: React.FormEvent<HTMLFormElement>
  ): Promise<void> => {
    e.preventDefault();
    setIsLoading(true);
    setError("");

    try {
      const response = await apiService.login(formData);
      authService.setToken(response);
      // Navigate to dashboard using React Router
      navigate("/dashboard");
    } catch (error) {
      console.error("Login error:", error);
      setError(
        error instanceof Error
          ? error.message
          : "Login failed. Please try again."
      );
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
          <h1 className="welcome-text">Sign In</h1>
          <p className="welcome-subtitle">Study <b>Freely</b> with your <b>AI Friend</b></p>
        </div>

        {/* Login Form */}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email" className="form-label">
              Email Address
            </label>
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
            <label htmlFor="password" className="form-label">
              Password
            </label>
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

          {error && <div className="error-message">{error}</div>}

          <button type="submit" className="signin-button" disabled={isLoading}>
            {/* <Crown className="button-icon" size={20} /> */}
            {isLoading ? "Signing In..." : "Sign In"}
          </button>
        </form>

        {/* Account Creation Link */}
        <div className="signup-link">
          <span>Don't have an account? </span>
          <Link to="/signup" className="signup-text">
            Sign Up
          </Link>
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
