'use client';

import React from 'react';
import { Provider } from 'react-redux';
import { PersistGate } from 'redux-persist/integration/react';
import { store, persistor } from '@/redux/store';
import Navbar from '@/components/Navbar/Navbar';
import I18nProvider from '@/i18n/I18nProvider';
import { CssBaseline } from '@mui/material';
import { ThemeProvider } from '@/context/ThemeContext';
import PreFooter from '@/components/PreFooter/PreFooter';
import Footer from '@/components/Footer/Footer';
import { Box } from '@mui/material';

export default function ClientWrapper({ children }) {
    return (
        <Provider store={store}>
            <PersistGate loading={null} persistor={persistor}>
                <ThemeProvider>
                    <CssBaseline />
                    <I18nProvider>
                        <Box 
                            sx={{ 
                                display: 'flex', 
                                flexDirection: 'column', 
                                minHeight: '100vh',
                                width: '100%'
                            }}
                        >
                            <Navbar />
                            <Box
                                component="main"
                                sx={{
                                    flexGrow: 1,
                                    minHeight: 'calc(100vh - 80px)', // Subtract navbar height
                                    marginTop: '80px', // Add margin for navbar
                                    width: '100%',
                                    display: 'flex',
                                    flexDirection: 'column',
                                    '& > *': {  // This targets immediate children
                                        width: '100% !important',
                                        maxWidth: 'none !important',
                                        paddingLeft: '0 !important',
                                        paddingRight: '0 !important'
                                    }
                                }}
                            >
                                {children}
                            </Box>
                            <PreFooter />
                            <Footer />
                        </Box>
                    </I18nProvider>
                </ThemeProvider>
            </PersistGate>
        </Provider>
    );
} 