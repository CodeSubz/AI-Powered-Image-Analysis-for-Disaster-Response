import streamlit as st
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pydeck as pdk
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.svm import SVC
from sklearn.neighbors import KNeighborsClassifier
from sklearn.naive_bayes import GaussianNB
from sklearn.metrics import accuracy_score, f1_score, recall_score, precision_score
from imblearn.over_sampling import RandomOverSampler
import joblib
import warnings
warnings.filterwarnings("ignore")

# --- Data Loading ---
data = pd.read_csv('Prediction/natural_disasters_dataset.csv')

# --- Data Preprocessing for Modeling (do not mutate original data) ---
data_processed = data.copy()
data_processed.replace('nan', np.nan, inplace=True)
numerical_cols = data_processed.select_dtypes(include=np.number).columns
imputer = SimpleImputer(strategy='mean')
data_processed[numerical_cols] = imputer.fit_transform(data_processed[numerical_cols])
categorical_cols = data_processed.select_dtypes(include='object').columns
imputer = SimpleImputer(strategy='most_frequent')
data_processed[categorical_cols] = imputer.fit_transform(data_processed[categorical_cols])
label_encoder = LabelEncoder()
for col in categorical_cols:
    data_processed[col] = label_encoder.fit_transform(data_processed[col])

# --- SIDEBAR ---
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to:", [
    "Dashboard Overview",
    "EDA Visualizations",
    "Model Evaluation",
    "GIS Disaster Map"
])

# --- THEME & STYLE ---
st.markdown("""
    <style>
    .main {background-color: #181c25; color: #f0f0f0;}
    .stApp {background-color: #181c25;}
    .css-1d391kg {background-color: #23272f;}
    .st-bb {color: #f0f0f0;}
    .st-cq {color: #f0f0f0;}
    .stDataFrame {background-color: #23272f; color: #f0f0f0;}
    </style>
""", unsafe_allow_html=True)

# --- PAGE LOGIC ---
if page == "Dashboard Overview":
    st.title("🌎 Global Disaster Monitoring Dashboard")
    st.subheader("Key Statistics")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Records", f"{len(data):,}")
    col2.metric("Disaster Types", data['Disaster Type'].nunique())
    col3.metric("Countries", data['Country'].nunique())
    st.write("---")
    st.write("### Quick Data Preview")
    st.dataframe(data.head(20), use_container_width=True)
    st.write("---")
    st.write("#### Explore more using the sidebar!")

elif page == "EDA Visualizations":
    st.header("Exploratory Data Analysis (EDA)")
    # 1. Frequency of Disaster Types by Continent
    st.subheader("Frequency of Disaster Types by Continent")
    disaster_counts = data.groupby(['Continent', 'Disaster Type']).size().unstack(fill_value=0)
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    disaster_counts.plot(kind='bar', stacked=True, colormap='inferno', ax=ax1)
    ax1.set_xlabel('Continent')
    ax1.set_ylabel('Frequency')
    ax1.set_title('Frequency of Disaster Types by Continent')
    ax1.legend(title='Disaster Type', bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig1)

    # Top 5 continents
    st.write("**Top 5 Continents with Most Disasters:**")
    top_continents = disaster_counts.sum(axis=1).nlargest(5)
    st.write(top_continents)

    # 2. Distribution of Disaster Types
    st.subheader("Distribution of Disaster Types")
    disaster_type_counts = data['Disaster Type'].value_counts().sort_values(ascending=False)
    fig2, ax2 = plt.subplots(figsize=(14, 8))
    sns.barplot(x=disaster_type_counts, y=disaster_type_counts.index, ax=ax2)
    for index, value in enumerate(disaster_type_counts):
        ax2.text(value, index, str(value), va='center', fontsize=10, color='black', ha='left')
    ax2.set_title('Distribution of Disaster Types')
    ax2.set_xlabel('Count')
    ax2.set_ylabel('Disaster Type')
    st.pyplot(fig2)

    # 3. Correlation Heatmap
    st.subheader("Correlation Heatmap (Numerical Features)")
    fig3, ax3 = plt.subplots(figsize=(16, 10))
    correlation_matrix = data.select_dtypes(include=[np.number]).corr()
    sns.heatmap(correlation_matrix, annot=False, cmap='magma', ax=ax3)
    ax3.set_title('Correlation Heatmap')
    st.pyplot(fig3)

    # 4. Time Series Analysis of Top 5 Disaster Types
    top_disaster_types = data['Disaster Type'].value_counts().nlargest(5).index
    filtered_data = data[data['Disaster Type'].isin(top_disaster_types)]
    disaster_type_counts = filtered_data.groupby(['Start Year', 'Disaster Type']).size().unstack(fill_value=0)
    fig4, ax4 = plt.subplots(figsize=(14, 8))
    for disaster_type in disaster_type_counts.columns:
        ax4.plot(disaster_type_counts.index, disaster_type_counts[disaster_type], label=disaster_type)
    ax4.set_title('Time Series Analysis of Top 5 Disaster Types Over the Years')
    ax4.set_xlabel('Year')
    ax4.set_ylabel('Frequency')
    ax4.legend()
    st.pyplot(fig4)

elif page == "Model Evaluation":
    st.header("Model Training & Evaluation")
    # Use preprocessed data for modeling
    data_selected = data_processed[
        ['Year', 'Dis Mag Scale', 'Dis Mag Value', 'Country', 'Longitude', 'Latitude', 'Disaster Type']
    ]
    st.subheader("Selected Features for Modeling")
    st.write(data_selected.head())

    X = data_selected.drop('Disaster Type', axis=1)
    y = data_selected['Disaster Type']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Oversampling for balance
    oversampler = RandomOverSampler(random_state=42)
    X_resampled, y_resampled = oversampler.fit_resample(X, y)
    X_train_os, X_test_os, y_train_os, y_test_os = train_test_split(X_resampled, y_resampled, test_size=0.2, random_state=42)
    X_train_os_scaled = scaler.fit_transform(X_train_os)
    X_test_os_scaled = scaler.transform(X_test_os)

    # Models
    def get_metrics(model, X_test, y_test):
        y_pred = model.predict(X_test)
        return {
            'Accuracy': accuracy_score(y_test, y_pred),
            'F1 Score': f1_score(y_test, y_pred, average='weighted'),
            'Recall': recall_score(y_test, y_pred, average='weighted'),
            'Precision': precision_score(y_test, y_pred, average='weighted')
        }

    rf_model = RandomForestClassifier(n_estimators=100, random_state=42)
    svm_model = SVC(kernel='linear', C=1.0, probability=True, random_state=42)
    knn_model = KNeighborsClassifier(n_neighbors=5)
    nb_model = GaussianNB()

    rf_model.fit(X_train_os_scaled, y_train_os)
    svm_model.fit(X_train_os_scaled, y_train_os)
    knn_model.fit(X_train_os_scaled, y_train_os)
    nb_model.fit(X_train_os_scaled, y_train_os)

    metrics_rf = get_metrics(rf_model, X_test_os_scaled, y_test_os)
    metrics_svm = get_metrics(svm_model, X_test_os_scaled, y_test_os)
    metrics_knn = get_metrics(knn_model, X_test_os_scaled, y_test_os)
    metrics_nb = get_metrics(nb_model, X_test_os_scaled, y_test_os)

    ensemble_hard = VotingClassifier(estimators=[
        ('rf', rf_model),
        ('svm', svm_model),
        ('knn', knn_model),
        ('nb', nb_model)
    ], voting='hard')
    ensemble_hard.fit(X_train_os_scaled, y_train_os)
    metrics_ensemble_hard = get_metrics(ensemble_hard, X_test_os_scaled, y_test_os)

    ensemble_soft = VotingClassifier(estimators=[
        ('rf', rf_model),
        ('svm', svm_model),
        ('knn', knn_model),
        ('nb', nb_model)
    ], voting='soft')
    ensemble_soft.fit(X_train_os_scaled, y_train_os)
    metrics_ensemble_soft = get_metrics(ensemble_soft, X_test_os_scaled, y_test_os)

    # Display metrics
    def show_metrics_table(metrics_dicts, model_names):
        df = pd.DataFrame(metrics_dicts, index=model_names)
        st.dataframe(df.style.format("{:.4f}"))

    st.subheader("Model Performance Comparison")
    show_metrics_table([
        metrics_rf, metrics_svm, metrics_knn, metrics_nb, metrics_ensemble_hard, metrics_ensemble_soft
    ], [
        'Random Forest', 'SVM', 'K-NN', 'Naive Bayes', 'Ensemble Hard-Voting', 'Ensemble Soft-Voting'
    ])
    st.subheader("Grouped Bar Chart: Model Evaluation Metrics")
    metrics_names = ['F1 Score', 'Accuracy', 'Recall', 'Precision']
    model_names = ['Random Forest', 'SVM', 'K-NN', 'Naive Bayes', 'Ensemble Hard-Voting', 'Ensemble Soft-Voting']
    metrics_matrix = [
        [metrics_rf['F1 Score'], metrics_rf['Accuracy'], metrics_rf['Recall'], metrics_rf['Precision']],
        [metrics_svm['F1 Score'], metrics_svm['Accuracy'], metrics_svm['Recall'], metrics_svm['Precision']],
        [metrics_knn['F1 Score'], metrics_knn['Accuracy'], metrics_knn['Recall'], metrics_knn['Precision']],
        [metrics_nb['F1 Score'], metrics_nb['Accuracy'], metrics_nb['Recall'], metrics_nb['Precision']],
        [metrics_ensemble_hard['F1 Score'], metrics_ensemble_hard['Accuracy'], metrics_ensemble_hard['Recall'], metrics_ensemble_hard['Precision']],
        [metrics_ensemble_soft['F1 Score'], metrics_ensemble_soft['Accuracy'], metrics_ensemble_soft['Recall'], metrics_ensemble_soft['Precision']]
    ]
    metrics_matrix = np.array(metrics_matrix)
    bar_width = 0.2
    index = np.arange(len(model_names))
    fig5, ax5 = plt.subplots(figsize=(14, 6))
    for i, metric in enumerate(metrics_names):
        ax5.bar(index + i * bar_width, metrics_matrix[:, i], bar_width, label=metric)
    ax5.set_xlabel('Models')
    ax5.set_ylabel('Scores')
    ax5.set_title('Model Evaluation Metrics')
    ax5.set_xticks(index + 1.5 * bar_width)
    ax5.set_xticklabels(model_names, rotation=15)
    ax5.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(fig5)

elif page == "GIS Disaster Map":
    st.header("🗺️ GIS Disaster-Prone Areas Map")
    st.write("Interactively explore disaster-prone areas by type, country, and frequency.")
    # Use the original (not label-encoded) data for map
    map_data = pd.read_csv('Prediction/natural_disasters_dataset.csv')
    map_data = map_data.dropna(subset=['Latitude', 'Longitude'])
    # --- Clean Latitude/Longitude columns ---
    def extract_float(val):
        if pd.isnull(val):
            return np.nan
        # Remove N/S/E/W and any non-numeric except . and -
        val = str(val).replace('N','').replace('S','').replace('E','').replace('W','')
        val = ''.join([c for c in val if c.isdigit() or c in ['.', '-'] or c == ' '])
        try:
            # If multiple numbers are concatenated, split and take the first valid float
            for part in val.split():
                try:
                    return float(part)
                except:
                    continue
            return float(val)
        except:
            return np.nan
    map_data['Latitude'] = map_data['Latitude'].apply(extract_float)
    map_data['Longitude'] = map_data['Longitude'].apply(extract_float)
    map_data = map_data.dropna(subset=['Latitude', 'Longitude'])
    # Color by disaster type
    disaster_types = map_data['Disaster Type'].unique()
    color_map = {d: [int(x) for x in plt.cm.tab20(i % 20)[:3]] for i, d in enumerate(disaster_types)}
    map_data['color'] = map_data['Disaster Type'].map(lambda d: color_map[d])
    # Cluster by location
    top_n = st.slider('Number of top-prone locations to show', 100, 1000, 300, 50)
    grouped_map = map_data.groupby(['Latitude', 'Longitude', 'Country', 'Disaster Type']).size().reset_index(name='Count')
    top_map = grouped_map.sort_values('Count', ascending=False).head(top_n)
    top_map['color'] = top_map['Disaster Type'].map(lambda d: color_map[d])
    # Compute radius for each point (normalize by max count)
    if not top_map['Count'].max() or top_map['Count'].max() == 0:
        top_map['radius'] = 10000
    else:
        top_map['radius'] = 10000 + 40000 * (top_map['Count'] / top_map['Count'].max())
    # GIS Map
    st.pydeck_chart(pdk.Deck(
        map_style='mapbox://styles/mapbox/dark-v10',
        initial_view_state=pdk.ViewState(
            latitude=top_map['Latitude'].mean(),
            longitude=top_map['Longitude'].mean(),
            zoom=2.5,
            pitch=30,
        ),
        layers=[
            pdk.Layer(
                'ScatterplotLayer',
                data=top_map,
                get_position='[Longitude, Latitude]',
                get_color='color',
                get_radius='radius',
                pickable=True,
                auto_highlight=True,
            ),
        ],
        tooltip={"text": "Country: {Country}\nDisaster: {Disaster Type}\nCount: {Count}"}
    ))
    # Legend
    st.markdown("**Legend:**")
    legend_cols = st.columns(4)
    for i, d in enumerate(disaster_types):
        color = color_map[d]
        legend_cols[i % 4].markdown(f'<div style="display:flex;align-items:center;"><div style="width:18px;height:18px;background:rgb{tuple(color)};margin-right:8px;"></div>{d}</div>', unsafe_allow_html=True)
    st.caption("Zoom, pan, and hover for details. Data and models are for demonstration purposes.")
