'use client';

import React, { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import { Alert, Snackbar } from '@mui/material';

const ToastContext = createContext(null);

const DEFAULT_TOAST_DURATION_MS = 6000;

let toastSequence = 0;

/**
 * App-wide toast notifications (MUI Snackbar + Alert).
 *
 * Toasts are queued and shown one at a time, so a background message such as
 * "Draft saved" never replaces an error the user has not read yet. A toast that
 * repeats the one showing (or last queued) is dropped.
 */
export const ToastProvider = ({ children }) => {
  const [toastQueue, setToastQueue] = useState([]);
  const [activeToast, setActiveToast] = useState(null);
  const [isToastOpen, setIsToastOpen] = useState(false);
  const activeToastRef = useRef(null);

  const showToast = useCallback((message, severity = 'success', options = {}) => {
    if (!message) return;
    const nextToast = {
      key: ++toastSequence,
      message,
      severity,
      autoHideDuration: options.autoHideDuration ?? DEFAULT_TOAST_DURATION_MS,
    };
    setToastQueue((queue) => {
      const latestToast = queue[queue.length - 1] || activeToastRef.current;
      if (latestToast && latestToast.message === message && latestToast.severity === severity) {
        return queue;
      }
      return [...queue, nextToast];
    });
  }, []);

  // Show the next queued toast once the current one has fully closed
  useEffect(() => {
    if (!activeToast && toastQueue.length > 0) {
      const [nextToast, ...remainingToasts] = toastQueue;
      activeToastRef.current = nextToast;
      setActiveToast(nextToast);
      setToastQueue(remainingToasts);
      setIsToastOpen(true);
    }
  }, [activeToast, toastQueue]);

  const handleToastClose = () => setIsToastOpen(false);

  const handleToastExited = () => {
    activeToastRef.current = null;
    setActiveToast(null);
  };

  const contextValue = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={contextValue}>
      {children}
      <Snackbar
        key={activeToast?.key}
        open={isToastOpen}
        autoHideDuration={activeToast?.autoHideDuration}
        onClose={handleToastClose}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
        // Sit just below the fixed 80px navbar instead of covering it
        sx={{ top: { xs: 88, sm: 96 } }}
        slotProps={{ transition: { onExited: handleToastExited } }}
      >
        <Alert
          onClose={handleToastClose}
          severity={activeToast?.severity || 'success'}
          sx={{ width: '100%', boxShadow: 3 }}
        >
          {activeToast?.message}
        </Alert>
      </Snackbar>
    </ToastContext.Provider>
  );
};

/**
 * Returns { showToast(message, severity = 'success', { autoHideDuration }) }.
 * severity is one of 'success' | 'info' | 'warning' | 'error'.
 */
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};
