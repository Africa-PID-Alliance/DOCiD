import axios from 'axios';
import { NextResponse } from 'next/server';

export async function POST(request) {
  try {
    const { token, password } = await request.json();
    
    // Input validation
    if (!token) {
      return NextResponse.json(
        { status: false, message: 'Token is required' },
        { status: 400 }
      );
    }
    
    if (!password) {
      return NextResponse.json(
        { status: false, message: 'Password is required' },
        { status: 400 }
      );
    }
    
    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
    
    try {
      const resetResponse = await axios.post(
        `${apiBaseUrl}/auth/reset-password`,
        {
          password: password,
          token: token,
        }
      );
      
      // Return the response data from the backend
      return NextResponse.json(
        { 
          status: true,
          message: resetResponse.data.message || "Password has been reset successfully!", 
        },
        { status: 200 }
      );
    } catch (error) {
      // Handle specific error cases
      if (error.response) {
        const statusCode = error.response.status;
        let message = "Invalid token or request!";
        
        if (statusCode === 400) {
          message = error.response.data.message || "Invalid request parameters";
        } else if (statusCode === 404) {
          message = "Token not found or expired";
        }
        
        return NextResponse.json(
          { status: false, message },
          { status: statusCode }
        );
      }
      
      throw error; // Re-throw for outer catch
    }
  } catch (error) {
    console.error('Error during password reset:', error.message);
    return NextResponse.json(
      { 
        status: false, 
        message: "Server error. Please try again.",
        error: error.message 
      },
      { status: 500 }
    );
  }
} 