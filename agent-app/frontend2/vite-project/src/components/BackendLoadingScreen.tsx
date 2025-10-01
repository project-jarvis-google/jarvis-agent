import React from 'react';
import { Box, CircularProgress, Typography, Paper } from '@mui/material';

export const BackendLoadingScreen = () => (
  <Box
    sx={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      backgroundColor: '#f5f5f5',
    }}
  >
    <Paper elevation={3} sx={{ p: 4, textAlign: 'center', borderRadius: '16px' }}>
      <Typography variant="h4" component="h1" gutterBottom>
        ✨ Jarvis Agent 🚀
      </Typography>
      <Box sx={{ my: 3 }}>
        <CircularProgress size={60} />
      </Box>
      <Typography variant="h6" color="text.secondary">
        Waiting for backend to be ready...
      </Typography>
      <Typography variant="body2" color="text.secondary">
        This may take a moment
      </Typography>
    </Paper>
  </Box>
);