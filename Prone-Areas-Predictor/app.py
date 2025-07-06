import streamlit as st
import joblib
import pandas as pd
import numpy as np

# Load the trained model
@st.cache_resource
def load_model():
    return joblib.load('prone_area_predictor.joblib')

model = load_model()

# Load region data with features
@st.cache_data
def load_region_data():
    # Load your dataset with region features
    data_path = r'd:\Harshith\RVCE\projects\IDP\Global_Disaster_Monitoring-main\Global_Disaster_Monitoring-main\Prone-Areas-Predictor\world_risk_index.csv'
    df = pd.read_csv(data_path)
    
    # Clean column names
    df.columns = df.columns.str.strip()
    
    # Get latest record for each region
    if 'Year' in df.columns:
        latest_data = df.sort_values('Year', ascending=False).groupby('Region').first().reset_index()
    else:
        latest_data = df.groupby('Region').first().reset_index()
    
    return latest_data

try:
    region_data = load_region_data()
except Exception as e:
    st.error(f"Error loading region data: {str(e)}")
    st.stop()

# Risk mapping system
risk_mapping = {
    'very low': 1,
    'low': 2,
    'moderate': 3,
    'high': 4,
    'very high': 5,
    '1': 1,
    '2': 2,
    '3': 3,
    '4': 4,
    '5': 5
}

risk_colors = {
    1: "#4CAF50",  # Green
    2: "#8BC34A",   # Light Green
    3: "#FFC107",   # Amber
    4: "#FF9800",   # Orange
    5: "#F44336"    # Red
}

risk_labels = {
    1: "Very Low Risk",
    2: "Low Risk",
    3: "Moderate Risk",
    4: "High Risk",
    5: "Very High Risk"
}

risk_descriptions = {
    1: "Minimal disaster risk. These regions have strong infrastructure and low exposure to natural hazards.",
    2: "Low disaster risk. Occasional minor events possible but unlikely to cause significant damage.",
    3: "Moderate disaster risk. Vulnerable to seasonal hazards with potential for localized damage.",
    4: "High disaster risk. Frequent exposure to significant natural hazards requiring preparedness measures.",
    5: "Very high disaster risk. Extremely vulnerable to major disasters with potential for catastrophic impacts."
}

st.set_page_config(
    page_title="Disaster Risk Predictor",
    page_icon="🌋",
    layout="centered"
)

# Sidebar for location selection
with st.sidebar:
    st.title("🌍 Region Selection")
    
    try:
        regions = sorted(region_data['Region'].unique())
        selected_region = st.selectbox(
            "Select Region", 
            regions,
            index=0
        )
    except KeyError:
        st.error("'Region' column not found in dataset")
        st.stop()
    
    st.markdown("---")
    st.info("""
    **About This Tool:**
    - Predicts disaster risk levels based on vulnerability metrics
    - Uses historical data and machine learning
    - Risk levels: Very Low to Very High
    """)
    
    st.markdown("---")
    st.caption("Global Disaster Monitoring System - v1.0")

# Main content area
st.title("🌋Disaster Prone - Areas Prediction")
st.markdown("""
Predict the likelihood of natural disasters in different regions based on vulnerability metrics.
Select a region from the sidebar to get started.
""")

# Display selected region info
if selected_region:
    try:
        region_info = region_data[region_data['Region'] == selected_region].iloc[0]
    except IndexError:
        st.error(f"No data available for region: {selected_region}")
        st.stop()
    
    # Create columns for layout
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader(f"{selected_region}")
        
        # Display metrics
        metrics = [
            ('WRI', 'World Risk Index', '{:.2f}'),
            ('Exposure', 'Exposure Level', '{:.1f}%'),
            ('Vulnerability', 'Vulnerability Score', '{:.1f}')
        ]
        
        for col, label, fmt in metrics:
            if col in region_info:
                st.metric(label, fmt.format(region_info[col]))
        
    with col2:
        # Make prediction
        features = ['WRI', 'Exposure', 'Vulnerability', 'Susceptibility', 
                   'Lack of Coping Capabilities', 'Lack of Adaptive Capacities']
        
        # Check if all features exist
        missing_features = [f for f in features if f not in region_info]
        if missing_features:
            st.error(f"Missing features in data: {', '.join(missing_features)}")
            st.stop()
            
        input_data = region_info[features].to_frame().T
        
        try:
            prediction = model.predict(input_data)[0]
        except Exception as e:
            st.error(f"Prediction error: {str(e)}")
            st.stop()
        
        # Convert prediction to consistent format
        if isinstance(prediction, (int, float)):
            risk_level = int(prediction)
        elif isinstance(prediction, str):
            # Normalize string prediction
            normalized_pred = prediction.lower().strip()
            risk_level = risk_mapping.get(normalized_pred, 3)  # Default to moderate if not found
        else:
            risk_level = 3  # Fallback to moderate
        
        # Ensure risk level is within 1-5 range
        risk_level = max(1, min(5, risk_level))
        
        st.subheader("Risk Prediction")
        
        # Create a clean risk level indicator
        st.markdown(f"""
        <div style="
            text-align: center; 
            padding: 25px; 
            background-color: {risk_colors[risk_level]}20;
            border-radius: 10px; 
            border: 2px solid {risk_colors[risk_level]};
            margin-bottom: 20px;
        ">
            <h1 style="margin: 0; color: {risk_colors[risk_level]};">{risk_labels[risk_level]}</h1>
        </div>
        """, unsafe_allow_html=True)
        
        st.info(f"**Assessment:** {risk_descriptions[risk_level]}")
        
        # Recommended actions
        st.subheader("Recommended Actions")
        if risk_level <= 2:
            st.success("""
            ✅ Maintain current disaster preparedness programs  
            ✅ Continue monitoring environmental changes  
            ✅ Conduct annual disaster response drills
            """)
        elif risk_level == 3:
            st.warning("""
            ⚠️ Review and update emergency response plans  
            ⚠️ Conduct community preparedness drills  
            ⚠️ Invest in early warning systems
            """)
        else:
            st.error("""
            ❗ Invest in disaster-resilient infrastructure  
            ❗ Implement real-time monitoring systems  
            ❗ Develop comprehensive evacuation plans  
            ❗ Establish emergency supply stockpiles
            """)

# Footer
st.markdown("---")
st.caption("""
**Data Sources:** World Risk Index Report • Global Disaster Database  
**Predictive Model:** Random Forest Classifier • Accuracy: 95.3%
""")

