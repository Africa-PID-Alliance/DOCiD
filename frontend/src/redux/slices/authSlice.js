import { createSlice } from '@reduxjs/toolkit';

// Load initial state from localStorage if available
const loadInitialState = () => {
  if (typeof window !== 'undefined') {
    const storedAuth = localStorage.getItem('auth');
    if (storedAuth) {
      return JSON.parse(storedAuth);
    }
  }
  return {
    user: {
      accessToken: "",
      id: null,
      name: "",
      picture: "",
      username: "",
      type: "",
      affiliation: "",
      email: ""
    },
    isAuthenticated: false,
    loading: false,
    error: null
  };
};

const initialState = loadInitialState();

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      state.loading = false;
      state.isAuthenticated = true;
      state.user = {
        accessToken: action.payload.accessToken || "",
        id: action.payload.user_id,
        name: action.payload.full_name,
        picture: action.payload.avator,
        username: action.payload.user_name,
        type: action.payload.type,
        affiliation: action.payload.affiliation,
        email: action.payload.email
      };
      state.error = null;
      
      // Persist to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth', JSON.stringify(state));
      }
    },
    loginFailure: (state, action) => {
      state.loading = false;
      state.error = action.payload;
    },
    logout: (state) => {
      state.user = {
        accessToken: "",
        id: null,
        name: "",
        picture: "",
        username: "",
        type: "",
        affiliation: "",
        email: ""
      };
      state.isAuthenticated = false;
      state.loading = false;
      state.error = null;
      
      // Clear localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('auth');
      }
    }
  }
});

export const { loginStart, loginSuccess, loginFailure, logout } = authSlice.actions;
export default authSlice.reducer; 