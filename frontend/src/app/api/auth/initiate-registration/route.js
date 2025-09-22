import axios from 'axios';
import crypto from 'crypto';
import { NextResponse } from 'next/server';
import nodemailer from 'nodemailer';
//import smtpTransport from 'nodemailer-smtp-transport';

//define the transporter
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

    const text = `  
Welcome to DOCiD™ APP!

Please complete your registration by clicking the link below:

Registration Link: ${registrationLink}

This link will expire in 1 month. Please complete your registration before then.

If you did not initiate this registration, please ignore this email.

Regards,
DOCID Team
`;  

   console.log("Preparing to send email...");
    const mailOptions = {
        from: "DOCID Registration <docid@africapidalliance.org>",
        to: email,
        subject: "Complete Your Registration for DOCiD™ APP",   
        text: text,
    };
   // console.log("Mail options:", mailOptions);

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
    //console.error('Error during registration :', error.message);
    return NextResponse.json(
      { status: false, 
        message: 'Server error. Please try again.' },
      { status: 500 }
    );
  }
} 