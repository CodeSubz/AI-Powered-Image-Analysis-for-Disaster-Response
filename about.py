import streamlit as st

def main():
    st.header("🌍 Geo-Spatial Visualization for Disaster Monitoring")
    st.write(
        """
        **Geo-Spatial Visualization for Disaster Monitoring** is a web application to monitor and visualize disasters in real-time through the analysis of news articles. By extracting valuable information from news sources, the project aims to provide a comprehensive overview of ongoing and past disaster events. 
        """
    )

    st.divider()
    
    st.subheader("🚀 Key Features")
    st.markdown("""
    - **Interactive Map Visualization**: View geographical distribution of disaster events on an interactive map
    - **Advanced Filtering**: Filter events by type and date range
    - **Comprehensive Analytics**: Gain insights through visualizations including:
        - Disaster distribution charts
        - Event timelines
        - Word clouds
    - **Real-time Updates**: Dynamic updates based on user-selected filters
    - **Key Events Feed**: Scrolling marquee with recent events and clickable links
    """)

    st.divider()
    
    st.subheader("📊 Data Sources")
    st.write(
        """
        - Primary data collected from **NewsAPI** service
        - Preprocessed and stored in **MongoDB** (database: GeoNews)
        - Additional sources integrated for enhanced coverage and accuracy
        """
    )

    st.divider()
    
    st.subheader("💻 Technologies Used")
    st.markdown("""
    - **Python**: Core programming language
    - **Streamlit**: Web application framework
    - **Pandas**: Data manipulation and analysis
    - **Folium**: Interactive mapping
    - **Plotly**: Advanced visualizations
    - **MongoDB**: Database management
    - **Geopy**: Geocoding services
    - **WordCloud**: Text visualization
    """)

    st.divider()
    
    st.subheader("🔗 Project Repository")
    st.markdown("[GitHub Repository](https://github.com/CodeSubz/AI-Powered-Image-Analysis-for-Disaster-Response)", unsafe_allow_html=True)
    st.write("Contribute, report issues, or explore the source code")

if __name__ == "__main__":
    main()