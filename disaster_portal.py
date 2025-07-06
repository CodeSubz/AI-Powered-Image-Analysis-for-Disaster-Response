import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore
from firebase_admin import exceptions as firebase_exceptions
from pymongo import MongoClient
import pandas as pd
import smtplib
import ssl
import os
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime, timedelta, timezone

# Load environment variables
load_dotenv()

# Initialize Firebase
if not firebase_admin._apps:
    cred = credentials.Certificate("D:\Downloads\disaster-emails-firebase-adminsdk-fbsvc-3a24796976.json")
    firebase_admin.initialize_app(cred)
db_firestore = firestore.client()

# MongoDB setup
MONGODB_URI = os.getenv("MONGODB_URI")
client = MongoClient(MONGODB_URI)
db_mongo = client["GeoNews"]
collection = db_mongo["disaster_info"]
subscriptions_collection = db_mongo["subscriptions"]

# Email functions
def send_welcome_email(email):
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart('alternative')
    msg['From'] = email_sender
    msg['To'] = email
    msg['Subject'] = "Welcome to Geo-Spatial Visualization for Disaster Monitoring"

    html_content = f"""
    <html>
    <head><style>h2{{font-size:20px;font-weight:bold;}}</style></head>
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
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email, msg.as_string())

def send_subscription_email(email):
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart('alternative')
    msg['From'] = email_sender
    msg['To'] = email
    msg['Subject'] = "Subscription Confirmation"

    html_content = """
    <html>
    <head><style>h2{{font-size:20px;font-weight:bold;}}</style></head>
    <body>
        <p>Congratulations! You are now successfully subscribed to Geospatial Visualization for Disaster Monitoring.</p>
        <p>As a subscriber, you will receive:</p>
        <ol>
            <li><strong>Real-time Alerts</strong></li>
            <li><strong>Geospatial Visualization</strong></li>
            <li><strong>Customizable Preferences</strong></li>
        </ol>
        <p>Best regards,<br>The Geo-Spatial Visualization Team</p>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email, msg.as_string())

def send_dummy_alert_email(email):
    email_sender = os.getenv("EMAIL_SENDER")
    email_password = os.getenv("EMAIL_PASSWORD")
    
    msg = MIMEMultipart('alternative')
    msg['From'] = email_sender
    msg['To'] = email
    msg['Subject'] = "🚨 TEST ALERT: Wildfire Alert - Yellowstone National Park"

    html_content = """
    <html>
    <head>
        <style>
            .alert {{
                color: #d9534f;
                font-weight: bold;
                font-size: 18px;
            }}
            .header {{
                background-color: #f8d7da;
                padding: 10px;
                border-left: 5px solid #d9534f;
            }}
            .content {{
                margin-top: 20px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h2>TEST ALERT: Wildfire Detected</h2>
            <p>This is a test alert from Geo-Spatial Visualization System</p>
        </div>
        
        <div class="content">
            <p class="alert">⚠️ IMPORTANT: This is only a test notification</p>
            
            <h3>Wildfire Alert Details:</h3>
            <ul>
                <li><strong>Location:</strong> Yellowstone National Park</li>
                <li><strong>Severity:</strong> High</li>
                <li><strong>Status:</strong> Spreading rapidly</li>
                <li><strong>Evacuation Notice:</strong> Precautionary evacuation of nearby areas</li>
            </ul>
            
            <h3>Recommended Actions:</h3>
            <ol>
                <li>Avoid the affected area</li>
                <li>Follow local authority instructions</li>
                <li>Prepare emergency supplies</li>
            </ol>
            
            <p>This is a simulated alert to demonstrate our notification system. 
            No actual emergency exists at this time.</p>
            
            <p>Stay safe,<br>
            <strong>Geo-Spatial Visualization Team</strong></p>
        </div>
    </body>
    </html>
    """
    msg.attach(MIMEText(html_content, 'html'))
    
    context = ssl.create_default_context()
    with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
        smtp.login(email_sender, email_password)
        smtp.sendmail(email_sender, email, msg.as_string())

# Data processing function
@st.cache_data
def get_disaster_data():
    df = pd.DataFrame(list(collection.find()))
    df.drop_duplicates(subset='title', inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    df = df.dropna(subset=['Latitude', 'Longitude'])
    
    exclude_locations = ['politics', 'yahoo', 'sports', 'entertainment', 'cricket']
    df = df[~df['Location'].str.lower().isin(exclude_locations)]
    df = df[~df['url'].str.lower().str.contains('politics|yahoo|sports')]
    df = df[~df['title'].str.lower().str.contains('tool|angry')]
    
    df['date_only'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df.drop_duplicates(subset=['date_only', 'disaster_event', 'Location'], inplace=True)
    return df.drop(columns=['date_only', 'location_ner'], errors='ignore')

# Check subscription status
def check_subscription(email):
    subscription = subscriptions_collection.find_one({"email": email})
    return subscription if subscription else None

# Main app
def main():
    st.title(':green[Geo-Spatial Visualization for Disaster Monitoring]')
    
    # Initialize session state
    if 'signed_in' not in st.session_state:
        st.session_state.signed_in = False
    if 'page' not in st.session_state:
        st.session_state.page = "login"
    if 'dummy_alert' not in st.session_state:
        st.session_state.dummy_alert = False
    if 'editing_subscription' not in st.session_state:
        st.session_state.editing_subscription = False

    # Login/Signup Page
    if not st.session_state.signed_in:
        st.subheader("Login / Sign Up")
        choice = st.radio("Select option:", ["Login", "Sign Up"])
        
        email = st.text_input("Email Address")
        password = st.text_input("Password", type="password")
        
        if choice == "Login":
            if st.button("Login"):
                try:
                    user = auth.get_user_by_email(email)
                    st.session_state.signed_in = True
                    st.session_state.user = user
                    st.session_state.useremail = email
                    st.session_state.page = "dashboard"
                    
                    # Get username from Firestore
                    user_doc = db_firestore.collection('users').document(user.uid).get()
                    if user_doc.exists:
                        st.session_state.username = user_doc.to_dict().get('username', '')
                    
                    # Check subscription status
                    st.session_state.subscription = check_subscription(email)
                    st.success("Login Successful!")
                    st.rerun()  # Refresh to show dashboard
                except firebase_exceptions.FirebaseError:
                    st.error("Invalid Login Credentials")
        else:
            username = st.text_input("Username (Unique)")
            if st.button("Create Account"):
                if len(password) < 6:
                    st.error("Password must be at least 6 characters")
                    return
                if any(db_firestore.collection('users').where('username', '==', username).stream()):
                    st.error("Username already taken")
                    return
                try:
                    user = auth.create_user(email=email, password=password)
                    db_firestore.collection('users').document(user.uid).set({
                        'username': username,
                        'email': email
                    })
                    st.session_state.signed_in = True
                    st.session_state.user = user
                    st.session_state.useremail = email
                    st.session_state.username = username
                    st.session_state.page = "dashboard"
                    st.session_state.subscription = None
                    st.success("Account Created Successfully!")
                    send_welcome_email(email)
                    st.rerun()  # Refresh to show dashboard
                except firebase_exceptions.FirebaseError as e:
                    st.error(str(e))

    # Dashboard Page
    elif st.session_state.page == "dashboard":
        st.subheader(f"Welcome, {st.session_state.username or st.session_state.useremail}!")
        st.write(f"Email: {st.session_state.useremail}")
        st.write(f"User ID: {st.session_state.user.uid}")
        
        # Subscription status
        if st.session_state.subscription:
            st.success("✅ You are subscribed to alerts")
            st.write(f"**Events:** {', '.join(st.session_state.subscription['selected_events'])}")
            st.write(f"**Locations:** {', '.join(st.session_state.subscription['selected_locations'])}")
        else:
            st.warning("⚠️ You are not subscribed to alerts")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Subscribe/Manage Alerts"):
                st.session_state.page = "subscribe"
                st.rerun()
        with col2:
            if st.button("Send Test Alert"):
                try:
                    send_dummy_alert_email(st.session_state.useremail)
                    st.success("Test alert sent to your email!")
                except Exception as e:
                    st.error(f"Failed to send test alert: {str(e)}")
        with col3:
            if st.button("Logout"):
                st.session_state.signed_in = False
                st.session_state.page = "login"
                st.session_state.user = None
                st.session_state.subscription = None
                st.rerun()

    # Subscription Page
    elif st.session_state.page == "subscribe":
        st.subheader("Manage Alert Subscriptions")
        
        # Get and filter disaster data
        df = get_disaster_data()
        start_date_min = datetime.utcnow().date() - timedelta(days=2)
        start_date_utc = datetime.combine(start_date_min, datetime.min.time()).replace(tzinfo=timezone.utc)
        
        # Get all available options
        all_events = ["All"] + list(df["disaster_event"].unique())
        all_locations = list(df["Location"].unique())
        
        # Pre-fill with existing subscription if available
        if st.session_state.subscription and not st.session_state.editing_subscription:
            st.info("Current Subscription Settings")
            st.write(f"**Events:** {', '.join(st.session_state.subscription['selected_events'])}")
            st.write(f"**Locations:** {', '.join(st.session_state.subscription['selected_locations'])}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("Edit Subscription"):
                    st.session_state.editing_subscription = True
                    st.rerun()
            with col2:
                if st.button("Cancel Subscription"):
                    subscriptions_collection.delete_one({"_id": st.session_state.subscription["_id"]})
                    st.session_state.subscription = None
                    st.success("Subscription cancelled")
                    st.rerun()
            with col3:
                if st.button("Back to Dashboard"):
                    st.session_state.page = "dashboard"
                    st.session_state.editing_subscription = False
                    st.rerun()
        else:
            # Subscription form
            st.write("Customize your alert preferences:")
            
            # Pre-fill with current subscription if editing
            default_events = st.session_state.subscription["selected_events"] if st.session_state.subscription else []
            default_locations = st.session_state.subscription["selected_locations"] if st.session_state.subscription else []
            
            selected_events = st.multiselect("Select Disaster Events", all_events, default=default_events)
            selected_location = st.multiselect("Select Locations", all_locations, default=default_locations)
            
            # Display sample alerts
            if selected_events and selected_location:
                if "All" in selected_events:
                    filtered_df = df[(df['timestamp'] >= start_date_utc) & df['Location'].isin(selected_location)]
                else:
                    filtered_df = df[(df['timestamp'] >= start_date_utc) & 
                                    df['Location'].isin(selected_location) & 
                                    df['disaster_event'].isin(selected_events)]
                
                st.write(f"Sample alerts matching your criteria ({len(filtered_df)} found):")
                if not filtered_df.empty:
                    st.dataframe(filtered_df[['title', 'disaster_event', 'Location', 'timestamp']].head(3))
            
            # Subscription controls
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Save Subscription"):
                    if not selected_events or not selected_location:
                        st.error("Please select at least one event type and location")
                    else:
                        subscription_data = {
                            "email": st.session_state.useremail,
                            "selected_events": selected_events,
                            "selected_locations": selected_location
                        }
                        
                        if st.session_state.subscription:
                            # Update existing subscription
                            subscriptions_collection.update_one(
                                {"_id": st.session_state.subscription["_id"]},
                                {"$set": subscription_data}
                            )
                            st.success("Subscription updated successfully!")
                        else:
                            # Create new subscription
                            subscriptions_collection.insert_one(subscription_data)
                            send_subscription_email(st.session_state.useremail)
                            st.success("Subscription created successfully!")
                        
                        # Update session state
                        st.session_state.subscription = check_subscription(st.session_state.useremail)
                        st.session_state.editing_subscription = False
                        st.balloons()
                        st.rerun()
            
            with col2:
                if st.button("Cancel"):
                    st.session_state.editing_subscription = False
                    st.session_state.page = "dashboard"
                    st.rerun()

if __name__ == "__main__":
    main()