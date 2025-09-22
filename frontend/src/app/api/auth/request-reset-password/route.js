import axios from 'axios';
import crypto from 'crypto';
import { NextResponse } from 'next/server';
import nodemailer from 'nodemailer';

// Define the transporter
const transporter = nodemailer.createTransport(
  {
    
host: 'send.one.com',
  port: 465,
  secure: true, // true for port 465 with SSL/TLS
    auth: {
      user: process.env.NEXT_PUBLIC_SMTP_USER,
      pass: process.env.NEXT_PUBLIC_SMTP_PASS,
    },
    
  }
);

export async function POST(request) {
  try {
    const { email } = await request.json();

    // Input validation
    if (!email) {
      return NextResponse.json(
        { status: false, message: 'Email is required' },
        { status: 400 }
      );
    }

    if (!/\S+@\S+\.\S+/.test(email)) {
      return NextResponse.json(
        { status: false, message: 'Please enter a valid email address' },
        { status: 400 }
      );
    }

    console.log('Requesting password reset for email:', email);
    const token = crypto.randomBytes(32).toString("hex");
    const expiresAt = new Date(Date.now() + 5 * 60 * 1000); // 5 minutes
    const formattedDate = `${expiresAt.getFullYear()}-${String(
      expiresAt.getMonth() + 1
    ).padStart(2, '0')}-${String(expiresAt.getDate()).padStart(2, '0')}T${String(
      expiresAt.getHours()
    ).padStart(2, '0')}:${String(expiresAt.getMinutes()).padStart(2, '0')}:${String(
      expiresAt.getSeconds()
    ).padStart(2, '0')}`;

    try {
      const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
      const frontendBaseUrl = process.env.NEXT_PUBLIC_BASE_URL;

      // Check if email exists
      const encodedEmail = encodeURIComponent(email);
      const checkEmailResponse = await axios.get(
        `${apiBaseUrl}/auth/user/email/${encodedEmail}`
      );

      if (checkEmailResponse.data && checkEmailResponse.data.email === email) {
        // Store the reset token
        const resetTokenResponse = await axios.post(
          `${apiBaseUrl}/auth/request-password-reset`,
          {
            email: email,
            token: token,
            expiresAt: formattedDate
          }
        );

        // Create the reset link
        const resetLink = `${frontendBaseUrl}/reset-password/${token}`;
        
        const text = `
You requested a password reset. Click the link below to reset your password:
    
${resetLink}
    
This link will expire in 5 minutes.
    
If you did not request this change, please ignore this email.
    
Regards,
DOCID Team
`;

        // Send the email
        const mailOptions = {
          from: "DOCID Password Reset <docid@africapidalliance.org>",
          to: email,
          subject: "Password Reset Request",
          text: text,
        };

        await transporter.sendMail(mailOptions);
        console.log("Password reset email sent successfully to:", email);

        return NextResponse.json(
          { 
            status: true,
            message: "Password reset link has been sent to your email." 
          },
          { status: 200 }
        );
      }
    } catch (error) {
      if (error.response && error.response.status === 404) {
        return NextResponse.json(
          { status: false, message: "Email provided does not exist!" },
          { status: 404 }
        );
      }
      throw error; // Re-throw for the outer catch block
    }

    return NextResponse.json(
      { status: false, message: "Something went wrong. Please try again." },
      { status: 500 }
    );

  } catch (error) {
    console.error('Error during password reset request:', error.message);
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
