import axios from 'axios';
import { NextResponse } from 'next/server';

// Create a Map to store recently used codes with timestamps
const recentlyUsedCodes = new Map();
// Time window in milliseconds (30 seconds)
const CODE_REUSE_WINDOW = 30000;

// Define CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Credentials': 'true',
};

// Handle OPTIONS request
export async function OPTIONS(request) {
    return NextResponse.json({}, { headers: corsHeaders });
}

// Handle GET request
export async function GET(request) {
    try {
        console.log('\n=== STEP 1: Starting Google token exchange ===');
        
        const { searchParams } = new URL(request.url);
        const code = searchParams.get('code');

        console.log("code", code);

        // Only check for duplicates if we have a valid code
        if (code) {
            // Check if this code was recently used
            const lastUsed = recentlyUsedCodes.get(code);
            const now = Date.now();

            if (lastUsed && (now - lastUsed) < CODE_REUSE_WINDOW) {
                console.log('\n=== Duplicate request detected, returning cached error ===');
                return NextResponse.json({
                    error: 'Request already processed',
                    code: 'DUPLICATE_REQUEST'
                }, {
                    status: 400,
                    headers: corsHeaders
                });
            }
            
            // Mark this code as used
            recentlyUsedCodes.set(code, now);
            
            // Clean up old codes
            for (const [storedCode, timestamp] of recentlyUsedCodes.entries()) {
                if (now - timestamp > CODE_REUSE_WINDOW) {
                    recentlyUsedCodes.delete(storedCode);
                }
            }
        }

        // Validate code
        if (!code) {
            console.error('\n❌ ERROR: No authorization code provided');
            return NextResponse.json(
                { error: 'Authorization code is required' }, 
                { status: 400, headers: corsHeaders });
        }

        console.log('\n=== STEP 2: Environment Variables Check ===');
        // Log all environment variables (without values for security)
        const envCheck = {
            hasClientId: !!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID,
            hasClientSecret: !!process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET,
            hasRedirectUri: !!process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI
        };
        console.log('Environment variables:', envCheck);

        // Google OAuth Configuration
        const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
        const clientSecret = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET;
        const redirectUri = process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI;
        const tokenUrl = 'https://oauth2.googleapis.com/token';

        console.log('\n=== STEP 3: Fetching Google token ===');
        
        if (!clientId || !clientSecret || !redirectUri) {
            console.error('\n❌ ERROR: Missing Google credentials');
            return NextResponse.json(
                { error: 'Missing Google credentials' },
                { status: 500, headers: corsHeaders }
            );
        }

        // Exchange code for token
        const tokenResponse = await axios.post(
            tokenUrl,
            {
                client_id: clientId,
                client_secret: clientSecret,
                code: code,
                redirect_uri: redirectUri,
                grant_type: 'authorization_code'
            },
            {
                headers: {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
                }
            }
        );

        const { access_token, id_token } = tokenResponse.data;

        if (!access_token || !id_token) {
            console.error('\n❌ ERROR: Missing Google token data');
            return NextResponse.json(
                { error: 'Failed to obtain Google token data' },
                { status: 500, headers: corsHeaders }
            );
        }

        // Get user profile information using the access token
        const userResponse = await axios.get(
            `https://www.googleapis.com/oauth2/v3/userinfo`,
            {
                headers: {
                    Authorization: `Bearer ${access_token}`
                }
            }
        );

        const { sub, name, email, picture } = userResponse.data;

        // Generate a unique ID
        const social_id = sub.toString();

        // First check if user already exists by both social_id and email
        console.log('\n=== STEP 4: Checking if user exists ===');
        
        // Try to get user by email first, which is more reliable
        const getUserByEmailResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/get-user-by-email`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                email: email
            })
        });
        
        // If we found the user by email
        if (getUserByEmailResponse.ok) {
            const existingUser = await getUserByEmailResponse.json();
            
            if (existingUser && existingUser.user_id) {
                console.log('\n=== User found by email, returning existing user data ===');
                
                // If user has a different social_id, consider updating it
                if (existingUser.social_id !== social_id && existingUser.type === 'google') {
                    // Update user's social_id to match their current Google ID
                    try {
                        const updateResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/update-social-id`, {
                            method: 'POST',
                            headers: {
                                'Content-Type': 'application/json'
                            },
                            body: JSON.stringify({
                                user_id: existingUser.user_id,
                                social_id: social_id,
                                type: 'google'
                            })
                        });
                        
                        if (updateResponse.ok) {
                            console.log('\n=== Updated user social_id ===');
                        }
                    } catch (updateError) {
                        console.error('\n❌ ERROR: Failed to update social_id:', updateError);
                    }
                }
                
                const formattedResponse = {
                    affiliation: existingUser.affiliation || "",
                    avatar: existingUser.avatar || picture,
                    email: existingUser.email || email,
                    first_time: 0, // Not first time since user exists
                    full_name: existingUser.full_name || name,
                    message: "User already exists",
                    status: true,
                    type: "google",
                    user_id: existingUser.user_id,
                    user_name: existingUser.user_name || name,
                    social_id: social_id, // Use the current social_id
                };

                return NextResponse.json(formattedResponse, {
                    status: 200,
                    headers: corsHeaders
                });
            }
        }
        
        // If we didn't find the user by email, proceed with regular check
        const checkUserResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/check-user`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                social_id: social_id,
                email: email,
                type: 'google'
            })
        });

        if (checkUserResponse.ok) {
            const existingUser = await checkUserResponse.json();
            
            // If user exists, return their details
            if (existingUser && existingUser.exists) {
                console.log('\n=== User already exists, returning existing user data ===');
                
                const formattedResponse = {
                    affiliation: existingUser.affiliation || "",
                    avatar: existingUser.avatar || picture,
                    email: existingUser.email || email,
                    first_time: 0, // Not first time since user exists
                    full_name: existingUser.full_name || name,
                    message: "User already exists",
                    status: true,
                    type: "google",
                    user_id: existingUser.user_id,
                    user_name: existingUser.user_name || name,
                    social_id: existingUser.social_id || social_id,
                };

                return NextResponse.json(formattedResponse, {
                    status: 200,
                    headers: corsHeaders
                });
            }
        }

        // If user doesn't exist, register them
        console.log('\n=== STEP 5: Registering new user ===');
        try {
            const dbResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    social_id: social_id,
                    full_name: name,
                    email: email,
                    type: 'google',
                    avatar: picture,
                    timestamp: Date.now().toString(),
                    user_name: name,
                    affiliation: "",
                    password: access_token, // Ensure tokens are stored securely
                })
            });

            if (!dbResponse.ok) {
                const errorText = await dbResponse.text();
                console.error('\n❌ ERROR: Failed to send Google user details to the database:', errorText);
                
                // Check if this is a duplicate key error
                if (errorText.includes('duplicate key') && errorText.includes('email')) {
                    console.log('\n=== Email already exists, trying to retrieve user ===');
                    
                    // Try to get user by email as a fallback
                    const getUserFallbackResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/get-user-by-email`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            email: email
                        })
                    });
                    
                    if (getUserFallbackResponse.ok) {
                        const existingUser = await getUserFallbackResponse.json();
                        
                        if (existingUser && existingUser.user_id) {
                            console.log('\n=== User found by email after error, returning existing user data ===');
                            
                            const formattedResponse = {
                                affiliation: existingUser.affiliation || "",
                                avatar: existingUser.avatar || picture,
                                email: existingUser.email || email,
                                first_time: 0,
                                full_name: existingUser.full_name || name,
                                message: "User found with this email",
                                status: true,
                                type: existingUser.type || "google",
                                user_id: existingUser.user_id,
                                user_name: existingUser.user_name || name,
                                social_id: existingUser.social_id || social_id,
                            };

                            return NextResponse.json(formattedResponse, {
                                status: 200,
                                headers: corsHeaders
                            });
                        }
                    }
                    
                    // If we still can't find the user, return an appropriate error
                    return NextResponse.json(
                        { error: 'Email already exists but cannot retrieve user account' },
                        { status: 409, headers: corsHeaders }
                    );
                }
                
                return NextResponse.json(
                    { error: 'Failed to register user in database' },
                    { status: dbResponse.status, headers: corsHeaders }
                );
            }

            const userData = await dbResponse.json();
            console.log("Flask API Response:", userData);

            // Return successful response with Google data
            const formattedResponse = {
                affiliation: userData.affiliation || "",
                avatar: userData.avatar || picture,
                email: userData.email || email,
                first_time: userData.first_time || 1, // First time since this is a new user
                full_name: userData.full_name || name,
                message: userData.message || "User registered successfully",
                status: userData.status || true,
                type: "google",
                user_id: userData.user_id || null,
                user_name: userData.user_name || name,
                social_id: userData.social_id || social_id,
            }

            console.log("Successfully registered user in database", formattedResponse);

            return NextResponse.json(formattedResponse, {
                status: 200,
                headers: corsHeaders
            });
        } catch (registrationError) {
            console.error('\n❌ ERROR: Exception during registration:', registrationError);
            
            // Handle database errors more gracefully
            if (registrationError.message && registrationError.message.includes('duplicate key')) {
                // Try to get user by email as a fallback
                const getUserFallbackResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/get-user-by-email`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        email: email
                    })
                });
                
                if (getUserFallbackResponse.ok) {
                    const existingUser = await getUserFallbackResponse.json();
                    
                    if (existingUser && existingUser.user_id) {
                        console.log('\n=== User found by email after exception, returning existing user data ===');
                        
                        const formattedResponse = {
                            affiliation: existingUser.affiliation || "",
                            avatar: existingUser.avatar || picture,
                            email: existingUser.email || email,
                            first_time: 0,
                            full_name: existingUser.full_name || name,
                            message: "User found with this email",
                            status: true,
                            type: existingUser.type || "google",
                            user_id: existingUser.user_id,
                            user_name: existingUser.user_name || name,
                            social_id: existingUser.social_id || social_id,
                        };

                        return NextResponse.json(formattedResponse, {
                            status: 200,
                            headers: corsHeaders
                        });
                    }
                }
            }
            
            throw registrationError;
        }

    } catch (error) {
        console.error("Error during Google authentication:", error);
        return NextResponse.json({
            error: error.response?.data?.error || error.message || 'Error during authentication',
            code: 'AUTHENTICATION_ERROR'
        }, {
            status: 500,
            headers: corsHeaders
        });
    }
} 