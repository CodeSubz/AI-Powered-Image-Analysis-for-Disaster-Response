import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
import joblib

# Load your data
data_path = r'd:\Harshith\RVCE\projects\IDP\Global_Disaster_Monitoring-main\Global_Disaster_Monitoring-main\Prone-Areas-Predictor\world_risk_index.csv'
df = pd.read_csv(data_path)

# Clean column names (remove spaces)
df.columns = df.columns.str.strip()

# Select features and target
features = ['WRI', 'Exposure', 'Vulnerability', 'Susceptibility', 
            'Lack of Coping Capabilities', 'Lack of Adaptive Capacities']
target = 'WRI Category'

# Create target if it doesn't exist
if target not in df.columns:
    # Create categories only for non-missing WRI values
    valid_wri = df['WRI'].dropna()
    bins = pd.cut(valid_wri, bins=5, labels=[1, 2, 3, 4, 5], retbins=True)[1]
    df[target] = pd.cut(df['WRI'], bins=bins, labels=[1, 2, 3, 4, 5])

# Remove rows with missing target values
df = df.dropna(subset=[target])

# Create pipeline with robust preprocessing
pipeline = Pipeline([
    ('imputer', SimpleImputer(strategy='median')),  # Fill missing feature values
    ('classifier', RandomForestClassifier(
        n_estimators=100, 
        random_state=42,
        n_jobs=-1  # Use all CPU cores for faster training
    ))
])

# Train the model
pipeline.fit(df[features], df[target])

# Save the model
joblib.dump(pipeline, 'prone_area_predictor.joblib')
print("Model trained and saved successfully!")

# Print model info
print("\nModel Information:")
print(f"- Features used: {', '.join(features)}")
print(f"- Target variable: {target}")
print(f"- Number of samples trained on: {len(df)}")
print(f"- Model type: Random Forest Classifier")