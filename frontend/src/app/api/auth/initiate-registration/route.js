import axios from 'axios';
import crypto from 'crypto';
import { NextResponse } from 'next/server';
import nodemailer from 'nodemailer';
//import smtpTransport from 'nodemailer-smtp-transport';

//create transporter per-request to ensure env vars are loaded
function createTransporter() {
  return nodemailer.createTransport({
    host: process.env.SMTP_HOST || 'send.one.com',
    port: parseInt(process.env.SMTP_PORT || '465'),
    secure: process.env.SMTP_SECURE === 'false' ? false : true,
    auth: {
      user: process.env.SMTP_USER,
      pass: process.env.SMTP_PASS,
    },
  });
}

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

    // TODO: Add your email verification logic here
    // For example, check if email already exists in database
    // Send verification email, etc.

    try{
        console.log("Email:", email);
        //check if email already exists
        const encodedEmail = encodeURIComponent(email);
        //console.log("Encoded Email:", encodedEmail);

        const checkEmailResponse = await axios.get(
            `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/user/email/${encodedEmail}`
        );

        if(checkEmailResponse.data && checkEmailResponse.data.email === email){
            return NextResponse.json(
                { status: false, message: 'Email provided already exists in our database!' },
                { status: 400 }
            );
        }
    }
    catch(error){
        if(error.response && error.response.status === 404){
            console.log("Email not found, proceeding with registration");
        }
        else{
            console.error("Error checking email:", error);
            throw error;
        }
    }


    //Generate a random token
    const token = crypto.randomBytes(20).toString("hex");
    const expiresAt = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000); //30 days
    const formattedExpiresAt = expiresAt.toISOString().slice(0, 19).replace("T", " ");
    //console.log("Generated token:", token);

    //Store registration token
    console.log("Storing registration token...");
    await axios.post(
        `${process.env.NEXT_PUBLIC_API_BASE_URL}/auth/store-registration-token`,
        { email, token, expires_at: formattedExpiresAt }
    );

    //Send registration email
    const registrationLink = `${process.env.NEXT_PUBLIC_BASE_URL}/complete-registration/${token}`;
    //console.log("Registration link:", registrationLink);

    const text = `Welcome to DOCiD™ APP!\n\nPlease complete your registration by clicking the link below:\n\nRegistration Link: ${registrationLink}\n\nThis link will expire in 1 month. Please complete your registration before then.\n\nIf you did not initiate this registration, please ignore this email.\n\nRegards,\nDOCID Team`;

    const html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0; padding:0; background-color:#f4f6f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#f4f6f9; padding:40px 20px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="background-color:#ffffff; border-radius:12px; overflow:hidden; box-shadow:0 2px 8px rgba(0,0,0,0.08);">
          <!-- Header -->
          <tr>
            <td style="background: linear-gradient(135deg, #1565c0 0%, #141a3b 100%); padding:32px 40px; text-align:center;">
              <h1 style="margin:0; color:#ffffff; font-size:24px; font-weight:700; letter-spacing:0.5px;">DOCiD™</h1>
              <p style="margin:8px 0 0; color:rgba(255,255,255,0.85); font-size:14px;">Digital Object Identifiers (DOIs)</p>
            </td>
          </tr>
          <!-- Body -->
          <tr>
            <td style="padding:40px;">
              <h2 style="margin:0 0 16px; color:#1a1a2e; font-size:20px; font-weight:600;">Welcome!</h2>
              <p style="margin:0 0 24px; color:#555; font-size:15px; line-height:1.6;">
                Thank you for signing up. Please complete your registration by clicking the button below.
              </p>
              <table role="presentation" cellpadding="0" cellspacing="0" style="margin:0 auto 24px;">
                <tr>
                  <td style="background: linear-gradient(135deg, #1565c0 0%, #1976d2 100%); border-radius:8px;">
                    <a href="${registrationLink}" target="_blank" style="display:inline-block; padding:14px 36px; color:#ffffff; text-decoration:none; font-size:15px; font-weight:600; letter-spacing:0.3px;">
                      Complete Registration
                    </a>
                  </td>
                </tr>
              </table>
              <p style="margin:0 0 12px; color:#777; font-size:13px; line-height:1.5;">
                Or copy and paste this link into your browser:
              </p>
              <p style="margin:0 0 24px; word-break:break-all; color:#1565c0; font-size:13px;">
                <a href="${registrationLink}" style="color:#1565c0; text-decoration:underline;">${registrationLink}</a>
              </p>
              <hr style="border:none; border-top:1px solid #eee; margin:24px 0;">
              <p style="margin:0; color:#999; font-size:12px; line-height:1.5;">
                This link will expire in <strong>1 month</strong>. If you did not initiate this registration, please ignore this email.
              </p>
            </td>
          </tr>
          <!-- Footer -->
          <tr>
            <td style="background-color:#f8f9fa; padding:20px 40px; text-align:center; border-top:1px solid #eee;">
              <p style="margin:0; color:#999; font-size:12px;">
                &copy; ${new Date().getFullYear()} DOCiD™ &mdash; Africa PID Alliance
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>`;

    console.log("Preparing to send email...");
    const mailOptions = {
        from: "DOCID Registration <docid@africapidalliance.org>",
        to: email,
        subject: "Complete Your Registration for DOCiD™ APP",
        text: text,
        html: html,
    };
   // console.log("Mail options:", mailOptions);

    const transporter = createTransporter();
    await transporter.sendMail(mailOptions);
    //console.log("Email sent successfully to:", email);      
    
    
    return NextResponse.json(
      { 
        status: true, 
        message: 'Registration link sent to your email',
      },
      { status: 200 }
    );

  } catch (error) {
    console.error('Error during registration:', error.message);
    return NextResponse.json(
      { status: false,
        message: 'Server error. Please try again.' },
      { status: 500 }
    );
  }
} 