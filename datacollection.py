import pandas as pd
import requests
import datetime
import spacy
import ssl
from db_connect import get_database
import numpy as np
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
from pymongo import MongoClient
from pymongo.server_api import ServerApi

NEWSAPI_KEY = '55996ab5fc8f4c539351b9a1b1c18b0d'
NEWSAPI_ENDPOINT = 'https://newsapi.org/v2/everything'

disaster_keywords = ['earthquake', 'flood', 'tsunami', 'hurricane', 'wildfire', 'forestfire', 'tornado', 'cyclone', 'volcano', 'drought', 'landslide', 'storm', 'blizzard', 'avalanche', 'heatwave']

# Load the spaCy English language model
nlp = spacy.load("en_core_web_sm")

# Initialize geocoder
geolocator = Nominatim(user_agent="my_geocoder")

# List of locations to exclude
exclude_locations = ['politics', 'yahoo', 'sports', 'entertainment', 'cricket']

def fetch_live_data(keyword):
    # Calculate the date 2 days ago
    two_days_ago = datetime.datetime.now() - datetime.timedelta(days=2)
    
    params = {
        'apiKey': NEWSAPI_KEY,
        'q': keyword,
        'from': two_days_ago.strftime('%Y-%m-%d'),  # From 2 days ago
        'to': datetime.datetime.now().strftime('%Y-%m-%d'),  # To today
        'language': 'en',
    }

    response = requests.get(NEWSAPI_ENDPOINT, params=params)
    return response.json().get('articles', [])

def identify_disaster_event(title):
    if title is None:
        return 'Unknown'
    
    title_lower = title.lower()
    for keyword in disaster_keywords:
        if keyword.lower() in title_lower:
            return keyword  # Return the found keyword as the disaster event
    return 'Unknown'

def extract_location_ner(text):
    doc = nlp(text)
    location_ner_tags = [ent.text for ent in doc.ents if ent.label_ == 'GPE']
    return location_ner_tags

def get_coordinates(location):
    try:
        location_info = geolocator.geocode(location, timeout=10)  # Increase timeout if needed
        if location_info:
            return location_info.latitude, location_info.longitude
        else:
            return (np.nan, np.nan)
    except GeocoderTimedOut:
        print(f"Geocoding timed out for {location}")
        return (np.nan, np.nan)
    except Exception as e:
        print(f"Error geocoding {location}: {str(e)}")
        return (np.nan, np.nan)

if __name__ == "__main__":
    all_live_data = []
    for keyword in disaster_keywords:
        live_data = fetch_live_data(keyword)
        for article in live_data:
            published_at = article.get('publishedAt', datetime.datetime.now(datetime.timezone.utc))
            disaster_event = identify_disaster_event(article['title'])
            filtered_article = {
                'title': article['title'],
                'disaster_event': disaster_event,
                'timestamp': published_at,
                'source': article['source'],
                'url': article['url']
            }
            
            all_live_data.append(filtered_article)
    
    df = pd.DataFrame(all_live_data)

    df['disaster_event'] = df['disaster_event'].replace(to_replace="Unknown", value=np.nan)
    df.dropna(axis=0, inplace=True)
    df.drop_duplicates(subset='title', inplace=True)
    df['source'] = df['source'].apply(lambda x: x['name'])
    
    df['location_ner'] = df['title'].apply(extract_location_ner)
    
    df.dropna(axis=0, inplace=True)

    def fun(text):
        country, region, city = '', '', ''
        if len(text) == 1:
            country = text[0]
        elif len(text) == 2:
            country, region = text[0], text[1]
        elif len(text) == 3:
            country, region, city = text[0], text[1], text[2]
        return country, region, city

    a = df['location_ner'].apply(fun)

    df['Country'] = ''
    df['Region'] = ''
    df['City'] = ''

    df[['Country', 'Region', 'City']] = pd.DataFrame(a.tolist(), index=df.index, columns=['Country', 'Region', 'City'])

    def create_location(row):
        if row['City']:
            return row['City']
        elif row['Region']:
            return row['Region']
        else:
            return row['Country']

    df['Location'] = df.apply(create_location, axis=1)
    df = df.dropna(subset=['Location'])

    # Ensure 'Location' column is string type before using .str accessor
    df['Location'] = df['Location'].astype(str)

    # Filter out unwanted locations (e.g., political or social media articles)
    df = df[~df['Location'].str.lower().isin(exclude_locations)]
    df = df[~df['url'].str.lower().str.contains('politics|yahoo|sports|entertainment|cricket')]

    # Apply geocoding to get coordinates
    df['Coordinates'] = df['Location'].apply(get_coordinates)

    # Split the coordinates into separate latitude and longitude columns
    df[['Latitude', 'Longitude']] = pd.DataFrame(df['Coordinates'].tolist(), index=df.index)

    # Drop the Coordinates column
    df.drop('Coordinates', axis=1, inplace=True)

    # Drop rows with missing Latitude or Longitude
    df = df.dropna(subset=['Latitude', 'Longitude'])

    db = get_database()
    collection = db["disaster_info"]

    # Convert DataFrame to list of dictionaries
    data_list = df.to_dict(orient='records')

    # Insert the data list into the collection
    try:
        result = collection.insert_many(data_list)
        print("Documents inserted successfully. IDs:", result.inserted_ids)
    except Exception as e:
        print("An error occurred:", e)
