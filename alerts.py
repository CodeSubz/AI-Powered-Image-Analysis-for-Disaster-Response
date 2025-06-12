import streamlit as st
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
import pandas as pd
from db_connect import get_database
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

def main():
    def send_email(email):
        email_sender  = 'YOUR EMAIL HERE'
        email_password = 'YOUR EMAIL PASSWORD HERE'

        email_receiver = email
        subject = "Subscription Confirmation"

        # Create a message with HTML content
        msg = MIMEMultipart('alternative')
        msg['From'] = email_sender
        msg['To'] = email
        msg['Subject'] = subject

        # Plain text version (optional)
        text_part = MIMEText("Plain text version of the email", 'plain')  # Corrected constructor call
        msg.attach(text_part)
        

        # HTML version with bold formatting and larger headings
        html_part = MIMEText(f"""
    <html>
    <head>
        <style>
            h2 {{
                font-size: 20px;
                font-weight: bold;
            }}
            p, li {{
                font-size: 16px;
            }}
        </style>
    </head>
    <body>
    <p>Congratulations! You are now successfully subscribed to Geospatial Visualization  for Disaster Monitoring. Thank you for choosing to stay informed and prepared in times of crisis.</p>
    <p>As a subscriber, you will receive timely updates and alerts regarding disasters and emergencies around the world based on your preferences. Our system utilizes advanced geospatial technology to provide you with accurate and up-to-date information, helping you make informed decisions to ensure your safety and well-being.</p>
    <p>Here's what you can expect from your subscription:</p>
    <ol>
        <li><strong>Real-time Alerts:</strong> Instant notifications about ongoing disasters, emergencies, and significant events worldwide.</li>
        <li><strong>Geospatial Visualization:</strong> Interactive maps and visualizations to track disaster events and their impact in real-time.</li>
        <li><strong>Customizable Preferences:</strong> Tailor your subscription preferences to receive alerts specific to your location, areas of interest, and types of disasters.</li>
    </ol>
    <p>Stay tuned for your first update, and in the meantime, feel free to explore the our platform and its features.</p>
    <p>Thank you for joining us in our mission to enhance disaster preparedness and response through innovative geospatial technology.</p>
    <p>Best regards,<br>The Geo-Spatial Visualization for Disaster Monitoring Team</p>
</body>

    </html>
    """, 'html')
        msg.attach(html_part)

        # Set Content-Type header for HTML rendering
        msg['Content-Type'] = "text/html"

        # Add SSL (layer of security)
        context = ssl.create_default_context()

        # Log in and send the email
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(email_sender, email_password)
            smtp.sendmail(email_sender, email_receiver, msg.as_string())
    

    # Initialize session state if not already done
    if 'username' not in st.session_state:
        st.session_state.username = ''

        
    try:
        client.admin.command('ping')
        print("MongoDB Atlas connected successfully!")
    except Exception as e:
        print("Connection failed:", e)

    db = get_database()
    collection = db["disaster_info"]


    # ✅ Fetch and clean data
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
    df.drop(columns=['date_only', 'location_ner'], inplace=True)

    # ✅ Streamlit filters
    st.title("Geospatial Visualization for Disaster Monitoring")

    selected_events = st.multiselect("Select Disaster Events", ["All"] + list(df["disaster_event"].unique()), default=["All"])
    selected_location = st.multiselect("Select Disaster Events Location", list(df["Location"].unique()))

    start_date_min = datetime.utcnow().date() - timedelta(days=2)
    start_date_utc = datetime.combine(start_date_min, datetime.min.time()).replace(tzinfo=timezone.utc)

    if "All" in selected_events:
        filtered_df = df[(df['timestamp'] >= start_date_utc) & df['Location'].isin(selected_location)]
    else:
        filtered_df = df[(df['timestamp'] >= start_date_utc) & df['Location'].isin(selected_location) & (df['disaster_event'].isin(selected_events))]

    # ✅ Subscription functionality
    if st.button("Subscribe to Alerts"):
        if st.session_state.username == '':
            st.header(':red[Login Now to Get Custom Alerts]')
        elif not selected_events:
            st.error('Disaster Event is not Selected')
        elif not selected_location:
            st.error('Location is not Selected')
        else:
            subscriptions_db = client["GeoNews"]  # <-- replace with your actual DB name if needed
            subscriptions_collection = subscriptions_db["subscriptions"]  # <-- your collection name
            subscription_data = {
                "email": st.session_state.useremail,
                "selected_events": selected_events,
                "selected_locations": selected_location
            }
            subscriptions_collection.insert_one(subscription_data)
            st.success("Subscription successful! You will receive alerts.")
            st.balloons()
            send_email(st.session_state.useremail)

