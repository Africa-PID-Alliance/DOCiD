"use client";

import React, { useState, useEffect } from 'react';
import {
  Box,
  Container,
  Paper,
  Typography,
  Grid,
  Divider,
  Avatar,
  TextField,
  Button,
  List,
  ListItem,
  ListItemText,
  ListItemAvatar,
  Card,
  CardContent,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Link,
  IconButton,
} from '@mui/material';
import {
  Comment as CommentIcon,
  Send as SendIcon,
  Link as LinkIcon,
  CalendarToday,
  Person,
  Description,
  Image,
  ThumbUpOutlined,
  VisibilityOutlined,
  Close,
  InfoOutlined,
  MoreVert as MoreVertIcon,
} from '@mui/icons-material';
import EmailIcon from '@mui/icons-material/Email';
import FacebookIcon from '@mui/icons-material/Facebook';
import TwitterIcon from '@mui/icons-material/Twitter';
import WhatsAppIcon from '@mui/icons-material/WhatsApp';
import LinkedInIcon from '@mui/icons-material/LinkedIn';
import Popover from '@mui/material/Popover';
import axios from 'axios';
import { Close as CloseIcon } from '@mui/icons-material';
import { useTheme } from '@mui/material/styles';
import { formatDocIdForDisplay, formatDocIdForUrl } from '@/utils/docidUtils';
import { useSelector } from 'react-redux';

const DocIDPage = ({ params }) => {
  const [comment, setComment] = useState('');
  const [docData, setDocData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [anchorEl, setAnchorEl] = useState(null);
  const [selectedSection, setSelectedSection] = useState(null);
  const [modalOpen, setModalOpen] = useState(false);
  const [creatorRoles, setCreatorRoles] = useState([]);
  const [featureModal, setFeatureModal] = useState(false);
  const [comments, setComments] = useState([]);
  const [commentLoading, setCommentLoading] = useState(false);
  const [commentsLoading, setCommentsLoading] = useState(false);
  const [showAllComments, setShowAllComments] = useState(false);
  const [replyingTo, setReplyingTo] = useState(null);
  const [replyText, setReplyText] = useState('');
  const [expandedReplies, setExpandedReplies] = useState(new Set());
  const [commentsModalOpen, setCommentsModalOpen] = useState(false);
  const [publicationId, setPublicationId] = useState(null);
  const [commentError, setCommentError] = useState('');
  const [commentSuccess, setCommentSuccess] = useState('');
  
  // Redux state
  const { user, isAuthenticated } = useSelector((state) => state.auth);
  
  // Use React.use() to unwrap params
  const unwrappedParams = React.use(params);
  const docId = unwrappedParams.id;
  
  const theme = useTheme();

  // Fetch comments for this DOCiD
  const fetchComments = async () => {
    if (!publicationId) return;

    try {
      setCommentsLoading(true);
      const response = await axios.get(`/api/publications/${publicationId}/comments`);

      // Handle the improved API response structure
      if (response.data.comments) {
        setComments(response.data.comments);
      } else if (Array.isArray(response.data)) {
        setComments(response.data);
      } else {
        setComments([]);
      }

      // Log any service messages for debugging
      if (response.data.message) {
        console.log('Comments service message:', response.data.message);
      }
    } catch (error) {
      console.error('Error fetching comments:', error);

      // Check if it's a service unavailable error vs other errors
      if (error.response?.status === 503) {
        console.log('Comments service is temporarily unavailable');
      } else {
        console.log('Comments could not be loaded');
      }

      setComments([]);
    } finally {
      setCommentsLoading(false);
    }
  };

  useEffect(() => {
    const fetchDocData = async () => {
      try {
        setLoading(true);
        // Normalize the docId for API requests
        const normalizedId = formatDocIdForUrl(docId);
        console.log('Normalized docId:', normalizedId);
        
        // First find the publication ID from the list
        const listResponse = await axios.get('/api/publications/get-publications');
        // Need to handle both encoded and non-encoded versions when comparing with API data
        const decodedForComparison = formatDocIdForDisplay(normalizedId);
        const publication = listResponse.data.data.find(pub => 
          pub.docid === decodedForComparison || pub.docid === normalizedId
        );
        
        if (!publication) {
          throw new Error('DOCiD not found');
        }

        console.log('Publication ID:', publication.id);
        setPublicationId(publication.id);

        // Then fetch the full publication details
        try {
          const response = await axios.get(`/api/publications/get-publication/${publication.id}`);
          console.log('DocData received:', response.data);
          console.log('Published field:', response.data.published);
          console.log('Published_isoformat field:', response.data.published_isoformat);
          setDocData(response.data);
        } catch (apiError) {
          // Handle API errors gracefully
          if (apiError.response?.status === 502) {
            console.warn('External API issue, using basic publication data');
            // Use the basic data from the list if the detailed API fails
            setDocData({
              ...publication,
              document_title: publication.title,
              document_docid: publication.docid,
              document_description: publication.description,
              publication_poster_url: publication.publication_poster_url,
              publication_creators: [],
              publication_organizations: [],
              publication_funders: [],
              publication_projects: [],
              publications_files: [],
              publication_documents: []
            });
          } else {
            throw apiError;
          }
        }
      } catch (err) {
        console.error('Error in fetchDocData:', err);
        setError(err.response?.data?.message || err.message || 'Failed to load DOCiD data');
      } finally {
        setLoading(false);
      }
    };

    fetchDocData();
  }, [docId]);

  // Fetch comments when publication ID is available
  useEffect(() => {
    if (publicationId) {
      fetchComments();
    }
  }, [publicationId]);

  // Fetch creator roles
  useEffect(() => {
    const fetchCreatorRoles = async () => {
      try {
        const response = await axios.get('/api/publications/get-list-creators-roles');
        console.log('Fetched creator roles:', response.data);
        setCreatorRoles(response.data);
      } catch (error) {
        console.error('Error fetching creator roles:', error);
      }
    };
    fetchCreatorRoles();
  }, []);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Typography color="error">{error}</Typography>
      </Box>
    );
  }

  if (!docData) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh' }}>
        <Typography>DOCiD not found</Typography>
      </Box>
    );
  }

  // Section counts using actual data
  const sectionData = [
    { 
      label: 'Publication(s)', 
      count: docData.publications_files?.length || 0,
      data: docData.publications_files || []
    },
    { 
      label: 'Document(s)', 
      count: docData.publication_documents?.length || 0,
      data: docData.publication_documents || []
    },
    { 
      label: 'Creator(s)', 
      count: docData.publication_creators?.length || 0,
      data: docData.publication_creators || []
    },
    { 
      label: 'Organizations', 
      count: docData.publication_organizations?.length || 0,
      data: docData.publication_organizations || []
    },
    { 
      label: 'Funders', 
      count: docData.publication_funders?.length || 0,
      data: docData.publication_funders || []
    },
    { 
      label: 'Project(s)', 
      count: docData.publication_projects?.length || 0,
      data: docData.publication_projects || []
    }
  ];

  const identifiers = [
    {
      label: 'APA Handle iD',
      value: 1
    },
    {
      label: 'Datacite',
      value: 2
    },
    {
      label: 'CrossRef',
      value: 3
    },
    {
      label: 'DOI',
      value: 4,
      disabled: true
    }
  ];

  const getIdentifierLabel = (identifierId) => {
    const identifier = identifiers.find(id => id.value === parseInt(identifierId));
    return identifier ? identifier.label : 'Unknown';
  };

  const getRoleName = (roleId) => {
    console.log('Role ID:', roleId);
    console.log('Creator roles:', creatorRoles);
    if (!roleId || !creatorRoles || !Array.isArray(creatorRoles) || creatorRoles.length === 0) return 'Loading...';
    
    const role = creatorRoles.find(role => {
      if (!role || !role.role_id) return false;
      return role.role_id.toString() === roleId.toString();
    });
    console.log('Role:', role);
    
    return role ? role.role_name : 'Unknown Role';
  };

  const handleCommentSubmit = async (e) => {
    e.preventDefault();
    
    if (!comment.trim() || !publicationId) {
      return;
    }

    // Clear previous messages
    setCommentError('');
    setCommentSuccess('');

    try {
      setCommentLoading(true);
      
      console.log('User ID:', user?.id);
      console.log('User object:', user);
      console.log('Publication ID:', publicationId);
      
      const commentObject = {
        comment_text: comment.trim(),
        comment_type: "general",
        parent_comment_id: null,
        user_id: user?.id || 0
      };
      
      console.log('Comment object being submitted:', commentObject);
      
      const response = await axios.post(
        `/api/publications/${publicationId}/comments`,
        commentObject
      );

      console.log('Comment submission response:', response);

      if (response.status === 201 || response.status === 200) {
        // Clear the comment input
        setComment('');
        // Refresh comments
        await fetchComments();
        // Show success message
        setCommentSuccess('Comment posted successfully!');
        // Clear success message after 3 seconds
        setTimeout(() => setCommentSuccess(''), 3000);
      }
    } catch (error) {
      console.error('Error submitting comment:', error);
      console.error('Error response:', error.response);
      
      // Show user-friendly error messages based on the error type
      let errorMessage = 'Unable to post comment. Please try again.';
      
      if (error.response?.status === 503) {
        errorMessage = 'Comments service is temporarily unavailable. Please try again later.';
      } else if (error.response?.status === 401) {
        errorMessage = 'You must be logged in to post comments.';
      } else if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to post comments.';
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid comment. Please check your input.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many requests. Please wait before posting again.';
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
        errorMessage = 'Network connection issue. Please check your internet connection.';
      } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again.';
      }
      
      // Show error message to user
      setCommentError(errorMessage);
      // Clear error message after 5 seconds
      setTimeout(() => setCommentError(''), 5000);
      
      console.log('User-friendly error:', errorMessage);
    } finally {
      setCommentLoading(false);
    }
  };

  const handleReplySubmit = async (parentId) => {
    if (!replyText.trim() || !publicationId) {
      return;
    }

    // Clear previous messages
    setCommentError('');
    setCommentSuccess('');

    try {
      setCommentLoading(true);
      
      console.log('Reply - User ID:', user?.id);
      console.log('Reply - Publication ID:', publicationId);
      console.log('Reply - Parent ID:', parentId);
      
      const replyObject = {
        comment_text: replyText.trim(),
        comment_type: "general",
        parent_comment_id: parseInt(parentId, 10),
        user_id: user?.id || 0
      };
      
      console.log('Reply object being submitted:', replyObject);
      
      const response = await axios.post(
        `/api/publications/${publicationId}/comments`,
        replyObject
      );

      console.log('Reply submission response:', response);

      if (response.status === 201 || response.status === 200) {
        // Clear the reply input
        setReplyText('');
        setReplyingTo(null);
        // Refresh comments
        await fetchComments();
        // Show success message
        setCommentSuccess('Reply posted successfully!');
        // Clear success message after 3 seconds
        setTimeout(() => setCommentSuccess(''), 3000);
      }
    } catch (error) {
      console.error('Error submitting reply:', error);
      console.error('Reply error response:', error.response);
      
      // Show user-friendly error messages based on the error type
      let errorMessage = 'Unable to post reply. Please try again.';
      
      if (error.response?.status === 503) {
        errorMessage = 'Comments service is temporarily unavailable. Please try again later.';
      } else if (error.response?.status === 401) {
        errorMessage = 'You must be logged in to post replies.';
      } else if (error.response?.status === 403) {
        errorMessage = 'You do not have permission to post replies.';
      } else if (error.response?.status === 400) {
        errorMessage = 'Invalid reply. Please check your input.';
      } else if (error.response?.status === 429) {
        errorMessage = 'Too many requests. Please wait before posting again.';
      } else if (error.response?.data?.error) {
        errorMessage = error.response.data.error;
      } else if (error.code === 'NETWORK_ERROR' || error.message.includes('Network Error')) {
        errorMessage = 'Network connection issue. Please check your internet connection.';
      } else if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        errorMessage = 'Request timed out. Please try again.';
      }
      
      // Show error message to user
      setCommentError(errorMessage);
      // Clear error message after 5 seconds
      setTimeout(() => setCommentError(''), 5000);
      
      console.log('User-friendly reply error:', errorMessage);
    } finally {
      setCommentLoading(false);
    }
  };

  const handleReplyClick = (commentId) => {
    setReplyingTo(commentId);
    setReplyText('');
  };

  const handleCancelReply = () => {
    setReplyingTo(null);
    setReplyText('');
  };

  const toggleRepliesExpansion = (commentId) => {
    const newExpanded = new Set(expandedReplies);
    if (newExpanded.has(commentId)) {
      newExpanded.delete(commentId);
    } else {
      newExpanded.add(commentId);
    }
    setExpandedReplies(newExpanded);
  };

  const handleCommentsModalOpen = () => {
    setCommentsModalOpen(true);
  };

  const handleCommentsModalClose = () => {
    setCommentsModalOpen(false);
    setReplyingTo(null);
    setReplyText('');
  };

 

  // Format date for published date (more user-friendly)
  const formatDate = (dateString) => {
    if (!dateString) return 'Date not available';
    
    // Handle different date formats
    let date;
    
    // If it's a number (timestamp), convert it
    if (typeof dateString === 'number') {
      // Check if it's in seconds (Unix timestamp) or milliseconds
      if (dateString < 10000000000) {
        // It's in seconds, convert to milliseconds
        date = new Date(dateString * 1000);
      } else {
        // It's already in milliseconds
        date = new Date(dateString);
      }
    } else {
      // It's a string, parse it directly
      date = new Date(dateString);
    }
    
    // Check if the date is valid
    if (isNaN(date.getTime())) {
      console.error('Invalid date:', dateString);
      return 'Invalid date';
    }
    
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const day = days[date.getUTCDay()];
    const month = months[date.getUTCMonth()];
    const dateNum = date.getUTCDate();
    const year = date.getUTCFullYear();

    return `${day}, ${month} ${dateNum}, ${year}`;
  };

  // Format date for comments (with time)
  const formatCommentDate = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  // Calculate total comment count including replies
  const getTotalCommentCount = () => {
    let total = comments.length;
    comments.forEach(comment => {
      if (comment.replies) {
        total += comment.replies.length;
      }
    });
    return total;
  };

  const handleShareClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleShareClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  // Share handlers
  const handleEmailShare = () => {
    const subject = encodeURIComponent(`Check out this DOCiD: ${docData.document_title}`);
    const body = encodeURIComponent(
      `Check out this DOCiD:\n\n` +
      `Title: ${docData.document_title}\n` +
      `Description: ${docData.document_description.replace(/<[^>]+>/g, '')}\n\n` +
      `Link: ${window.location.href}`
    );
    window.open(`mailto:?subject=${subject}&body=${body}`);
    handleShareClose();
  };

  const handleFacebookShare = () => {
    const url = encodeURIComponent(window.location.href);
    window.open(`https://www.facebook.com/sharer/sharer.php?u=${url}`, '_blank');
    handleShareClose();
  };

  const handleTwitterShare = () => {
    const text = encodeURIComponent(`Check out this DOCiD: ${docData.document_title}`);
    const url = encodeURIComponent(window.location.href);
    window.open(`https://twitter.com/intent/tweet?text=${text}&url=${url}`, '_blank');
    handleShareClose();
  };

  const handleWhatsAppShare = () => {
    const text = encodeURIComponent(`Check out this DOCiD: ${docData.document_title}\n${window.location.href}`);
    window.open(`https://wa.me/?text=${text}`, '_blank');
    handleShareClose();
  };

  const handleLinkedInShare = () => {
    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(docData.document_title);
    window.open(`https://www.linkedin.com/sharing/share-offsite/?url=${url}&title=${title}`, '_blank');
    handleShareClose();
  };

  const handleViewSection = (section) => {
    setSelectedSection(section);
    setModalOpen(true);
  };

  const handleCloseModal = () => {
    setModalOpen(false);
    setSelectedSection(null);
  };

  const handleDownloadFile = (fileUrl) => {
    const link = document.createElement('a');
    link.href = `${process.env.NEXT_PUBLIC_UPLOAD_BASE_URL}/${fileUrl}`;
    link.download = fileUrl.split('/').pop(); // Get the filename
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  const handleLikeClick = () => {
    setFeatureModal(true);
  };

  const handleFeatureModalClose = () => {
    setFeatureModal(false);
  };

  return (
    <Box sx={{  minHeight: '100vh', backgroundColor: 'background.content' }}>
      <Container maxWidth="xl" sx={{ py: 4 }}>
        <Grid container spacing={3}>
          {/* Main Content */}
          <Grid item xs={12} md={8}>
            <Paper elevation={0} sx={{ p: 3, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.05)', bgcolor: 'background.paper' }}>
              {/* Header: User Info */}
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2, justifyContent: 'space-between' }}>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  <Avatar src={docData.avatar || '/default-avatar.png'} alt={docData.owner} sx={{ width: 48, height: 48, mr: 2 }} />
                  <Box>
                    <Typography fontWeight={600}>{docData.owner}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {formatDate(docData.published_isoformat || docData.published)}
                    </Typography>
                  </Box>
                </Box>
                <IconButton 
                  onClick={() => setFeatureModal(true)}
                  sx={{ ml: 2 }}
                >
                  <MoreVertIcon />
                </IconButton>
              </Box>
              {/* Title */}
              <Typography align="center" variant="h5" color="primary" fontWeight={600} mb={1}>
                {docData.document_title}
              </Typography>
              <Typography align="center" variant="subtitle1" color="text.secondary" mb={2}>
                DOCiD: {formatDocIdForDisplay(docData.document_docid || docData.docid)}
              </Typography>
              {/* Main Image */}
              <Box 
                display="flex" 
                justifyContent="center" 
                mb={2} 
                sx={{
                  width: '100%',
                  bgcolor: '#f5f5f5',
                  borderRadius: 2,
                  overflow: 'hidden'
                }}
              >
                <img
                  src={docData.publication_poster_url
                    ? (docData.publication_poster_url.startsWith('http')
                      ? docData.publication_poster_url
                      : `${process.env.NEXT_PUBLIC_NODE_URL}/${docData.publication_poster_url}`)
                    : '/assets/images/Logo2.png'}
                  alt="DOCiD"
                  style={{
                    width: '100%',
                    height: 'auto',
                    display: 'block',
                    maxWidth: '100%'
                  }}
                />
              </Box>
              {/* Description */}
              <Typography align="center" mb={2} dangerouslySetInnerHTML={{ __html: docData.document_description }} />
              {/* Like, View, Share Row */}
              <Box display="flex" justifyContent="space-between" alignItems="center" gap={4} mb={2}>
                <Button startIcon={<ThumbUpOutlined sx={{ fontSize: 80 }} />} size="large" onClick={handleLikeClick}>0</Button>
                <Button startIcon={<CommentIcon sx={{ fontSize: 80 }} />} size="large" onClick={handleCommentsModalOpen}>{getTotalCommentCount()}</Button>
                <Button startIcon={<VisibilityOutlined sx={{ fontSize: 80 }} />} size="large">0</Button>
                <Button startIcon={<SendIcon sx={{ fontSize: 80 }} />} size="large" onClick={handleShareClick}>Share</Button>
              </Box>
              <Popover
                open={open}
                anchorEl={anchorEl}
                onClose={handleShareClose}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
                transformOrigin={{ vertical: 'top', horizontal: 'center' }}
              >
                <Box sx={{ display: 'flex', p: 2, gap: 2 }}>
                  <IconButton 
                    aria-label="email"
                    onClick={handleEmailShare}
                    sx={{ 
                      '&:hover': { bgcolor: '#EA433533' },
                      '& .MuiSvgIcon-root': { color: '#EA4335' }
                    }}
                  >
                    <EmailIcon fontSize="large" />
                  </IconButton>
                  <IconButton 
                    aria-label="facebook"
                    onClick={handleFacebookShare}
                    sx={{ 
                      '&:hover': { bgcolor: '#1877F233' },
                      '& .MuiSvgIcon-root': { color: '#1877F2' }
                    }}
                  >
                    <FacebookIcon fontSize="large" />
                  </IconButton>
                  <IconButton 
                    aria-label="twitter"
                    onClick={handleTwitterShare}
                    sx={{ 
                      '&:hover': { bgcolor: '#1DA1F233' },
                      '& .MuiSvgIcon-root': { color: '#1DA1F2' }
                    }}
                  >
                    <TwitterIcon fontSize="large" />
                  </IconButton>
                  <IconButton 
                    aria-label="whatsapp"
                    onClick={handleWhatsAppShare}
                    sx={{ 
                      '&:hover': { bgcolor: '#25D36633' },
                      '& .MuiSvgIcon-root': { color: '#25D366' }
                    }}
                  >
                    <WhatsAppIcon fontSize="large" />
                  </IconButton>
                  <IconButton 
                    aria-label="linkedin"
                    onClick={handleLinkedInShare}
                    sx={{ 
                      '&:hover': { bgcolor: '#0A66C233' },
                      '& .MuiSvgIcon-root': { color: '#0A66C2' }
                    }}
                  >
                    <LinkedInIcon fontSize="large" />
                  </IconButton>
                </Box>
              </Popover>
              {/* Feature Not Available Modal */}
              <Dialog
                open={featureModal}
                onClose={handleFeatureModalClose}
                maxWidth="xs"
                PaperProps={{
                  sx: {
                    borderRadius: 2,
                    p: 2
                  }
                }}
              >
                <Box sx={{ 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center',
                  textAlign: 'center',
                  p: 2 
                }}>
                  <InfoOutlined 
                    sx={{ 
                      fontSize: 48, 
                      color: 'primary.main',
                      mb: 2,
                      p: 1,
                      borderRadius: '50%',
                      border: 2,
                      borderColor: 'primary.main'
                    }} 
                  />
                  <Typography variant="body1" sx={{ mb: 2 }}>
                    This feature is not yet available but is in progress for the next version release.
                  </Typography>
                  <Button 
                    variant="contained" 
                    onClick={handleFeatureModalClose}
                    sx={{ minWidth: 100 }}
                  >
                    OK
                  </Button>
                </Box>
              </Dialog>
              
              {/* Comments Modal */}
              <Dialog
                open={commentsModalOpen}
                onClose={handleCommentsModalClose}
                maxWidth="md"
                fullWidth
                PaperProps={{
                  sx: {
                    borderRadius: 2,
                    maxHeight: '80vh',
                    bgcolor: 'background.paper'
                  }
                }}
              >
                <DialogTitle sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  borderBottom: '1px solid rgba(0,0,0,0.1)',
                  py: 2
                }}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CommentIcon />
                    <Typography variant="h6" fontWeight={600}>
                      Comments ({getTotalCommentCount()})
                    </Typography>
                  </Box>
                  <IconButton
                    aria-label="close"
                    onClick={handleCommentsModalClose}
                    sx={{ color: 'primary.contrastText' }}
                  >
                    <CloseIcon />
                  </IconButton>
                </DialogTitle>
                <DialogContent sx={{ p: 0, bgcolor: 'background.paper' }}>
                  {commentsLoading ? (
                    <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '200px' }}>
                      <CircularProgress />
                    </Box>
                  ) : comments.length === 0 ? (
                    <Box sx={{ textAlign: 'center', py: 6, bgcolor: 'background.paper' }}>
                      <CommentIcon sx={{ fontSize: 64, color: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300', mb: 2 }} />
                      <Typography variant="h6" color="text.secondary" mb={1}>
                        No comments yet
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        Be the first to share your thoughts!
                      </Typography>
                    </Box>
                  ) : (
                    <Box sx={{ p: 2, bgcolor: 'background.paper' }}>
                      {/* Add New Comment Section */}
                      <Box sx={{ mb: 3, p: 2, borderRadius: 2, bgcolor: theme.palette.mode === 'dark' ? '#141a3a' : 'grey.50', border: '1px solid', borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200' }}>
                        {/* Error Message */}
                        {commentError && (
                          <Box sx={{ mb: 2, p: 1.5, borderRadius: 1, bgcolor: 'error.light', border: '1px solid', borderColor: 'error.main' }}>
                            <Typography variant="body2" color="error.dark" sx={{ fontWeight: 500 }}>
                              ⚠️ {commentError}
                            </Typography>
                          </Box>
                        )}
                        
                        {/* Success Message */}
                        {commentSuccess && (
                          <Box sx={{ mb: 2, p: 1.5, borderRadius: 1, bgcolor: 'success.light', border: '1px solid', borderColor: 'success.main' }}>
                            <Typography variant="body2" color="success.dark" sx={{ fontWeight: 500 }}>
                              ✅ {commentSuccess}
                            </Typography>
                          </Box>
                        )}
                        
                        <TextField
                          placeholder="💭 Share your thoughts..."
                          fullWidth
                          size="medium"
                          multiline
                          minRows={3}
                          value={comment}
                          onChange={e => setComment(e.target.value)}
                          sx={{ 
                            mb: 2,
                            '& .MuiOutlinedInput-root': {
                              bgcolor: 'background.paper',
                              borderRadius: 2,
                              fontSize: '0.95rem',
                              '&:hover .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'primary.main',
                              },
                              '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                                borderColor: 'primary.main',
                                borderWidth: 2,
                              },
                              '& .MuiOutlinedInput-input': {
                                color: 'text.primary'
                              }
                            }
                          }}
                        />
                        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                          <Button
                            variant="contained"
                            endIcon={commentLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                            size="medium"
                            sx={{ 
                              textTransform: 'none',
                              fontWeight: 600,
                              px: 4,
                              py: 1,
                              borderRadius: 2,
                              bgcolor: 'primary.main',
                              '&:hover': {
                                bgcolor: 'primary.dark',
                                transform: 'translateY(-1px)',
                                boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                              },
                              '&:disabled': {
                                bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300'
                              }
                            }}
                            onClick={handleCommentSubmit}
                            disabled={commentLoading || !comment.trim()}
                          >
                            {commentLoading ? 'Posting...' : 'Post Comment'}
                          </Button>
                        </Box>
                      </Box>

                      {/* Comments List */}
                      <Box sx={{ maxHeight: '400px', overflowY: 'auto', pr: 1 }}>
                        {comments.map((comment, index) => (
                          <Box key={comment.id || index} sx={{ mb: 2 }}>
                            {/* Main Comment */}
                            <Box
                              sx={{
                                p: 2,
                                borderRadius: 2,
                                bgcolor: theme.palette.mode === 'dark' ? '#141a3a' : 'grey.50',
                                border: '1px solid',
                                borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200',
                                transition: 'all 0.2s ease-in-out',
                                '&:hover': {
                                  bgcolor: theme.palette.mode === 'dark' ? '#1e2756' : 'grey.100',
                                  borderColor: 'primary.light',
                                  transform: 'translateY(-1px)',
                                  boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                                }
                              }}
                            >
                              <Box sx={{ display: 'flex', gap: 2 }}>
                                <Avatar 
                                  src={comment.user_avatar || '/default-avatar.png'} 
                                  alt={comment.user_name}
                                  sx={{
                                    width: 44,
                                    height: 44,
                                    border: '2px solid',
                                    borderColor: 'primary.light'
                                  }}
                                />
                                <Box sx={{ flex: 1, minWidth: 0 }}>
                                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                                    <Typography 
                                      variant="subtitle1" 
                                      fontWeight={600}
                                      color="primary.main"
                                      sx={{ fontSize: '0.95rem' }}
                                    >
                                      {comment.user_name}
                                    </Typography>
                                    <Typography 
                                      variant="caption" 
                                      color="text.secondary"
                                      sx={{
                                        bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.100',
                                        px: 1,
                                        py: 0.5,
                                        borderRadius: 1,
                                        fontSize: '0.75rem'
                                      }}
                                    >
                                      {formatCommentDate(comment.created_at)}
                                    </Typography>
                                  </Box>
                                  <Typography 
                                    variant="body1" 
                                    sx={{ 
                                      mb: 2,
                                      lineHeight: 1.6,
                                      color: 'text.primary'
                                    }}
                                  >
                                    {comment.comment_text}
                                  </Typography>
                                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                    <Button 
                                      size="small" 
                                      onClick={() => handleReplyClick(comment.id)}
                                      startIcon={<CommentIcon sx={{ fontSize: 16 }} />}
                                      sx={{ 
                                        textTransform: 'none', 
                                        fontSize: '0.8rem',
                                        fontWeight: 500,
                                        color: 'primary.main',
                                        '&:hover': {
                                          bgcolor: 'primary.light',
                                          color: 'white'
                                        }
                                      }}
                                    >
                                      Reply
                                    </Button>
                                    
                                    {/* Replies Toggle Button */}
                                    {comment.replies && comment.replies.length > 0 && (
                                      <Button
                                        size="small"
                                        onClick={() => toggleRepliesExpansion(comment.id)}
                                        sx={{
                                          textTransform: 'none',
                                          fontSize: '0.8rem',
                                          fontWeight: 500,
                                          color: 'text.secondary',
                                          '&:hover': {
                                            bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200',
                                            color: 'text.primary'
                                          }
                                        }}
                                      >
                                        {expandedReplies.has(comment.id) 
                                          ? `🔽 Hide ${comment.replies.length} ${comment.replies.length === 1 ? 'reply' : 'replies'}`
                                          : `💬 View ${comment.replies.length} ${comment.replies.length === 1 ? 'reply' : 'replies'}`
                                        }
                                      </Button>
                                    )}
                                  </Box>
                                </Box>
                              </Box>
                            </Box>

                            {/* Reply Input */}
                            {replyingTo === comment.id && (
                              <Box 
                                sx={{ 
                                  ml: 6, 
                                  mr: 1, 
                                  mt: 2,
                                  p: 2,
                                  borderRadius: 2,
                                  bgcolor: theme.palette.mode === 'dark' ? 'primary.dark' : 'primary.light',
                                  border: '1px solid',
                                  borderColor: 'primary.main'
                                }}
                              >
                                <TextField
                                  placeholder={`Reply to ${comment.user_name}...`}
                                  fullWidth
                                  size="small"
                                  multiline
                                  minRows={3}
                                  value={replyText}
                                  onChange={(e) => setReplyText(e.target.value)}
                                  sx={{ 
                                    mb: 2,
                                    '& .MuiOutlinedInput-root': {
                                      bgcolor: 'background.paper',
                                      borderRadius: 2,
                                      '&:hover .MuiOutlinedInput-notchedOutline': {
                                        borderColor: 'primary.main',
                                      },
                                      '& .MuiOutlinedInput-input': {
                                        color: 'text.primary'
                                      }
                                    }
                                  }}
                                />
                                <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                                  <Button
                                    size="small"
                                    onClick={handleCancelReply}
                                    sx={{
                                      textTransform: 'none',
                                      color: 'text.secondary',
                                      '&:hover': {
                                        bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200'
                                      }
                                    }}
                                  >
                                    Cancel
                                  </Button>
                                  <Button
                                    variant="contained"
                                    size="small"
                                    onClick={() => handleReplySubmit(comment.id)}
                                    disabled={commentLoading || !replyText.trim()}
                                    sx={{
                                      textTransform: 'none',
                                      fontWeight: 600,
                                      px: 3,
                                      borderRadius: 2,
                                      bgcolor: 'primary.main',
                                      '&:hover': {
                                        bgcolor: 'primary.dark'
                                      }
                                    }}
                                  >
                                    {commentLoading ? <CircularProgress size={16} color="inherit" /> : 'Reply'}
                                  </Button>
                                </Box>
                              </Box>
                            )}

                            {/* Replies - Show when expanded */}
                            {comment.replies && comment.replies.length > 0 && expandedReplies.has(comment.id) && (
                              <Box sx={{ ml: 6, mt: 2 }}>
                                {comment.replies.map((reply, replyIndex) => (
                                  <Box
                                    key={reply.id || replyIndex}
                                    sx={{
                                      p: 2,
                                      mb: 1.5,
                                      borderRadius: 2,
                                      bgcolor: theme.palette.mode === 'dark' ? '#0d1b3a' : 'white',
                                      border: '1px solid',
                                      borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300',
                                      borderLeft: '3px solid',
                                      borderLeftColor: 'primary.light',
                                      transition: 'all 0.2s ease-in-out',
                                      '&:hover': {
                                        bgcolor: theme.palette.mode === 'dark' ? '#141a3a' : 'grey.50',
                                        borderLeftColor: 'primary.main',
                                        transform: 'translateX(4px)',
                                        boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                                      }
                                    }}
                                  >
                                    <Box sx={{ display: 'flex', gap: 1.5 }}>
                                      <Avatar 
                                        src={reply.user_avatar || '/default-avatar.png'} 
                                        alt={reply.user_name}
                                        sx={{ 
                                          width: 36, 
                                          height: 36,
                                          border: '2px solid',
                                          borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300'
                                        }}
                                      />
                                      <Box sx={{ flex: 1, minWidth: 0 }}>
                                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                          <Typography 
                                            variant="subtitle2" 
                                            fontWeight={600} 
                                            fontSize="0.85rem"
                                            color="primary.main"
                                          >
                                            {reply.user_name}
                                          </Typography>
                                          <Typography 
                                            variant="caption" 
                                            color="text.secondary"
                                            sx={{
                                              bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.100',
                                              px: 0.8,
                                              py: 0.3,
                                              borderRadius: 0.8,
                                              fontSize: '0.7rem'
                                            }}
                                          >
                                            {formatCommentDate(reply.created_at)}
                                          </Typography>
                                        </Box>
                                        <Typography 
                                          variant="body2" 
                                          fontSize="0.85rem" 
                                          sx={{ 
                                            lineHeight: 1.5,
                                            color: 'text.primary'
                                          }}
                                        >
                                          {reply.comment_text}
                                        </Typography>
                                      </Box>
                                    </Box>
                                  </Box>
                                ))}
                              </Box>
                            )}
                          </Box>
                        ))}
                      </Box>
                    </Box>
                  )}
                </DialogContent>
              </Dialog>
              
              {/* Sections */}
              {sectionData.map((section, idx) => (
                <Box key={section.label} display="flex" alignItems="center" justifyContent="space-between" mb={2} p={2} borderRadius={2} bgcolor='theme.content'>
                  <Box>
                    <Typography fontWeight={600}>{section.label}</Typography>
                    <Typography variant="caption">Number of {section.label}: {section.count}</Typography>
                  </Box>
                  <Button 
                    variant="contained" 
                    size="small" 
                    endIcon={<VisibilityOutlined />}
                    onClick={() => handleViewSection(section)}
                    disabled={section.count === 0}
                  >
                    VIEW
                  </Button>
              </Box>
              ))}

              {/* Modal for viewing section details */}
              <Dialog
                open={modalOpen}
                onClose={handleCloseModal}
                maxWidth="md"
                fullWidth
                PaperProps={{
                  sx: {
                    bgcolor: 'background.paper',
                  }
                }}
              >
                <DialogTitle sx={{ 
                  display: 'flex', 
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  bgcolor: 'primary.main',
                  color: 'primary.contrastText',
                  borderBottom: '1px solid rgba(0,0,0,0.1)'
                }}>
                  {selectedSection?.label}
                  <IconButton
                    aria-label="close"
                    onClick={handleCloseModal}
                    sx={{ color: 'primary.contrastText' }}
                  >
                    <CloseIcon />
                  </IconButton>
                </DialogTitle>
                <DialogContent sx={{ p: 0 }}>
                  {(selectedSection?.label === 'Publication(s)' || selectedSection?.label === 'Document(s)') && (
                    <List sx={{ width: '100%', p: 0 }}>
                      {selectedSection.data.map((item, index) => (
                        <Box key={index} sx={{ p: 3, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
                            <Typography color="primary">{index + 1}.</Typography>
                            <Box sx={{ flex: 1 }}>
                              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                                Title
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.title}
                                InputProps={{
                                  readOnly: true,
                                }}
                                variant="outlined"
                                size="small"
                                sx={{ mb: 2 }}
                              />

                              <Button
                                variant="contained"
                                fullWidth
                                onClick={() => handleDownloadFile(item.file_url)}
                                color="primary"
                                sx={{ mb: 2 }}
                              >
                                VIEW FILE
                              </Button>

                              <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                                Description
              </Typography>
                              <TextField
                                fullWidth
                                multiline
                                rows={4}
                                value={item.description?.replace(/<[^>]+>/g, '') || ''}
                                InputProps={{
                                  readOnly: true,
                                }}
                                variant="outlined"
                                size="small"
                                sx={{ mb: 2 }}
                              />

                              <Grid container spacing={2} sx={{ mb: 2 }}>
                                <Grid item xs={12} sm={6}>
                                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                                    Identifier
                                  </Typography>
                                  <TextField
                                    fullWidth
                                    value={getIdentifierLabel(item.identifier)}
                                    InputProps={{
                                      readOnly: true,
                                    }}
                                    variant="outlined"
                                    size="small"
                                  />
                                </Grid>
                                <Grid item xs={12} sm={6}>
                                  <Typography variant="subtitle1" sx={{ mb: 1, fontWeight: 600 }}>
                                    Generated Identifier
              </Typography>
                                  <TextField
                                    fullWidth
                                    value={item.generated_identifier}
                                    InputProps={{
                                      readOnly: true,
                                    }}
                                    variant="outlined"
                                    size="small"
                                  />
                                </Grid>
                              </Grid>
                            </Box>
                          </Box>
                        </Box>
                ))}
              </List>
                  )}
                  {selectedSection?.label === 'Creator(s)' && (
                    <List sx={{ width: '100%', p: 0 }}>
                      {selectedSection.data.map((item, index) => (
                        //console.log(item)
                        <Box key={index} sx={{ p: 3, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                          <Typography variant="h6" sx={{ mb: 3 }}>
                            No. {index + 1}
                          </Typography>

                          <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Full Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={`${item.given_name || ''} ${item.family_name || ''}`}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Family Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.family_name || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Given Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.given_name || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Identifier
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.identifier || 'ORCID'}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Affiliation
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.affiliation || 'DOCiD'}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Role
                              </Typography>
                              <TextField
                                fullWidth
                                value={getRoleName(item.role)}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>
                          </Grid>
                        </Box>
                ))}
              </List>
                  )}
                  {selectedSection?.label === 'Organizations' && (
                    <List sx={{ width: '100%', p: 0 }}>
                      {selectedSection.data.map((item, index) => (
                        <Box key={index} sx={{ p: 3, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                          <Typography variant="h6" sx={{ mb: 3 }}>
                            No. {index + 1}
                          </Typography>

                          <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Organization Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.name || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Organization Type
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.type || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Other Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.other_name || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Country
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.country || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>
                          </Grid>
                        </Box>
                      ))}
                    </List>
                  )}
                  {selectedSection?.label === 'Funders' && (
                    <List sx={{ width: '100%', p: 0 }}>
                      {selectedSection.data.map((item, index) => (
                        <Box key={index} sx={{ p: 3, borderBottom: '1px solid rgba(0,0,0,0.1)' }}>
                          <Typography variant="h6" sx={{ mb: 3 }}>
                            No. {index + 1}
                          </Typography>

                          <Grid container spacing={2}>
                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Organization Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.name || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Organization Type
                              </Typography>
                              <TextField
                                fullWidth
                                value="Funder"
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Other Name
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.other_name || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>

                            <Grid item xs={12} sm={6}>
                              <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
                                Country
                              </Typography>
                              <TextField
                                fullWidth
                                value={item.country || ''}
                                InputProps={{ readOnly: true }}
                                variant="outlined"
                                size="small"
                              />
                            </Grid>
                          </Grid>
                        </Box>
                      ))}
                    </List>
                  )}
                  {selectedSection?.label !== 'Publication(s)' && 
                   selectedSection?.label !== 'Document(s)' && 
                   selectedSection?.label !== 'Creator(s)' &&
                   selectedSection?.label !== 'Organizations' &&
                   selectedSection?.label !== 'Funders' && (
                    <List>
                      {selectedSection?.data.map((item, index) => (
                        <ListItem key={index} divider>
                          <ListItemText
                            primary={item.title || item.name || `${item.given_name} ${item.family_name}` || 'N/A'}
                            secondary={
                              <Box component="span">
                                {item.description && (
                                  <Box 
                                    component="span" 
                                    sx={{ display: 'block', color: 'text.secondary' }}
                                    dangerouslySetInnerHTML={{ __html: item.description }} 
                                  />
                                )}
                                {item.country && (
                                  <Box 
                                    component="span" 
                                    sx={{ display: 'block', color: 'text.secondary' }}
                                  >
                                    Country: {item.country}
                                  </Box>
                                )}
                                {item.role && (
                                  <Box 
                                    component="span" 
                                    sx={{ display: 'block', color: 'text.secondary' }}
                                  >
                                    Role: {item.role}
                                  </Box>
                                )}
                              </Box>
                            }
                          />
                  </ListItem>
                ))}
              </List>
                  )}
                </DialogContent>
              </Dialog>
            </Paper>
          </Grid>
          {/* Sidebar */}
          <Grid item xs={12} md={4}>
            {/* Comments Section */}
            <Paper elevation={0} sx={{ p: 3, mb: 2, borderRadius: 2, boxShadow: '0 2px 8px rgba(0,0,0,0.05)', bgcolor: 'background.paper' }}>
              <Typography fontWeight={600} mb={1} color="text.primary">Comment(s) ({getTotalCommentCount()})</Typography>
              {commentsLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100px' }}>
                  <CircularProgress size={20} />
                </Box>
              ) : comments.length === 0 ? (
                <Typography variant="body2" color="text.secondary" mb={2}>No comments!</Typography>
              ) : (
                <Box>
                  <List sx={{ width: '100%', p: 0 }}>
                    {(showAllComments ? comments : comments.slice(0, 3)).map((comment, index) => (
                      <Box key={comment.id || index}>
                        {/* Main Comment */}
                        <Box
                          sx={{
                            p: 1.5,
                            mb: 1.5,
                            borderRadius: 2,
                            bgcolor: theme.palette.mode === 'dark' ? '#141a3a' : 'grey.50',
                            border: '1px solid',
                            borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200',
                            transition: 'all 0.2s ease-in-out',
                            '&:hover': {
                              bgcolor: theme.palette.mode === 'dark' ? '#1e2756' : 'grey.100',
                              borderColor: 'primary.light',
                              transform: 'translateY(-1px)',
                              boxShadow: '0 2px 8px rgba(0,0,0,0.08)'
                            }
                          }}
                        >
                          <Box sx={{ display: 'flex', gap: 1.5 }}>
                            <Avatar 
                              src={comment.user_avatar || '/default-avatar.png'} 
                              alt={comment.user_name}
                              sx={{
                                width: 40,
                                height: 40,
                                border: '2px solid',
                                borderColor: 'primary.light'
                              }}
                            />
                            <Box sx={{ flex: 1, minWidth: 0 }}>
                              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.5 }}>
                                <Typography 
                                  variant="subtitle2" 
                                  fontWeight={600}
                                  color="primary.main"
                                  sx={{ fontSize: '0.9rem' }}
                                >
                                  {comment.user_name}
                                </Typography>
                                <Typography 
                                  variant="caption" 
                                  color="text.secondary"
                                  sx={{
                                    bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.100',
                                    px: 0.8,
                                    py: 0.3,
                                    borderRadius: 1,
                                    fontSize: '0.7rem'
                                  }}
                                >
                                  {formatCommentDate(comment.created_at)}
                                </Typography>
                              </Box>
                              <Typography 
                                variant="body2" 
                                sx={{ 
                                  mb: 1,
                                  lineHeight: 1.5,
                                  color: 'text.primary',
                                  fontSize: '0.875rem'
                                }}
                              >
                                {comment.comment_text}
                              </Typography>
                              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                                <Button 
                                  size="small" 
                                  onClick={() => handleReplyClick(comment.id)}
                                  startIcon={<CommentIcon sx={{ fontSize: 14 }} />}
                                  sx={{ 
                                    textTransform: 'none', 
                                    fontSize: '0.75rem',
                                    fontWeight: 500,
                                    color: 'primary.main',
                                    minHeight: 'auto',
                                    py: 0.5,
                                    px: 1,
                                    '&:hover': {
                                      bgcolor: 'primary.light',
                                      color: theme.palette.mode === 'dark' ? 'white' : 'white'
                                    }
                                  }}
                                >
                                  Reply
                                </Button>
                                
                                {/* Replies Toggle Button */}
                                {comment.replies && comment.replies.length > 0 && (
                                  <Button
                                    size="small"
                                    onClick={() => toggleRepliesExpansion(comment.id)}
                                    sx={{
                                      textTransform: 'none',
                                      fontSize: '0.75rem',
                                      fontWeight: 500,
                                      color: 'text.secondary',
                                      minHeight: 'auto',
                                      py: 0.5,
                                      px: 1,
                                      '&:hover': {
                                        bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200',
                                        color: 'text.primary'
                                      }
                                    }}
                                  >
                                    {expandedReplies.has(comment.id) 
                                      ? `🔽 Hide ${comment.replies.length} ${comment.replies.length === 1 ? 'reply' : 'replies'}`
                                      : `💬 View ${comment.replies.length} ${comment.replies.length === 1 ? 'reply' : 'replies'}`
                                    }
                                  </Button>
                                )}
                              </Box>
                            </Box>
                          </Box>
                        </Box>

                        {/* Reply Input */}
                        {replyingTo === comment.id && (
                          <Box 
                            sx={{ 
                              ml: 5.5, 
                              mr: 1, 
                              mb: 2,
                              p: 1.5,
                              borderRadius: 2,
                              bgcolor: theme.palette.mode === 'dark' ? 'primary.dark' : 'primary.light',
                              border: '1px solid',
                              borderColor: 'primary.main'
                            }}
                          >
                            <TextField
                              placeholder={`Reply to ${comment.user_name}...`}
                              fullWidth
                              size="small"
                              multiline
                              minRows={2}
                              value={replyText}
                              onChange={(e) => setReplyText(e.target.value)}
                              sx={{ 
                                mb: 1.5,
                                '& .MuiOutlinedInput-root': {
                                  bgcolor: 'background.paper',
                                  borderRadius: 1.5,
                                  fontSize: '0.875rem',
                                  '&:hover .MuiOutlinedInput-notchedOutline': {
                                    borderColor: 'primary.main',
                                  },
                                  '& .MuiOutlinedInput-input': {
                                    color: 'text.primary'
                                  }
                                }
                              }}
                            />
                            <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                              <Button
                                size="small"
                                onClick={handleCancelReply}
                                sx={{
                                  textTransform: 'none',
                                  fontSize: '0.75rem',
                                  color: 'text.secondary',
                                  '&:hover': {
                                    bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200'
                                  }
                                }}
                              >
                                Cancel
                              </Button>
                              <Button
                                variant="contained"
                                size="small"
                                onClick={() => handleReplySubmit(comment.id)}
                                disabled={commentLoading || !replyText.trim()}
                                sx={{
                                  textTransform: 'none',
                                  fontSize: '0.75rem',
                                  fontWeight: 600,
                                  px: 2,
                                  borderRadius: 1.5,
                                  bgcolor: 'primary.main',
                                  '&:hover': {
                                    bgcolor: 'primary.dark'
                                  }
                                }}
                              >
                                {commentLoading ? <CircularProgress size={14} color="inherit" /> : 'Reply'}
                              </Button>
                            </Box>
                          </Box>
                        )}

                        {/* Replies - Only show when expanded */}
                        {comment.replies && comment.replies.length > 0 && expandedReplies.has(comment.id) && (
                          <Box sx={{ ml: 5.5, mb: 1 }}>
                            {comment.replies.map((reply, replyIndex) => (
                              <Box
                                key={reply.id || replyIndex}
                                sx={{
                                  p: 1.5,
                                  mb: 1,
                                  borderRadius: 1.5,
                                  bgcolor: theme.palette.mode === 'dark' ? '#0d1b3a' : 'white',
                                  border: '1px solid',
                                  borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300',
                                  borderLeft: '3px solid',
                                  borderLeftColor: 'primary.light',
                                  transition: 'all 0.2s ease-in-out',
                                  '&:hover': {
                                    bgcolor: theme.palette.mode === 'dark' ? '#141a3a' : 'grey.50',
                                    borderLeftColor: 'primary.main',
                                    transform: 'translateX(2px)',
                                    boxShadow: '0 1px 4px rgba(0,0,0,0.05)'
                                  }
                                }}
                              >
                                <Box sx={{ display: 'flex', gap: 1 }}>
                                  <Avatar 
                                    src={reply.user_avatar || '/default-avatar.png'} 
                                    alt={reply.user_name}
                                    sx={{ 
                                      width: 28, 
                                      height: 28,
                                      border: '1px solid',
                                      borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300'
                                    }}
                                  />
                                  <Box sx={{ flex: 1, minWidth: 0 }}>
                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 0.25 }}>
                                      <Typography 
                                        variant="caption" 
                                        fontWeight={600} 
                                        fontSize="0.8rem"
                                        color="primary.main"
                                      >
                                        {reply.user_name}
                                      </Typography>
                                      <Typography 
                                        variant="caption" 
                                        color="text.secondary"
                                        sx={{ fontSize: '0.65rem' }}
                                      >
                                        {formatCommentDate(reply.created_at)}
                                      </Typography>
                                    </Box>
                                    <Typography 
                                      variant="caption" 
                                      fontSize="0.8rem" 
                                      sx={{ 
                                        lineHeight: 1.4,
                                        color: 'text.primary',
                                        display: 'block'
                                      }}
                                    >
                                      {reply.comment_text}
                                    </Typography>
                                  </Box>
                                </Box>
                              </Box>
                            ))}
                          </Box>
                        )}
                      </Box>
                    ))}
                  </List>
                  
                  {/* Show More/Less Button for Parent Comments */}
                  {comments.length > 3 && (
                    <Box sx={{ textAlign: 'center', mt: 2, mb: 1 }}>
                      <Button
                        variant="outlined"
                        onClick={() => setShowAllComments(!showAllComments)}
                        sx={{ 
                          textTransform: 'none',
                          fontWeight: 600,
                          fontSize: '0.8rem',
                          px: 3,
                          py: 0.8,
                          borderRadius: 2,
                          borderWidth: 1.5,
                          borderColor: 'primary.main',
                          color: 'primary.main',
                          '&:hover': {
                            borderWidth: 1.5,
                            bgcolor: 'primary.light',
                            color: 'white',
                            transform: 'translateY(-1px)',
                            boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
                          }
                        }}
                      >
                        {showAllComments 
                          ? '📖 Show Less Comments' 
                          : `💬 Show All Comments (${comments.length})`
                        }
                      </Button>
                    </Box>
                  )}
                </Box>
              )}
                <Box sx={{ mt: 3, p: 2, borderRadius: 2, bgcolor: theme.palette.mode === 'dark' ? '#141a3a' : 'grey.50', border: '1px solid', borderColor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.200' }}>
                  {/* Error Message */}
                  {commentError && (
                    <Box sx={{ mb: 2, p: 1.5, borderRadius: 1, bgcolor: 'error.light', border: '1px solid', borderColor: 'error.main' }}>
                      <Typography variant="body2" color="error.dark" sx={{ fontWeight: 500 }}>
                        ⚠️ {commentError}
                      </Typography>
                    </Box>
                  )}
                  
                  {/* Success Message */}
                  {commentSuccess && (
                    <Box sx={{ mb: 2, p: 1.5, borderRadius: 1, bgcolor: 'success.light', border: '1px solid', borderColor: 'success.main' }}>
                      <Typography variant="body2" color="success.dark" sx={{ fontWeight: 500 }}>
                        ✅ {commentSuccess}
                      </Typography>
                    </Box>
                  )}
                  
                  <TextField
                    placeholder="💭 Share your thoughts..."
                    fullWidth
                    size="medium"
                    multiline
                    minRows={3}
                    value={comment}
                    onChange={e => setComment(e.target.value)}
                    sx={{ 
                      mb: 2,
                      '& .MuiOutlinedInput-root': {
                        bgcolor: 'background.paper',
                        borderRadius: 2,
                        fontSize: '0.95rem',
                        '&:hover .MuiOutlinedInput-notchedOutline': {
                          borderColor: 'primary.main',
                        },
                        '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
                          borderColor: 'primary.main',
                          borderWidth: 2,
                        },
                        '& .MuiOutlinedInput-input': {
                          color: 'text.primary'
                        }
                      }
                    }}
                  />
                  <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                    <Button
                      variant="contained"
                      endIcon={commentLoading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
                      size="medium"
                      sx={{ 
                        textTransform: 'none',
                        fontWeight: 600,
                        px: 4,
                        py: 1,
                        borderRadius: 2,
                        bgcolor: 'primary.main',
                        '&:hover': {
                          bgcolor: 'primary.dark',
                          transform: 'translateY(-1px)',
                          boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
                        },
                        '&:disabled': {
                          bgcolor: theme.palette.mode === 'dark' ? '#2a3275' : 'grey.300'
                        }
                      }}
                      onClick={handleCommentSubmit}
                      disabled={commentLoading || !comment.trim()}
                    >
                      {commentLoading ? 'Posting...' : 'Post Comment'}
                    </Button>
                  </Box>
                </Box>
            </Paper>
            {/* Related Docids */}
            <Button variant="outlined" fullWidth sx={{ 
              py: 2,
              borderColor: 'primary.main',
              color: 'primary.main',
              bgcolor: 'background.paper',
              '&:hover': {
                borderColor: 'primary.dark',
                bgcolor: 'primary.light',
                color: theme.palette.mode === 'dark' ? 'white' : 'white'
              }
            }}>
              Related Docids
            </Button>
          </Grid>
        </Grid>
      </Container>
    </Box>
  );
};

export default DocIDPage; 