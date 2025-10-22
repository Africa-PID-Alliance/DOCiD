import { createSlice } from '@reduxjs/toolkit';

// Safe initial state for SSR
const initialState = {
  user: {
    accessToken: "",
    refreshToken: "",
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
  error: null,
  language: 'en'
};

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    rehydrateAuth: (state) => {
      // Rehydrate auth state from localStorage after app loads
      if (typeof window !== 'undefined') {
        const storedAuth = localStorage.getItem('auth');
        if (storedAuth) {
          try {
            const parsedAuth = JSON.parse(storedAuth);
            return { ...state, ...parsedAuth };
          } catch (error) {
            console.warn('Failed to parse stored auth state:', error);
            localStorage.removeItem('auth');
          }
        }
      }
      return state;
    },
    loginStart: (state) => {
      state.loading = true;
      state.error = null;
    },
    loginSuccess: (state, action) => {
      state.loading = false;
      state.isAuthenticated = true;
      state.user = {
        accessToken: action.payload.accessToken || "",
        refreshToken: action.payload.refreshToken || "",
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
        refreshToken: "",
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
    },
    updateAccessToken: (state, action) => {
      state.user.accessToken = action.payload.accessToken;

      // Persist to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth', JSON.stringify(state));
      }
    },
    setLanguage: (state, action) => {
      state.language = action.payload;
      
      // Persist to localStorage
      if (typeof window !== 'undefined') {
        localStorage.setItem('auth', JSON.stringify(state));
      }
    }
  }
});

export const { rehydrateAuth, loginStart, loginSuccess, loginFailure, logout, updateAccessToken, setLanguage } = authSlice.actions;
export default authSlice.reducer; 