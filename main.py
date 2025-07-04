import streamlit as st
from streamlit_option_menu import option_menu
st.set_page_config(layout="wide")
# Set up the navigation menu
selected = option_menu(
    menu_title="", 
    options=["Home","Classify","Insight", "About","Precausion","Login","Alerts"],
    icons=["house","bell", "globe", "info","7-circle","key"],
    orientation="horizontal"
)


if selected == "Alerts":
    # Run the alerts.py script
    import alerts
    alerts.main()
    

elif selected == "Login":
    # Run the login.py script
    import login
    login.main()
    
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
