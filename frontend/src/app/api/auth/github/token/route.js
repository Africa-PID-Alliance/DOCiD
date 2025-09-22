import axios from 'axios';
import { NextResponse } from 'next/server';

//Create a Map to store recently used codes with timestamps
const recentlyUsedCodes = new Map();
//Time window in milliseconds (30 seconds instead of 5 seconds)
const CODE_REUSE_WINDOW = 30000;

//Define CORS headers
const corsHeaders = {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Access-Control-Allow-Credentials': 'true',
};

//Handle OPTIONS request
export async function OPTIONS(request) {
    return NextResponse.json({}, { headers: corsHeaders });
}

//Handle GET request
export async function GET(request) {
    try {
        const redirectUri = process.env.NEXT_PUBLIC_GITHUB_REDIRECT_URI;
        console.log('\n=== STEP 1: Starting GitHub token exchange ===');
        
        const { searchParams } = new URL(request.url);
        const code = searchParams.get('code');

        console.log("code", code)

        //Only check for duplicates if we have a valid code
        if (code) {
            //Check if this code was recently used
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
        }

          //Validate code
          if (!code) {
            console.error('\n❌ ERROR: No authorization code provided');
            return NextResponse.json(
                { error: 'Authorization code is required' }, 
                { status: 400, headers: corsHeaders });
        }

        const response = await axios.post(
            "https://github.com/login/oauth/access_token",
            {
              client_id: process.env.NEXT_PUBLIC_GITHUB_CLIENT_ID,
              client_secret: process.env.NEXT_PUBLIC_GITHUB_CLIENT_SECRET,
              code: code,
              redirect_uri:process.env.NEXT_PUBLIC_GITHUB_REDIRECT_URI,
            },
            {
              headers: {
                Accept: "application/json",
                "Content-Type": "application/x-www-form-urlencoded",
              },
            }
          );
      
          const token = response.data.access_token;
          console.log("token", token)

          // Store the code as recently used
          recentlyUsedCodes.set(code, Date.now());

          // Check if there's an error in the token response
          if (token.error) {
              console.error(`\n❌ GitHub API Error: ${token.error} - ${token.error_description}`);
              return NextResponse.json({
                  error: token.error,
                  error_description: token.error_description,
                  error_uri: token.error_uri
              }, {
                  status: 400,
                  headers: corsHeaders
              });
          }

          // Step 2: Fetch the user's GitHub profile using the access token
    const userResponse = await axios.get("https://api.github.com/user", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });
  
      const { id, name, avatar_url, login } = userResponse.data;

     // Convert social_id to a string (to match the database schema)
    const social_id = id.toString();

    // Generate a unique email using the GitHub username
    const uniqueEmail = `${userResponse.data.login}@github.com`;

 //Step 10: Send ORCID user details to the database
 const dbResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/register`, {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        social_id: social_id,
        full_name: name,
        email: uniqueEmail,
        type: 'github',
        avatar: avatar_url,
        timestamp: Date.now().toString(),
        user_name: login,
        affiliation: "",
        password: token, // Ensure tokens are stored securely
    })
});

if (!dbResponse.ok) {
    console.error('\n❌ ERROR: Failed to send GITHUB user details to the database:', await dbResponse.text());
    return NextResponse.json(
        { error: 'Failed to register user in database' },
        { status: dbResponse.status, headers: corsHeaders }
    );
}

const userData = await dbResponse.json();
console.log("Flask API Response:", userData);


 //Step 11: Return successful response with ORCID data including person details
 const formattedResponse = {
    affiliation: userData.affiliation || "",
    avatar: userData.avator || avatar_url,
    email: userData.email || uniqueEmail,
    first_time: userData.first_time || 0,
    full_name: userData.full_name || name,
    message: userData.message || "User already exists",
    status: userData.status || false,
    type: "github",
    user_id: userData.user_id || null,
    user_name: userData.user_name || login,
    social_id: userData.social_id || social_id,
}


console.log("Successfully registered user in database", formattedResponse);

return NextResponse.json(formattedResponse, {
    status: 200,
    headers: corsHeaders
});

    } catch (error) {
        console.error("Error during callback", error);
        return NextResponse.json({
            error: 'Error during authentication',
            code: 'AUTHENTICATION_ERROR'
        }, {
            status: 500,
            headers: corsHeaders
        });
    }
}

