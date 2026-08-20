import axios from 'axios';
import { NextResponse } from 'next/server';
import { getBackendApiV1BaseUrl } from '@/lib/apiBase';
import { getGoogleRedirectUri } from '@/lib/googleOAuth';

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
            hasClientSecret: !!process.env.GOOGLE_CLIENT_SECRET,
            hasRedirectUri: !!process.env.NEXT_PUBLIC_GOOGLE_REDIRECT_URI
        };
        console.log('Environment variables:', envCheck);

        // Google OAuth Configuration
        const clientId = process.env.NEXT_PUBLIC_GOOGLE_CLIENT_ID;
        const clientSecret = process.env.GOOGLE_CLIENT_SECRET || process.env.NEXT_PUBLIC_GOOGLE_CLIENT_SECRET;
        const redirectUri = getGoogleRedirectUri();
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
        const social_id = sub.toString();

        console.log('\n=== STEP 4: Checking if user exists ===');
        const existingUser = await lookupExistingGoogleUser(social_id, email);

        if (!existingUser) {
            console.log('\n=== Google user has no DOCiD account, skipping auto-registration ===');
            return NextResponse.json({
                needsRegistration: true,
                code: 'ACCOUNT_NOT_FOUND',
                message: 'No DOCiD account is linked to this Google login',
            }, {
                status: 200,
                headers: corsHeaders
            });
        }

        const formattedResponse = {
            affiliation: existingUser.affiliation || "",
            avatar: existingUser.avator || existingUser.avatar || picture,
            email: existingUser.email || email,
            first_time: existingUser.first_time || 0,
            full_name: existingUser.full_name || name,
            message: existingUser.message || "User already exists",
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

async function lookupExistingGoogleUser(socialId, email) {
    const baseUrl = getBackendApiV1BaseUrl();

    const socialResponse = await fetch(
        `${baseUrl}/auth/user/social/${encodeURIComponent(socialId)}`,
        { method: 'GET', headers: { 'Content-Type': 'application/json' } },
    );
    if (socialResponse.ok) {
        return socialResponse.json();
    }

    if (email) {
        const emailResponse = await fetch(
            `${baseUrl}/auth/user/email/${encodeURIComponent(email)}`,
            { method: 'GET', headers: { 'Content-Type': 'application/json' } },
        );
        if (emailResponse.ok) {
            return emailResponse.json();
        }
    }

    return null;
}
