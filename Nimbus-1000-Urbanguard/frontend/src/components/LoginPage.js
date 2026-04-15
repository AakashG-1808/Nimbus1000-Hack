import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { login, signup } from '../services/auth';
import './LoginPage.css';

/**
 * LoginPage component with login/signup toggle
 * Supports citizen and admin roles
 */
const LoginPage = ({ onAuthSuccess }) => {
  const [isSignup, setIsSignup] = useState(false);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('citizen');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      let user;
      if (isSignup) {
        user = await signup(email, password, role);
      } else {
        user = await login(email, password);
      }
      if (onAuthSuccess) onAuthSuccess(user);
      navigate('/');
    } catch (err) {
      setError(err.message || 'Authentication failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div className="login-header">
          <div className="login-logo">🏙️</div>
          <h1>UrbanGuard AI</h1>
          <p className="login-subtitle">Smart Civic Infrastructure Monitoring</p>
        </div>

        <div className="auth-toggle">
          <button
            className={`toggle-btn ${!isSignup ? 'active' : ''}`}
            onClick={() => { setIsSignup(false); setError(''); }}
            type="button"
          >
            Sign In
          </button>
          <button
            className={`toggle-btn ${isSignup ? 'active' : ''}`}
            onClick={() => { setIsSignup(true); setError(''); }}
            type="button"
          >
            Create Account
          </button>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          <div className="form-field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              required
              autoComplete="email"
            />
          </div>

          <div className="form-field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              required
              minLength={6}
              autoComplete={isSignup ? 'new-password' : 'current-password'}
            />
          </div>

          {isSignup && (
            <div className="form-field">
              <label htmlFor="role">Role</label>
              <select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value)}
              >
                <option value="citizen">🏠 Citizen</option>
                <option value="admin">🛡️ Admin (City Official)</option>
              </select>
            </div>
          )}

          {error && <div className="auth-error">{error}</div>}

          <button type="submit" className="submit-btn" disabled={loading}>
            {loading
              ? 'Please wait...'
              : isSignup
                ? 'Create Account'
                : 'Sign In'}
          </button>
        </form>

        <p className="login-footer">
          {isSignup
            ? 'Already have an account? '
            : "Don't have an account? "}
          <button
            className="link-btn"
            onClick={() => { setIsSignup(!isSignup); setError(''); }}
            type="button"
          >
            {isSignup ? 'Sign in' : 'Create one'}
          </button>
        </p>
      </div>
    </div>
  );
};

export default LoginPage;
