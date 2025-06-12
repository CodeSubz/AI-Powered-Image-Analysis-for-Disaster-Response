import streamlit as st
import tensorflow as tf
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import numpy as np
from PIL import Image

def main():
    model = load_model('disaster.h5')
    class_names = ['Cyclone', 'Earthquake', 'Flood', 'Wildfire']

    # Center title using markdown
    st.markdown("<h1 style='text-align: center; color: #4CAF50;'>🌪️ Disaster Image Classifier</h1>", unsafe_allow_html=True)
    st.write("")

    # Center the upload box and button
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        uploaded_file = st.file_uploader("Upload a Disaster Image", type=["jpg", "jpeg", "png"])

        if uploaded_file is not None:
            img = Image.open(uploaded_file)
            st.image(img, caption='Uploaded Image', use_column_width=True)
            st.write("")
            
            if st.button("Classify Disaster"):
                img = img.resize((64, 64))
                img_array = image.img_to_array(img)
                img_array = np.expand_dims(img_array, axis=0)
                img_array = img_array / 255.0

                prediction = model.predict(img_array)
                predicted_class = class_names[np.argmax(prediction)]

                st.success(f"Predicted Disaster: **{predicted_class}**")
