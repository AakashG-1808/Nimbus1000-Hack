/**
 * Auth Service
 * Handles user authentication with local JWT (Cognito-compatible for production)
 * 
 * In production, replace the login/signup calls with Cognito SDK
 * For local dev, uses the backend /auth endpoints
 */

const AUTH_TOKEN_KEY = 'urbanguard_token';
const AUTH_USER_KEY = 'urbanguard_user';

/**
 * Store auth data in sessionStorage
 */
const storeAuth = (token, user) => {
  sessionStorage.setItem(AUTH_TOKEN_KEY, token);
  sessionStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
};

/**
 * Clear auth data
 */
const clearAuth = () => {
  sessionStorage.removeItem(AUTH_TOKEN_KEY);
  sessionStorage.removeItem(AUTH_USER_KEY);
};

/**
 * Get current auth token
 */
export const getToken = () => {
  return sessionStorage.getItem(AUTH_TOKEN_KEY);
};

/**
 * Get current user info
 */
export const getCurrentUser = () => {
  const userStr = sessionStorage.getItem(AUTH_USER_KEY);
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
};

/**
 * Check if user is authenticated
 */
export const isAuthenticated = () => {
  return !!getToken();
};

/**
 * Check if user has admin role
 */
export const isAdmin = () => {
  const user = getCurrentUser();
  return user && user.role === 'admin';
};

/**
 * Login with email and password
 * Uses backend /auth/login endpoint
 */
export const login = async (email, password) => {
  const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/v1/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Login failed' }));
    throw new Error(error.detail || 'Login failed');
  }

  const data = await response.json();
  storeAuth(data.token, data.user);
  return data.user;
};

/**
 * Signup with email, password, and role
 */
export const signup = async (email, password, role = 'citizen') => {
  const baseUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
  const response = await fetch(`${baseUrl}/api/v1/auth/signup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, role }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Signup failed' }));
    throw new Error(error.detail || 'Signup failed');
  }

  const data = await response.json();
  storeAuth(data.token, data.user);
  return data.user;
};

/**
 * Logout - clear stored auth
 */
export const logout = () => {
  clearAuth();
};
