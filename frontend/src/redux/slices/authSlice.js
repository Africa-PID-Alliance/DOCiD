import { createSlice } from '@reduxjs/toolkit';

// Safe initial state for SSR
const initialState = {
  user: {
    accessToken: "",
    refreshToken: "",
    id: null,
    name: "",
    picture: "",
    logo_url: "",
    username: "",
    type: "",
    affiliation: "",
    email: "",
    account_type_name: ""
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
        logo_url: action.payload.logo_url || "",
        username: action.payload.user_name,
        type: action.payload.type,
        affiliation: action.payload.affiliation,
        email: action.payload.email,
        account_type_name: action.payload.account_type_name || ""
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
        logo_url: "",
        username: "",
        type: "",
        affiliation: "",
        email: "",
        account_type_name: ""
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
    updateUserProfile: (state, action) => {
      const payload = action.payload || {};
      if (payload.full_name !== undefined) state.user.name = payload.full_name;
      if (payload.email !== undefined) state.user.email = payload.email;
      if (payload.avator !== undefined) state.user.picture = payload.avator;
      if (payload.logo_url !== undefined) state.user.logo_url = payload.logo_url;
      if (payload.user_name !== undefined) state.user.username = payload.user_name;
      if (payload.affiliation !== undefined) state.user.affiliation = payload.affiliation;
      if (payload.account_type_name !== undefined) {
        state.user.account_type_name = payload.account_type_name;
      }

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

export const {
  rehydrateAuth,
  loginStart,
  loginSuccess,
  loginFailure,
  logout,
  updateAccessToken,
  updateUserProfile,
  setLanguage
} = authSlice.actions;
export default authSlice.reducer; 