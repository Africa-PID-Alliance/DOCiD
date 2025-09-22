import React from 'react';
import { Grid, Skeleton, Card, CardContent, Box } from '@mui/material';

const LoadingState = () => {
  return (
    <Grid container spacing={3}>
      {[1, 2, 3].map((item) => (
        <Grid item xs={12} sm={6} md={4} key={item}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center' }}>
                <Skeleton 
                  variant="circular" 
                  width={40} 
                  height={40} 
                  sx={{ mr: 2 }} 
                />
                <Box sx={{ width: '100%' }}>
                  <Skeleton variant="text" width="80%" />
                  <Skeleton variant="text" width="60%" />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export default LoadingState; 