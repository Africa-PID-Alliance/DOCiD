import { NextResponse } from 'next/server';

// Create a Map to store recently used codes with timestamps
const recentlyUsedCodes = new Map();
// Time window in milliseconds (30 seconds instead of 5 seconds)
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
        const redirectUri = process.env.NEXT_PUBLIC_ORCID_REDIRECT_URI
        console.log('\n=== STEP 1: Starting ORCID token exchange ===');

        const { searchParams } = new URL(request.url);
        const code = searchParams.get('code');

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

        //Validate code
        if (!code) {
            console.error('\n❌ ERROR: No authorization code provided');
            return NextResponse.json(
                { error: 'Authorization code is required' }, 
                { status: 400, headers: corsHeaders });
        }

        console.log('\n=== STEP 2: Environment Variables Check ===');
        // Log all environment variables (without values for security)
        const envCheck = {
            hasClientId: !!process.env.NEXT_PUBLIC_ORCID_CLIENT_ID,
            hasClientSecret: !!process.env.ORCID_CLIENT_SECRET,
            hasTokenUrl: !!process.env.NEXT_PUBLIC_ORCID_TOKEN_URL,
            hasRedirectLoginUri: !!process.env.NEXT_PUBLIC_ORCID_REDIRECT_LOGIN_URI,
            hasRedirectUri: !!process.env.NEXT_PUBLIC_ORCID_REDIRECT_URI,
            tokenUrl: process.env.NEXT_PUBLIC_ORCID_TOKEN_URL,
            redirectLoginUri: process.env.NEXT_PUBLIC_ORCID_REDIRECT_LOGIN_URI,
            redirectUri: process.env.NEXT_PUBLIC_ORCID_REDIRECT_URI
        };
        console.log('Environment variables:', envCheck);

        console.log('\n=== STEP 3: Received Parameters ===');
        console.log('Authorization code:', code);
        console.log('Redirect URI:', redirectUri);

        //Orcid Sandbox Configuratio
        const clientId = process.env.NEXT_PUBLIC_ORCID_CLIENT_ID;
        const clientSecret = process.env.ORCID_CLIENT_SECRET;
        const tokenUrl = process.env.NEXT_PUBLIC_ORCID_TOKEN_URL;

        console.log('\n=== STEP 4: Fetching ORCID token ===');
        console.log('Client ID Present:', !!clientId);
        console.log('Client Secret Present:', !!clientSecret);
        console.log('Token URL Present:', !!tokenUrl);

        if (!clientId || !clientSecret || !tokenUrl) {
            console.error('\n❌ ERROR: Missing ORCID credentials');
            return NextResponse.json(
                { error: 'Missing ORCID credentials' },
                { status: 500, headers: corsHeaders }
            );
        }

        //exchange code for token
        console.log('\n=== STEP 5: Preparing ORCID Token Request ===');
        const requestBody = new URLSearchParams(
            {
                'client_id': clientId,
                'client_secret': clientSecret,
                'grant_type': 'authorization_code',
                'code': code,
                'redirect_uri': redirectUri
            }
        ).toString();

        console.log('Request Body:', requestBody);

        //Send token request
        console.log('\n=== STEP 6: Sending ORCID Token Request ===');
        const tokenResponse = await fetch(tokenUrl, {
            method: 'POST',
            headers: {
                'Accept': 'application/json',
                'Content-Type': 'application/x-www-form-urlencoded'
            },
            body: requestBody
        });

        console.log('Token Response:', tokenResponse);

        if (!tokenResponse.ok) {
            const errorData = await tokenResponse.json();
            console.error('\n❌ ERROR: ORCID token request failed:', errorData);
            return NextResponse.json(
                { error: errorData.error_description || 'Failed to authenticate with ORCID' },
                { status: tokenResponse.status, headers: corsHeaders }
            );
        }

        const responseText = await tokenResponse.text();

        const { access_token, orcid, name, refresh_token, expires_in, scope, token_type } = JSON.parse(responseText);

       

        if (!access_token || !orcid) {
            console.error('\n❌ ERROR: Missing ORCID token data');
            return NextResponse.json(
                { error: 'Failed to obtain ORCID user details' },
                { status: 500, headers: corsHeaders }
            );
        }

       

        //Step 8 Fetch ORCID user details using the access token
        try {
            const orcidResponse = await fetch(`https://pub.sandbox.orcid.org/v3.0/${orcid}/person`, {
                headers: {
                    'Accept': 'application/vnd.orcid+json',
                    'Authorization': `Bearer ${access_token}`
                }
            });

            if (!orcidResponse.ok) {
                console.error('\n❌ ERROR: Failed to fetch ORCID person details:', await orcidResponse.text());
                return NextResponse.json(
                    { error: 'Failed to fetch ORCID person details' },
                    { status: orcidResponse.status, headers: corsHeaders }
                );
            }

            const personData = await orcidResponse.json();
            console.log('\n=== STEP 8: ORCID Person Details ===');
            console.log('Person Data:', personData);

            //Step 9:generate unique email
            const uniqueEmail = `${orcid}@orcid.org`;

            //Step 10: Send ORCID user details to the database
            const dbResponse = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/register`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    social_id: orcid,
                    full_name: name,
                    email: uniqueEmail,
                    type: 'orcid',
                    avatar: "https://orcid.org/sites/default/files/images/orcid_16x16.png",
                    timestamp: Date.now().toString(),
                    user_name: name,
                    affiliation: "",
                    password: access_token, // Ensure tokens are stored securely
                })
            });

            if (!dbResponse.ok) {
                console.error('\n❌ ERROR: Failed to send ORCID user details to the database:', await dbResponse.text());
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
                avatar: userData.avatar || "https://orcid.org/sites/default/files/images/orcid_16x16.png",
                email: userData.email || uniqueEmail,
                first_time: userData.first_time || 0,
                full_name: userData.full_name || name,
                message: userData.message || "User already exists",
                status: userData.status || false,
                type: "orcid",
                user_id: userData.user_id || null,
                user_name: userData.user_name || name,
                social_id: userData.social_id || orcid,
            }


            console.log("Successfully registered user in database", formattedResponse);

            return NextResponse.json(formattedResponse, {
                status: 200,
                headers: corsHeaders
            });

        } catch (error) {
            console.error('\n❌ ERROR: Failed to fetch ORCID user details:', error);
            return NextResponse.json(
                { error: 'Failed to fetch ORCID user details' },
                { status: 500, headers: corsHeaders }
            );
        }
    } catch (error) {
        console.error('Error during ORCID token exchange:', error);
        return NextResponse.json({ error: 'Internal server error' }, { status: 500 });
    }
}



