import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request) {
  try {
    const { email, name, password, picture, username, affiliation, token, account_type_id } = await request.json();

    try {
      // First, verify the registration token
      await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/complete-registration`,
        { token, email }
      );
    } catch (error) {
      // If token verification fails or user not found, proceed with registration
      if (error.response?.data || error.message === "User not found") {
        const registrationResponse = await axios.post(
          `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/register`,
          {
            social_id: "",
            full_name: name,
            email: email,
            type: "email",
            avator: picture,
            timestamp: Date.now().toString(),
            user_name: username,
            affiliation: affiliation,
            password: password,
            account_type_id: account_type_id,
          }
        );

        if (registrationResponse.data.message === 'User already exists') {
          return NextResponse.json(
            { status: false, message: "Username provided already exists!" },
            { status: 400 }
          );
        } else {
          return NextResponse.json(
            { status: true, message: "Successfully Registered!" },
            { status: 200 }
          );
        }
      } else {
        return NextResponse.json(
          { status: false, message: "Invalid Email or token!" },
          { status: 400 }
        );
      }
    }

    // If we get here, the token was valid and registration is complete
    return NextResponse.json(
      { status: true, message: "Registration completed successfully!" },
      { status: 200 }
    );

  } catch (error) {
    console.error('Error during registration completion:', error);
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
