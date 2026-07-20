import { NextResponse } from 'next/server';
import axios from 'axios';

export async function POST(request) {
  try {
    const { email, name, password, picture, username, affiliation, token, account_type_id } = await request.json();

    await axios.post(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/complete-registration`,
      { token, email }
    );

    await axios.post(
      `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/register`,
      {
        social_id: "",
        full_name: name,
        email,
        type: "email",
        avator: picture,
        timestamp: Date.now().toString(),
        user_name: username,
        affiliation,
        password,
        account_type_id,
        registration_token: token,
      },
      { headers: { 'X-Auth-Bootstrap-Secret': process.env.AUTH_BOOTSTRAP_SECRET } }
    );

    return NextResponse.json(
      { status: true, message: "Successfully Registered!" },
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
