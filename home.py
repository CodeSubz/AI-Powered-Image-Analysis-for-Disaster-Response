import streamlit as st
import pandas as pd
import folium
from folium.plugins import MarkerCluster, Fullscreen, MiniMap
from streamlit_folium import st_folium
import plotly.express as px
from datetime import datetime, timedelta, timezone, date
import pytz
from pymongo import MongoClient
import ssl
from db_connect import get_database

# Set page configuration
st.set_page_config(
    page_title="Disaster Monitoring Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for styling
st.markdown("""
<style>
    /* Main content area */
    .stApp {
        background-color: #f0f2f6;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #2c3e50 0%, #1a2530 100%);
        color: white;
    }
    
    /* Title styling */
    .dashboard-title {
        color: #2c3e50;
        border-bottom: 3px solid #3498db;
        padding-bottom: 10px;
    }
    
    /* Ticker styling */
    .ticker-container {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 8px;
        padding: 15px;
        margin-top: 20px;
    }
    
    .ticker-header {
        color: #3498db;
        font-weight: 700;
        margin-bottom: 10px;
    }
    
    .ticker-item {
        padding: 8px 0;
        border-bottom: 1px solid rgba(255,255,255,0.1);
    }
    
    /* Map container */
    .map-container {
        border: 1px solid #ddd;
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* Debug info */
    .debug-info {
        background-color: #fff8e1;
        padding: 10px;
        border-radius: 5px;
        margin-top: 10px;
        font-size: 0.8em;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Database connection
    db = get_database()
    collection = db["disaster_info"]
    
    # Data processing
    df = pd.DataFrame(list(collection.find()))
    st.sidebar.info(f"Total records loaded: {len(df)}")
    
    # Drop duplicates and handle timestamps
    initial_count = len(df)
    df.drop_duplicates(subset='title', inplace=True)
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce', utc=True)
    
    # Debug: Show timestamp range
    min_date = df['timestamp'].min().strftime('%Y-%m-%d') if not df['timestamp'].isnull().all() else 'N/A'
    max_date = df['timestamp'].max().strftime('%Y-%m-%d') if not df['timestamp'].isnull().all() else 'N/A'
    st.sidebar.info(f"Data timestamp range: {min_date} to {max_date}")
    
    # Filter out bad coordinates
    coord_initial = len(df)
    df = df.dropna(subset=['Latitude', 'Longitude', 'timestamp'])
    st.sidebar.info(f"Records with valid coordinates: {len(df)}/{coord_initial}")
    
    # Exclusion filters
    exclude_locations = ['politics', 'yahoo', 'sports', 'entertainment', 'cricket']
    df = df[~df['Location'].str.lower().isin(exclude_locations)]
    df = df[~df['url'].str.lower().str.contains('politics|yahoo|sports')]
    df = df[~df['title'].str.lower().str.contains('tool|angry')]
    
    # Deduplicate
    df['date_only'] = df['timestamp'].dt.strftime('%Y-%m-%d')
    df.drop_duplicates(subset=['date_only', 'disaster_event', 'Location'], inplace=True)
    df.drop(columns=['date_only'], inplace=True)
    st.sidebar.info(f"Final records after deduplication: {len(df)}/{initial_count}")

    # ===== SIDEBAR =====
    with st.sidebar:
        st.sidebar.markdown("<h2 style='text-align: center; color: #3498db;'>🌍 DISASTER MONITOR</h2>", unsafe_allow_html=True)
        
        # Date filters - FIXED DATE INPUTS
        st.subheader("Time Range")
        
        # Default to last 30 days
        default_end = datetime.utcnow().date()
        default_start = default_end - timedelta(days=30)
        
        col1, col2 = st.columns(2)
        with col1:
            # Allow any date selection
            start_date = st.date_input("From", value=default_start)
        with col2:
            # Allow any date selection
            end_date = st.date_input("To", value=default_end)
        
        # Recent events ticker
        st.subheader("Recent Events")
        three_days_ago = datetime.utcnow().replace(tzinfo=timezone.utc) - timedelta(days=3)
        recent_df = df[df['timestamp'] >= three_days_ago]
        
        if not recent_df.empty:
            for _, row in recent_df.head(5).iterrows():
                event_time = row['timestamp'].strftime('%b %d, %H:%M')
                st.markdown(
                    f"<div class='ticker-item'>"
                    f"<b>{row['disaster_event']}</b> in {row['Location']}<br>"
                    f"<small>{event_time}</small><br>"
                    f"<a href='{row['url']}' target='_blank' style='color:#3498db;font-size:0.8em;'>View source</a>"
                    f"</div>",
                    unsafe_allow_html=True
                )
        else:
            st.info("No recent events in the last 72 hours")

    # ===== MAIN CONTENT =====
    st.markdown("<h1 class='dashboard-title'>🌋 Geospatial Disaster Monitoring Dashboard</h1>", unsafe_allow_html=True)
    
    # Event type filter
    all_events = df["disaster_event"].unique().tolist()
    col1, col2 = st.columns([3, 1])
    with col1:
        selected_events = st.multiselect(
            "Select disaster types to monitor:",
            options=all_events,
            default=all_events[:min(3, len(all_events))] if all_events else []
        )
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        show_clusters = st.checkbox("Cluster Markers", value=True)
    
    # FIXED DATE CONVERSION - USE PANDAS FOR CONSISTENCY
    # Convert date inputs to pandas Timestamps for proper comparison
    start_date_utc = pd.Timestamp(start_date).tz_localize('UTC')
    end_date_utc = pd.Timestamp(end_date + timedelta(days=1)).tz_localize('UTC') - pd.Timedelta(seconds=1)
    
    # Filter dataframe
    filtered_df = df[
        (df['timestamp'] >= start_date_utc) & 
        (df['timestamp'] <= end_date_utc)
    ]
    
    # Apply event filter only if events are selected
    if selected_events:
        filtered_df = filtered_df[filtered_df['disaster_event'].isin(selected_events)]
    
    # Show debug info
    with st.expander("Debug Info", expanded=False):
        st.write(f"Date filter: {start_date_utc} to {end_date_utc}")
        st.write(f"Selected events: {selected_events}")
        st.write(f"Filtered records: {len(filtered_df)}")
        if not filtered_df.empty:
            st.write(f"Date range in filtered data: {filtered_df['timestamp'].min().strftime('%Y-%m-%d')} to {filtered_df['timestamp'].max().strftime('%Y-%m-%d')}")
            st.write("First 3 filtered records:", filtered_df[['title', 'timestamp', 'disaster_event']].head(3))
    
    # Show alerts if no data
    if filtered_df.empty:
        st.warning(f"""
        ⚠️ No disaster data found for the selected filters. 
        
        You selected dates: {start_date} to {end_date}
        Data range in database: {min_date} to {max_date}
        
        Try these solutions:
        1. Expand your date range
        2. Select different disaster types
        3. Check if your database has data for this period
        """)
        st.stop()

    # Create map
    with st.container():
        st.subheader("🌍 Global Event Distribution")
        map_col, stats_col = st.columns([3, 1])
        
        with map_col:
            # Calculate map center
            map_center = (filtered_df['Latitude'].mean(), filtered_df['Longitude'].mean())
            
            # Create map with container styling
            with st.container():
                st.markdown('<div class="map-container">', unsafe_allow_html=True)
                mymap = folium.Map(location=map_center, zoom_start=2, tiles='CartoDB dark_matter')
                
                # Add map controls
                Fullscreen().add_to(mymap)
                MiniMap().add_to(mymap)
                
                # Marker cluster or individual markers
                if show_clusters:
                    marker_cluster = MarkerCluster().add_to(mymap)
                    marker_group = marker_cluster
                else:
                    marker_group = mymap
                
                # Define icon mapping
                ICON_MAPPING = {
                    "Earthquake": "https://cdn-icons-png.flaticon.com/128/4140/4140041.png",
                    "Flood": "https://cdn-icons-png.flaticon.com/128/2970/2970785.png",
                    "Wildfire": "https://cdn-icons-png.flaticon.com/128/599/599508.png",
                    "Cyclone": "https://cdn-icons-png.flaticon.com/128/1908/1908921.png",
                    "Volcano": "https://cdn-icons-png.flaticon.com/128/3050/3050483.png",
                    "Tornado": "https://cdn-icons-png.flaticon.com/128/1146/1146850.png",
                    "Tsunami": "https://cdn-icons-png.flaticon.com/128/3273/3273780.png",
                    "Avalanche": "https://cdn-icons-png.flaticon.com/128/6196/6196274.png",
                    "Landslide": "https://cdn-icons-png.flaticon.com/128/6196/6196274.png",
                    "Blizzard": "https://cdn-icons-png.flaticon.com/128/642/642102.png",
                    "Heatwave": "https://cdn-icons-png.flaticon.com/128/2938/2938997.png",
                    "Drought": "https://cdn-icons-png.flaticon.com/128/2938/2938997.png",
                    "default": "https://cdn-icons-png.flaticon.com/128/484/484167.png"
                }
                
                # Add markers
                for _, row in filtered_df.iterrows():
                    icon_url = ICON_MAPPING.get(row['disaster_event'], ICON_MAPPING['default'])
                    custom_icon = folium.CustomIcon(
                        icon_image=icon_url,
                        icon_size=(32, 32),
                        icon_anchor=(16, 16)
                    )
                    
                    popup_content = f"""
                    <div style='min-width:250px'>
                        <b>{row['disaster_event']}</b><br>
                        <b>Location:</b> {row['Location']}<br>
                        <b>Date:</b> {row['timestamp'].strftime('%Y-%m-%d %H:%M')}<br>
                        <a href='{row['url']}' target='_blank'>View full report</a>
                    </div>
                    """
                    
                    folium.Marker(
                        location=[row['Latitude'], row['Longitude']],
                        popup=folium.Popup(popup_content, max_width=300),
                        icon=custom_icon,
                        tooltip=f"{row['disaster_event']} - {row['Location']}"
                    ).add_to(marker_group)
                
                # Display map
                st_folium(mymap, width=700, height=500)
                st.markdown('</div>', unsafe_allow_html=True)
        
        with stats_col:
            st.subheader("📊 Event Summary")
            
            if not filtered_df.empty:
                # Event count by type
                event_counts = filtered_df['disaster_event'].value_counts().reset_index()
                event_counts.columns = ['Event Type', 'Count']
                
                fig = px.bar(
                    event_counts,
                    x='Count',
                    y='Event Type',
                    orientation='h',
                    color='Event Type',
                    height=300
                )
                fig.update_layout(showlegend=False, margin=dict(l=0, r=0, t=0, b=0))
                st.plotly_chart(fig, use_container_width=True)
                
                # Stats cards
                st.metric("Total Events", len(filtered_df))
                st.metric("Locations Covered", filtered_df['Location'].nunique())
                st.metric("Date Range", f"{start_date.strftime('%b %d, %Y')} to {end_date.strftime('%b %d, %Y')}")
    
    # Data table
    if not filtered_df.empty:
        with st.expander("📋 View Detailed Event Data", expanded=False):
            # Format timestamp for display
            display_df = filtered_df.copy()
            display_df['timestamp'] = display_df['timestamp'].dt.strftime('%Y-%m-%d %H:%M')
            
            st.dataframe(
                display_df[['title', 'disaster_event', 'timestamp', 'source', 'url', 'Location']],
                height=300,
                column_config={
                    "url": st.column_config.LinkColumn("Source URL"),
                    "timestamp": "Timestamp"
                }
            )

if __name__ == "__main__":
    main()