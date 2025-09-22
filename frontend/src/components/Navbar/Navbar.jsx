"use client";

import React, { useState } from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Box, 
  IconButton, 
  Menu, 
  MenuItem,
  Button,
  useTheme,
  Divider,
  ListItemIcon,
  ListItemText,
  Avatar,
  Tooltip,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  useMediaQuery,
  Collapse
} from '@mui/material';
import {
  Person as PersonIcon,
  Language as LanguageIcon,
  Home as HomeIcon,
  Description as DescriptionIcon,
  Info as InfoIcon,
  Login as LoginIcon,
  PersonAdd as PersonAddIcon,
  Check as CheckIcon,
  AccountCircle as AccountCircleIcon,
  Logout as LogoutIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  Menu as MenuIcon,
  Close as CloseIcon,
  ExpandLess,
  ExpandMore
} from '@mui/icons-material';
import Image from 'next/image';
import { useRouter, usePathname } from 'next/navigation';
import { useTranslation } from 'react-i18next';
import { useSelector, useDispatch } from 'react-redux';
import { logout } from '@/redux/slices/authSlice';
import { useThemeContext } from '@/context/ThemeContext';
import Link from 'next/link';

const Navbar = () => {
  const [anchorEl, setAnchorEl] = useState(null);
  const [languageMenu, setLanguageMenu] = useState(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileLanguageOpen, setMobileLanguageOpen] = useState(false);
  const [mobileUserMenuOpen, setMobileUserMenuOpen] = useState(false);
  const router = useRouter();
  const pathname = usePathname();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const { t, i18n } = useTranslation('common');
  const dispatch = useDispatch();
  const { isAuthenticated, user } = useSelector((state) => state.auth);
  const { mode, toggleTheme } = useThemeContext();

  const handleUserMenuOpen = (event) => setAnchorEl(event.currentTarget);
  const handleUserMenuClose = () => setAnchorEl(null);
  const handleLanguageMenuOpen = (event) => setLanguageMenu(event.currentTarget);
  const handleLanguageMenuClose = () => setLanguageMenu(null);
  const handleMobileMenuToggle = () => setMobileMenuOpen(!mobileMenuOpen);
  const handleMobileMenuClose = () => {
    setMobileMenuOpen(false);
    setMobileLanguageOpen(false);
    setMobileUserMenuOpen(false);
  };

  const languages = [
    { code: 'en', name: 'English', flag: '🇬🇧' },
    { code: 'fr', name: 'French', flag: '🇫🇷' },
    { code: 'sw', name: 'Kiswahili', flag: '🇰🇪' },
    { code: 'ar', name: 'Arabic', flag: '🇸🇦' },
    { code: 'pt', name: 'Portuguese', flag: '🇵🇹' },
    { code: 'de', name: 'German', flag: '🇩🇪' }
  ];

  const handleLanguageChange = (langCode) => {
    i18n.changeLanguage(langCode).then(() => {
      localStorage.setItem('i18nextLng', langCode);
      document.documentElement.lang = langCode;
      handleLanguageMenuClose();
      if (isMobile) {
        setMobileLanguageOpen(false);
      }
    });
  };

  const isActiveRoute = (route) => pathname === route;

  const handleLogout = () => {
    dispatch(logout());
    handleUserMenuClose();
    handleMobileMenuClose();
    router.push('/login');
  };

  const handleNavigation = (path) => {
    router.push(path);
    handleMobileMenuClose();
  };

  const menuItems = [
    { icon: <HomeIcon />, label: t('nav.home'), path: '/' },
    { icon: <DescriptionIcon />, label: t('nav.docids'), path: '/list-docids' },
    { icon: <InfoIcon />, label: t('nav.about_docid'), path: '/about-us' }
  ];

  // Mobile Menu Content
  const MobileMenuContent = () => (
    <Box sx={{ width: 280, pt: 2 }}>
      {/* Mobile Header */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center', 
        justifyContent: 'space-between',
        px: 2,
        pb: 2,
        borderBottom: `1px solid ${theme.palette.divider}`
      }}>
        <Box sx={{ 
          height: '40px', 
          width: '120px', 
          position: 'relative',
          cursor: 'pointer'
        }}
        onClick={() => {
          router.push('/');
          handleMobileMenuClose();
        }}
        >
          <Image 
            src="/assets/images/Logo2.png"
            alt="Logo"
            width={120}
            height={40}
            style={{ 
              objectFit: 'contain',
              width: '100%',
              height: '100%'
            }}
            priority
          />
        </Box>
        <IconButton onClick={handleMobileMenuClose} size="small">
          <CloseIcon />
        </IconButton>
      </Box>

      {/* Navigation Items */}
      <List sx={{ px: 1 }}>
        {menuItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              onClick={() => handleNavigation(item.path)}
              sx={{
                borderRadius: 1,
                mx: 1,
                mb: 0.5,
                backgroundColor: isActiveRoute(item.path) 
                  ? theme.palette.primary.main + '15' 
                  : 'transparent',
                '&:hover': {
                  backgroundColor: theme.palette.primary.main + '20'
                }
              }}
            >
              <ListItemIcon sx={{ 
                color: isActiveRoute(item.path) 
                  ? theme.palette.primary.main 
                  : theme.palette.text.secondary,
                minWidth: 40
              }}>
                {item.icon}
              </ListItemIcon>
              <ListItemText 
                primary={item.label}
                primaryTypographyProps={{
                  fontWeight: isActiveRoute(item.path) ? 600 : 400,
                  color: isActiveRoute(item.path) 
                    ? theme.palette.primary.main 
                    : theme.palette.text.primary
                }}
              />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <Divider sx={{ my: 2 }} />

      {/* Theme Toggle */}
      <ListItem disablePadding>
        <ListItemButton onClick={toggleTheme} sx={{ borderRadius: 1, mx: 2 }}>
          <ListItemIcon sx={{ minWidth: 40 }}>
            {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
          </ListItemIcon>
          <ListItemText 
            primary={mode === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}
          />
        </ListItemButton>
      </ListItem>

      {/* Language Menu */}
      <ListItem disablePadding>
        <ListItemButton 
          onClick={() => setMobileLanguageOpen(!mobileLanguageOpen)} 
          sx={{ borderRadius: 1, mx: 2 }}
        >
          <ListItemIcon sx={{ minWidth: 40 }}>
            <LanguageIcon />
          </ListItemIcon>
          <ListItemText 
            primary={t('user_menu.language')}
            secondary={languages.find(lang => lang.code === i18n.language)?.name || 'English'}
          />
          {mobileLanguageOpen ? <ExpandLess /> : <ExpandMore />}
        </ListItemButton>
      </ListItem>

      <Collapse in={mobileLanguageOpen} timeout="auto" unmountOnExit>
        <List component="div" disablePadding sx={{ pl: 2 }}>
          {languages.map((lang) => (
            <ListItem key={lang.code} disablePadding>
              <ListItemButton 
                onClick={() => handleLanguageChange(lang.code)}
                sx={{ borderRadius: 1, mx: 1, py: 1 }}
              >
                <Typography sx={{ fontSize: '1.2rem', mr: 2 }}>
                  {lang.flag}
                </Typography>
                <ListItemText primary={lang.name} />
                {i18n.language === lang.code && (
                  <CheckIcon sx={{ color: theme.palette.primary.main, ml: 1 }} />
                )}
              </ListItemButton>
            </ListItem>
          ))}
        </List>
      </Collapse>

      <Divider sx={{ my: 2 }} />

      {/* User Menu */}
      {isAuthenticated && user ? (
        <>
          {/* User Info */}
          <Box sx={{ px: 2, py: 1 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
              <Avatar 
                src={user?.picture || ''} 
                alt={user?.name || 'User'}
                sx={{ width: 32, height: 32 }}
              >
                {!user?.picture && <PersonIcon />}
              </Avatar>
              <Box>
                <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                  {user?.name || 'User'}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {user?.email || ''}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Account Actions */}
          <ListItem disablePadding>
            <ListItemButton 
              onClick={() => {
                handleMobileMenuClose();
                router.push('/my-account');
              }}
              sx={{ borderRadius: 1, mx: 2 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <AccountCircleIcon color="primary" />
              </ListItemIcon>
              <ListItemText primary={t('user_menu.my_account')} />
            </ListItemButton>
          </ListItem>

          <ListItem disablePadding>
            <ListItemButton 
              onClick={handleLogout}
              sx={{ 
                borderRadius: 1, 
                mx: 2,
                color: '#f44336',
                '&:hover': {
                  backgroundColor: 'rgba(244, 67, 54, 0.08)'
                }
              }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <LogoutIcon sx={{ color: '#f44336' }} />
              </ListItemIcon>
              <ListItemText primary={t('user_menu.logout')} />
            </ListItemButton>
          </ListItem>
        </>
      ) : (
        <>
          {/* Guest Actions */}
          <Box sx={{ px: 2, py: 1, mb: 2 }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              {t('user_menu.welcome')}
            </Typography>
            <Typography variant="caption" color="text.secondary">
              {t('user_menu.sign_in_message')}
            </Typography>
          </Box>

          <ListItem disablePadding>
            <ListItemButton 
              onClick={() => {
                handleMobileMenuClose();
                router.push('/login');
              }}
              sx={{ borderRadius: 1, mx: 2 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <LoginIcon color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary={t('user_menu.login')}
                secondary={t('user_menu.login_desc')}
              />
            </ListItemButton>
          </ListItem>

          <ListItem disablePadding>
            <ListItemButton 
              onClick={() => {
                handleMobileMenuClose();
                router.push('/register');
              }}
              sx={{ borderRadius: 1, mx: 2 }}
            >
              <ListItemIcon sx={{ minWidth: 40 }}>
                <PersonAddIcon color="primary" />
              </ListItemIcon>
              <ListItemText 
                primary={t('user_menu.register')}
                secondary={t('user_menu.register_desc')}
              />
            </ListItemButton>
          </ListItem>
        </>
      )}
    </Box>
  );

  return (
    <Box sx={{ position: 'fixed', width: '100%', top: 0, zIndex: 1100 }}>
      <AppBar 
        position="static"
        elevation={0}
        sx={{ 
          height: '80px',
          borderBottom: `1px solid ${theme.palette.primary.main}22`,
          backgroundColor: '#1565c0',
        }}
      >
        <Toolbar sx={{ height: '100%', px: { xs: 2, sm: 3 } }}>
          {/* Mobile Menu Button */}
          {isMobile && (
            <IconButton
              edge="start"
              color="inherit"
              aria-label="menu"
              onClick={handleMobileMenuToggle}
              sx={{ 
                mr: 2,
                color: theme.palette.text.light,
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.1)'
                }
              }}
            >
              <MenuIcon />
            </IconButton>
          )}

          {/* Logo Container */}
          <Box 
            component="div" 
            onClick={() => router.push('/')}
            sx={{ 
              height: '50px', 
              width: { xs: '120px', sm: '150px' }, 
              position: 'relative', 
              marginRight: { xs: 'auto', md: '100px' },
              transition: 'transform 0.2s ease',
              cursor: 'pointer',
              '&:hover': {
                transform: 'scale(1.02)'
              }
            }}
          >
            <Image 
              src="/assets/images/Logo2.png"
              alt="Logo"
              width={150}
              height={50}
              style={{ 
                objectFit: 'contain',
                width: '100%',
                height: '100%'
              }}
              priority
            />
          </Box>

          {/* Desktop Menu Items */}
          {!isMobile && (
            <Box sx={{ flexGrow: 1, ml: 4, display: 'flex', gap: 3 }}>
              {menuItems.map((item) => (
                <Button 
                  key={item.path}
                  startIcon={item.icon}
                  onClick={() => router.push(item.path)}
                  sx={{ 
                    color: theme.palette.text.light,
                    fontSize: '0.95rem',
                    fontWeight: isActiveRoute(item.path) ? 600 : 400,
                    position: 'relative',
                    padding: '6px 16px',
                    transition: 'all 0.2s ease',
                    '&:before': {
                      content: '""',
                      position: 'absolute',
                      bottom: 0,
                      left: '50%',
                      transform: 'translateX(-50%)',
                      width: isActiveRoute(item.path) ? '80%' : '0%',
                      height: '3px',
                      backgroundColor: theme.palette.text.light,
                      transition: 'all 0.3s ease'
                    },
                    '&:hover': {
                      backgroundColor: 'rgba(255, 255, 255, 0.1)',
                      transform: 'translateY(-2px)',
                      '&:before': {
                        width: '80%'
                      }
                    }
                  }}
                >
                  {item.label}
                </Button>
              ))}
            </Box>
          )}

          {/* Desktop Theme Toggle */}
          {!isMobile && (
            <Tooltip title={mode === 'dark' ? 'Switch to Light Mode' : 'Switch to Dark Mode'}>
              <IconButton
                onClick={toggleTheme}
                sx={{
                  color: theme.palette.text.light,
                  transition: 'transform 0.2s ease',
                  width: 40,
                  height: 40,
                  mr: 1,
                  '&:hover': {
                    transform: 'scale(1.1)',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)'
                  }
                }}
              >
                {mode === 'dark' ? <LightModeIcon /> : <DarkModeIcon />}
              </IconButton>
            </Tooltip>
          )}

          {/* Desktop User Menu */}
          {!isMobile && (
            <>
              <IconButton 
                onClick={handleUserMenuOpen} 
                sx={{ 
                  color: theme.palette.text.light,
                  transition: 'transform 0.2s ease',
                  width: 40,
                  height: 40,
                  '&:hover': {
                    transform: 'scale(1.1)',
                    backgroundColor: 'rgba(255, 255, 255, 0.1)'
                  }
                }}
              >
                <PersonIcon />
              </IconButton>

              <Menu
                anchorEl={anchorEl}
                open={Boolean(anchorEl)}
                onClose={handleUserMenuClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'bottom' }}
                PaperProps={{
                  elevation: 5,
                  sx: {
                    mt: 1.5,
                    overflow: 'visible',
                    filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.15))',
                    borderRadius: 2,
                    minWidth: '250px',
                    '&:before': {
                      content: '""',
                      display: 'block',
                      position: 'absolute',
                      top: 0,
                      right: 14,
                      width: 10,
                      height: 10,
                      bgcolor: 'background.paper',
                      transform: 'translateY(-50%) rotate(45deg)',
                      zIndex: 0,
                    }
                  }
                }}
              >
                {isAuthenticated && user ? (
                  <Box>
                    <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                        <Avatar 
                          src={user?.picture || ''} 
                          alt={user?.name || 'User'}
                          sx={{ width: 40, height: 40 }}
                        >
                          {!user?.picture && <PersonIcon />}
                        </Avatar>
                        <Box>
                          <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                            {user?.name || 'User'}
                          </Typography>
                          <Typography variant="body2" color="text.secondary">
                            {user?.email || ''}
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                    <Link 
                      href="/my-account" 
                      style={{ textDecoration: 'none', color: 'inherit' }}
                      onClick={handleUserMenuClose}
                    >
                      <MenuItem 
                        sx={{ 
                          py: 1.5,
                          '&:hover': {
                            backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.light
                          }
                        }}
                      >
                        <ListItemIcon>
                          <AccountCircleIcon fontSize="small" color="primary" />
                        </ListItemIcon>
                        <ListItemText 
                          primary={t('user_menu.my_account')}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </MenuItem>
                    </Link>
                    <MenuItem 
                      onClick={handleLanguageMenuOpen}
                      sx={{ 
                        py: 1.5,
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.light
                        }
                      }}
                    >
                      <ListItemIcon>
                        <LanguageIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={t('user_menu.language')}
                        secondary={languages.find(lang => lang.code === i18n.language)?.name || 'English'}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </MenuItem>
                    <Divider />
                    <MenuItem 
                      onClick={handleLogout}
                      sx={{ 
                        py: 1.5,
                        color: '#f44336',
                        '&:hover': {
                          backgroundColor: 'rgba(244, 67, 54, 0.08)',
                        }
                      }}
                    >
                      <ListItemIcon>
                        <LogoutIcon sx={{ color: '#f44336' }} />
                      </ListItemIcon>
                      <ListItemText 
                        primary={t('user_menu.logout')}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </MenuItem>
                  </Box>
                ) : (
                  <Box>
                    <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                      <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                        {t('user_menu.welcome')}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {t('user_menu.sign_in_message')}
                      </Typography>
                    </Box>
                    <MenuItem 
                      onClick={() => {
                        handleUserMenuClose();
                        router.push('/login');
                      }}
                      sx={{ 
                        py: 1.5,
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.light
                        }
                      }}
                    >
                      <ListItemIcon>
                        <LoginIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={t('user_menu.login')}
                        secondary={t('user_menu.login_desc')}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </MenuItem>
                    <MenuItem 
                      onClick={() => {
                        handleUserMenuClose();
                        router.push('/register');
                      }}
                      sx={{ 
                        py: 1.5,
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.light
                        }
                      }}
                    >
                      <ListItemIcon>
                        <PersonAddIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={t('user_menu.register')}
                        secondary={t('user_menu.register_desc')}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </MenuItem>
                    <Divider />
                    <MenuItem 
                      onClick={handleLanguageMenuOpen}
                      sx={{ 
                        py: 1.5,
                        '&:hover': {
                          backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.light
                        }
                      }}
                    >
                      <ListItemIcon>
                        <LanguageIcon fontSize="small" color="primary" />
                      </ListItemIcon>
                      <ListItemText 
                        primary={t('user_menu.language')}
                        secondary={languages.find(lang => lang.code === i18n.language)?.name || 'English'}
                        primaryTypographyProps={{ fontWeight: 500 }}
                      />
                    </MenuItem>
                  </Box>
                )}
              </Menu>

              {/* Language Submenu */}
              <Menu
                anchorEl={languageMenu}
                open={Boolean(languageMenu)}
                onClose={handleLanguageMenuClose}
                transformOrigin={{ horizontal: 'right', vertical: 'top' }}
                anchorOrigin={{ horizontal: 'right', vertical: 'top' }}
                PaperProps={{
                  elevation: 5,
                  sx: {
                    mt: 1,
                    overflow: 'visible',
                    filter: 'drop-shadow(0px 2px 8px rgba(0,0,0,0.15))',
                    borderRadius: 2,
                    minWidth: '220px',
                    '&:before': {
                      content: '""',
                      display: 'block',
                      position: 'absolute',
                      top: 0,
                      right: 14,
                      width: 10,
                      height: 10,
                      bgcolor: 'background.paper',
                      transform: 'translateY(-50%) rotate(45deg)',
                      zIndex: 0,
                    },
                    animation: 'fadeIn 0.2s ease'
                  }
                }}
              >
                <Box sx={{ p: 2, borderBottom: `1px solid ${theme.palette.divider}` }}>
                  <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
                    {t('user_menu.select_language')}
                  </Typography>
                </Box>
                {languages.map((lang) => (
                  <MenuItem 
                    key={lang.code} 
                    onClick={() => handleLanguageChange(lang.code)}
                    sx={{ 
                      py: 1.5,
                      '&:hover': {
                        backgroundColor: theme.palette.mode === 'dark' ? '#141a3b' : theme.palette.primary.light
                      }
                    }}
                  >
                    <Box sx={{ 
                      display: 'flex', 
                      alignItems: 'center',
                      width: '100%',
                      position: 'relative'
                    }}>
                      <Typography sx={{ fontSize: '1.2rem', mr: 2 }}>
                        {lang.flag}
                      </Typography>
                      <Typography>{lang.name}</Typography>
                      {i18n.language === lang.code && (
                        <CheckIcon 
                          sx={{ 
                            position: 'absolute',
                            right: 0,
                            color: theme.palette.primary.main
                          }} 
                        />
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Menu>
            </>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Drawer */}
      <Drawer
        anchor="right"
        open={mobileMenuOpen}
        onClose={handleMobileMenuClose}
        PaperProps={{
          sx: {
            backgroundColor: theme.palette.background.paper,
            backgroundImage: 'none'
          }
        }}
      >
        <MobileMenuContent />
      </Drawer>
    </Box>
  );
};

export default Navbar;