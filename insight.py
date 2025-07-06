import pandas as pd
import folium
import streamlit as st
import seaborn as sns
from streamlit_folium import st_folium
from datetime import datetime, timedelta, timezone
from pymongo import MongoClient
from folium.plugins import MarkerCluster
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import plotly.express as px
import plotly.graph_objects as go
import ssl
from db_connect import get_database

# Only set page config - no styling
st.set_page_config(
    page_title="Disaster Insights Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    db = get_database()
    collection = db["disaster_info"]
    
    # Convert MongoDB cursor to DataFrame
    df = pd.DataFrame(list(collection.find()))
    df.drop_duplicates(subset='title', inplace=True)    
    # Convert the 'timestamp' column to datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
    exclude_locations = ['unknown', 'not specified', 'n/a']
    # Filter the DataFrame to exclude the locations in the exclude_locations list
    df = df[~df['Location'].str.lower().isin(exclude_locations)]
    df = df[~df['url'].str.lower().str.contains('politics|yahoo|sports')]
    df = df[~df['title'].str.lower().str.contains('tool|angry')]

    df['date_only'] = df['timestamp'].dt.strftime('%Y-%m-%d')

    # Drop duplicate rows based on the combination of date_only, disaster_event, and Location
    df.drop_duplicates(subset=['date_only', 'disaster_event', 'Location'], inplace=True)
    df.drop(columns=['date_only'], inplace=True)

    st.title("🌍 Disaster Monitoring Dashboard")
    st.markdown("### Global Disaster Analysis and Visualization Platform")

    # Disaster event filter at the center
    st.subheader("Select Disaster Events")
    selected_events = st.multiselect("", ["All"] + list(df["disaster_event"].unique()), default=["All"])

    # Sidebar widgets for filtering
    st.sidebar.header('Filter Data')
    
    # Start date filter
    start_date_min = datetime.utcnow().date() - timedelta(days=7)
    start_date_past = datetime(2023, 1, 1).date()
    start_date = st.sidebar.date_input("Start date", start_date_min, min_value=start_date_past,
                                    max_value=datetime.utcnow().date())

    # End date filter
    end_date = st.sidebar.date_input("End date", datetime.utcnow().date(), min_value=start_date_past, 
                                    max_value=datetime.utcnow().date())

    # Convert Streamlit date inputs to timezone-aware datetime objects with UTC timezone
    start_date_utc = datetime.combine(start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
    end_date_utc = datetime.combine(end_date, datetime.max.time()).replace(tzinfo=timezone.utc)

    # Filter dataframe based on selected filters
    if "All" in selected_events:
        filtered_df = df[(df['timestamp'] >= start_date_utc) & (df['timestamp'] <= end_date_utc)]
    else:
        filtered_df = df[(df['timestamp'] >= start_date_utc) & (df['timestamp'] <= end_date_utc) & (
                df['disaster_event'].isin(selected_events))]

    # KPI Cards
    if not filtered_df.empty:
        total_events = len(filtered_df)
        unique_disasters = filtered_df['disaster_event'].nunique()
        countries_affected = filtered_df['Location'].nunique()
        
        kpi1, kpi2, kpi3 = st.columns(3)
        with kpi1:
            st.metric("Total Events", total_events)
        with kpi2:
            st.metric("Disaster Types", unique_disasters)
        with kpi3:
            st.metric("Countries Affected", countries_affected)

    # Check if filtered_df is empty after filtering
    if filtered_df.empty:
        st.info("No disaster data available after filtering based on the selected criteria")
    else:
        # Create tabs for different analysis sections
        tab1, tab2, tab3 = st.tabs(["📊 Overview Analysis", "🌐 Geospatial Analysis", "📈 Trends & Patterns"])
        
        with tab1:
            col1, col2 = st.columns([3, 2])
            
            with col1:
                st.markdown("### Disaster Event Distribution")
                event_location_counts = filtered_df.groupby(['disaster_event', 'Location']).size().reset_index(name='count')
                fig_donut = px.sunburst(
                    event_location_counts,
                    path=['disaster_event', 'Location'],
                    values='count',
                    height=500
                )
                st.plotly_chart(fig_donut, use_container_width=True)
                
                st.markdown("### Disaster Events Timeline")
                event_counts = filtered_df.groupby([filtered_df['timestamp'].dt.date, 'disaster_event']).size().reset_index(name='count')
                fig = px.histogram(event_counts, x='timestamp', y='count', color='disaster_event',
                                labels={'timestamp': 'Date', 'count': 'Event Count', 'disaster_event': 'Disaster Event'},
                                height=400)
                fig.update_xaxes(type='date')
                fig.update_layout(barmode='stack', bargap=0.1)
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.markdown("### Top Disaster Events")
                event_counts = filtered_df['disaster_event'].value_counts().reset_index()
                event_counts.columns = ['disaster_event', 'count']
                top_5_events = event_counts.head(7)
                fig_horizontal_bar = px.bar(
                    top_5_events,
                    x='count',
                    y='disaster_event',
                    orientation='h',
                    labels={'disaster_event': 'Disaster Event', 'count': 'Count'},
                    height=400
                )
                st.plotly_chart(fig_horizontal_bar, use_container_width=True)
                
                st.markdown("### Top Affected Countries")
                location_counts = filtered_df['Location'].value_counts().reset_index()
                location_counts.columns = ['country', 'count']
                top_10_countries = location_counts.head(10)
                fig_vertical_bar = px.bar(
                    top_10_countries,
                    x='count',
                    y='country',
                    orientation='h',
                    labels={'country': 'Country', 'count': 'Count'},
                    height=400
                )
                st.plotly_chart(fig_vertical_bar, use_container_width=True)
                
                st.markdown("### Title Word Cloud")
                titles = filtered_df['title'].dropna()
                wordcloud = WordCloud(width=800, height=400, background_color='white').generate(' '.join(titles))
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis('off')
                st.pyplot(fig)
        
        with tab2:
            st.markdown("### Disaster Density by Country")
            country_counts = filtered_df['Location'].value_counts().reset_index()
            country_counts.columns = ['Country', 'Count']
            
            fig_heatmap = px.choropleth(
                country_counts,
                locations="Country",
                locationmode='country names',
                color="Count",
                hover_name="Country",
                color_continuous_scale='Reds'
            )
            fig_heatmap.update_layout(height=500)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
        with tab3:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                st.markdown("### Disaster Event Frequency")
                
                time_series_df = filtered_df.set_index('timestamp').resample('D').size().reset_index(name='count')
                
                fig = px.line(
                    time_series_df, 
                    x='timestamp', 
                    y='count',
                    labels={'count': 'Number of Events', 'timestamp': 'Date'},
                    height=400
                )
                fig.update_layout(
                    hovermode="x unified",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### Weekly Comparison")
                
                current_week_end = datetime.utcnow().date()
                current_week_start = current_week_end - timedelta(days=7)
                previous_week_end = current_week_start - timedelta(days=1)
                previous_week_start = previous_week_end - timedelta(days=6)
                
                current_week_data = df[(df['timestamp'].dt.date >= current_week_start) & 
                                        (df['timestamp'].dt.date <= current_week_end)]
                previous_week_data = df[(df['timestamp'].dt.date >= previous_week_start) & 
                                        (df['timestamp'].dt.date <= previous_week_end)]
                
                current_week_count = len(current_week_data)
                previous_week_count = len(previous_week_data)
                
                comparison_df = pd.DataFrame({
                    'week': ['Previous Week', 'Current Week'],
                    'count': [previous_week_count, current_week_count]
                })
                
                fig = px.bar(
                    comparison_df,
                    x='week',
                    y='count',
                    labels={'count': 'Number of Events', 'week': ''},
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
                
            with col2:
                st.markdown("### Disaster Comparison")
                
                fig = go.Figure(go.Indicator(
                    mode="number+gauge+delta",
                    value=current_week_count,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    gauge={
                        'axis': {'range': [None, max(current_week_count, previous_week_count, 1)]},
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': current_week_count}},
                    delta={
                        'reference': previous_week_count, 
                        'relative': True,
                        'font': {'size': 16}
                    }
                ))
                
                fig.update_layout(height=300)
                st.plotly_chart(fig, use_container_width=True)
                
                st.markdown("### Recent Events Timeline")
                
                recent_events = filtered_df.sort_values('timestamp', ascending=False).head(10)
                
                fig = px.timeline(
                    recent_events,
                    x_start="timestamp",
                    x_end=recent_events["timestamp"] + pd.Timedelta(hours=1),
                    y="title",
                    color="disaster_event",
                    hover_name="Location",
                    height=400
                )
                
                fig.update_yaxes(autorange="reversed")
                fig.update_layout(
                    xaxis_title="Date",
                    yaxis_title="Event",
                    showlegend=False
                )
                st.plotly_chart(fig, use_container_width=True)

    # Recent events ticker in sidebar
    df_filtered = df[df['disaster_event'].isin(["Earthquake", "Flood", "Cyclone", "Volcano"])]
    seven_days_ago = pd.Timestamp(datetime.utcnow() - timedelta(days=5), tz="UTC")
    filtered_recent_events = df_filtered[df_filtered['timestamp'] >= seven_days_ago]
    filtered_recent_events_sorted = filtered_recent_events.sort_values(by='timestamp', ascending=False)

    # Create marquee content
    marquee_content = ""
    for index, row in filtered_recent_events_sorted.iterrows():
        marquee_content += f"<div style='padding:8px 0;border-bottom:1px solid #eee;'>📌 <a href='{row['url']}' target='_blank'>{row['title']}</a></div>"

    # Render the ticker in the sidebar
    st.sidebar.markdown("<h2>🚨 Recent Alerts</h2>", unsafe_allow_html=True)
    st.sidebar.markdown(f"""
        <div style="height:300px;overflow:hidden;position:relative;">
            <div style="position:absolute;width:100%;animation:ticker 30s linear infinite;">
                {marquee_content}
            </div>
        </div>
        <style>
            @keyframes ticker {{
                0% {{ transform: translateY(100%); }}
                100% {{ transform: translateY(-100%); }}
            }}
        </style>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()