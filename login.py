import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin import exceptions as firebase_exceptions
from firebase_admin import firestore
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Load Firebase credentials
cred = credentials.Certificate("D:\Downloads\disaster-emails-firebase-adminsdk-fbsvc-3a24796976.json")
if not firebase_admin._apps:
    firebase_admin.initialize_app(cred)

# Initialize Firestore
db = firestore.client()

def send_email(email):
    email_sender = 'harshith.savanur01@gmail.com'
    email_password = 'iphd abzd gmgr scbq'
    email_receiver = email
    subject = "Welcome to Geo-Spatial Visualization for Disaster Monitoring"

    msg = MIMEMultipart('alternative')
    msg['From'] = email_sender
    msg['To'] = email_receiver
    msg['Subject'] = subject

    text_part = MIMEText("Plain text version of the email", 'plain')
    msg.attach(text_part)

    html_part = MIMEText(f"""
    <html>
    <head>
      <style>
        h2 {{ font-size: 20px; font-weight: bold; }}
      </style>
    </head>
    <body>
      <p>Dear User,</p>
      <p>Thank you for signing up for Geo-Spatial Visualization for Disaster Monitoring!</p>
      <h2><b>Key Features:</b></h2>
      <ol>
        <li><b>Interactive Map Visualization</b></li>
        <li><b>Advanced Filtering Options</b></li>
        <li><b>Insights and Analytics</b></li>
        <li><b>Key Events Marquee</b></li>
        <li><b>Dynamic Updates</b></li>
      </ol>
      <p>Best regards,<br>Geo-Spatial Visualization Team</p>
    </body>
    </html>
    """, 'html')
    msg.attach(html_part)

    msg['Content-Type'] = "text/html"
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email_receiver, msg.as_string())

def main():
    st.title(':green[Welcome to Geospatial Visualization for Disaster Monitoring]')

    if 'signed_in' not in st.session_state:
        st.session_state.signed_in = False

    if not st.session_state.signed_in:
        choice = st.selectbox('Login / Signup', ['Login', 'Sign Up'])

        email = st.text_input('Email Address')
        password = st.text_input('Password', type='password')

        if choice == 'Login':
            if st.button('Login'):
                try:
                    user = auth.get_user_by_email(email)
                    st.success("Login Successful")
                    st.session_state.signed_in = True
                    st.session_state.user = user
                    
                    db.collection('sessions').document(user.uid).set({
                        'email': email,
                        'is_logged_in': True
                    })
                    
                except firebase_exceptions.FirebaseError as e:
                    st.error("Invalid Login Credentials")
        else:
            username = st.text_input("Username (Unique)")
            if st.button('Create Account'):
                if len(password) < 6:
                    st.error("Password must be at least 6 characters.")
                    return
                docs = db.collection('users').where('username', '==', username).stream()
                if any(docs):
                    st.error("Username already taken.")
                    return
                try:
                    user = auth.create_user(email=email, password=password)
                    db.collection('users').document(user.uid).set({
                        'username': username,
                        'email': email
                    })
                    st.success("Account Created Successfully")
                    send_email(email)
                except firebase_exceptions.FirebaseError as e:
                    st.error(str(e))
    else:
        st.write("You are Logged In ✅")
        st.write("Email:", st.session_state.user.email)
        st.write("User ID:", st.session_state.user.uid)
        user_doc = db.collection('users').document(st.session_state.user.uid).get()
        if user_doc.exists:
            st.write("Username:", user_doc.to_dict()['username'])
        if st.button('Logout'):
            st.session_state.signed_in = False
            st.session_state.user = None

if __name__ == '__main__':
    main()