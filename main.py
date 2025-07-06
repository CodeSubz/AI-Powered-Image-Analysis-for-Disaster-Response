import streamlit as st
from streamlit_option_menu import option_menu
st.set_page_config(layout="wide")
# Set up the navigation menu
selected = option_menu(
    menu_title="", 
    options=["Home", "Classify", "Prone Area", "Insight","Precausion", "Login", "About"],
    icons=["house", "camera", "map", "info-circle", "bar-chart", "box-arrow-in-right", "exclamation-triangle", "bar-chart", "shield"],
    orientation="horizontal"
)

  
if selected == "Prone Area":
    import prone_area
    prone_area.main()

elif selected == "Login":
    # Run the login.py script
    import disaster_portal
    disaster_portal.main()
    
if selected == "Classify":
    # Run the classify_disaster.py script
    import classify_disaster
    classify_disaster.main()

elif selected == "About":
    # Run the about.py script
    import about
    about.main()
    

elif selected == "Home":
    # Run the home.py script
    import home
    home.main()
    
elif selected == "Insight":
    # Run the home.py script
    import insight
    insight.main()
    
elif selected == "Precausion":
    # Run the precausion.py script
    import precausion
    precausion.main()
