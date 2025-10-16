# NYC Taxi Trip Data Explorer - Urban Mobility Dashboard

## Group Members
Gedeon Ntigibeshya
Arnold Eloi Buyange Muvunyi

## Overview

This project is a fullstack application that analyzes real-world urban mobility patterns using the New York City Taxi Trip dataset. The application cleans and processes raw taxi trip data, stores it in a relational database, and presents interactive visualizations through a web dashboard to reveal insights about urban transportation patterns.

## Video Walkthrough

**[Summative-UrbanMobilityDataExplorer](https://youtu.be/hFbYPWcXMx0)**

*Note: Please replace the above link with your actual video walkthrough URL before submission.*

## Features

- **Data Processing Pipeline**: Custom data cleaning and validation with outlier detection
- **Database Management**: Normalized SQLite schema with proper indexing
- **Interactive Dashboard**: Real-time filtering and dynamic visualizations
- **Urban Mobility Insights**: Automated analysis of transportation patterns
- **Custom Algorithms**: Manual implementation of quicksort and haversine distance calculation

## Technology Stack

### Backend
- **Python 3.x**: Core processing language
- **Flask 3.0.0**: Web framework for API endpoints
- **SQLite**: Relational database for data storage

### Frontend  
- **HTML5/CSS3**: Structure and styling
- **JavaScript (ES6)**: Interactive functionality
- **Chart.js**: Data visualization library

### Data Processing
- **CSV Processing**: Native Python CSV handling
- **Custom Algorithms**: Manual quicksort and geospatial calculations

## Project Structure

```
dashboard-summative/
├── process.py          # Data cleaning and processing pipeline
├── db.py              # Database schema and operations
├── server.py          # Flask web server and API endpoints
├── index.html         # Main dashboard interface
├── script.js          # Frontend JavaScript functionality
├── style.css          # Dashboard styling
├── requirements.txt   # Python dependencies
├── train.csv          # NYC taxi dataset (not included in repo)
├── taxi_data.db       # SQLite database (generated)
└── README.md          # Project documentation
```

## Setup Instructions

### Prerequisites

- Python 3.7 or higher
- pip package manager
- Modern web browser (Chrome, Firefox, Safari, Edge)

### Installation

1. **Clone the repository or extract the project files**
   ```bash
   # Navigate to the project directory
   cd Summative-UrbanMobilityDataExplorer
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Obtain the NYC Taxi Dataset**
   - Download [`train.csv`](https://www.kaggle.com/competitions/nyc-taxi-trip-duration/data?select=train.zip) from the official NYC Taxi Trip dataset
   - Place the file in the project root directory
   - File should be named exactly `train.csv`

4. **Process the dataset**
   ```bash
   python process.py
   ```
   This will:
   - Clean and validate the raw taxi data
   - Apply outlier detection using custom quicksort algorithm
   - Create derived features (speed, distance categories, time periods)
   - Store processed data in SQLite database
   - Print processing statistics and exclusion reasons

5. **Start the web server**
   ```bash
   python server.py
   ```

6. **Access the dashboard**
   - Open your web browser
   - Navigate to `http://localhost:5000`
   - The dashboard will load with interactive visualizations

### Alternative Setup (Development Mode)

For development with auto-reload:
```bash
set FLASK_ENV=development
set FLASK_DEBUG=1
python server.py
```

## Usage Guide

### Dashboard Features

1. **Overview Cards**: Display total trips, average duration/distance, and dataset time period
2. **Interactive Filters**: 
   - Time of day (Morning, Afternoon, Evening, Night)
   - Vendor ID selection
   - Distance categories (Short <2km, Medium 2-10km, Long >10km)
   - Trip limit adjustment (100-10,000 trips)

3. **Visualizations**:
   - **Time Distribution Chart**: Bar chart showing trip patterns by time of day
   - **Distance Category Chart**: Doughnut chart displaying trip distribution by distance
   - **Recent Trips Table**: Detailed view of individual trip records

4. **Automated Insights**: Dynamic analysis showing:
   - Peak activity periods
   - Distance distribution patterns  
   - Traffic speed analysis

### API Endpoints

- `GET /`: Main dashboard interface
- `GET /data`: Trip data with filtering parameters
- `GET /stats`: Overall dataset statistics
- `GET /<path>`: Static file serving

### Filter Parameters

| Parameter | Description | Values |
|-----------|-------------|--------|
| time_of_day | Time period filter | all, morning, afternoon, evening, night |
| vendor_id | Taxi company filter | all, 1, 2 (specific vendor IDs) |
| distance_category | Trip length filter | all, short, medium, long |
| limit | Maximum trips returned | 100-10000 |

## Data Processing Details

### Custom Algorithm Implementation

The project implements a **custom quicksort algorithm** for outlier detection:

```python
def quicksort_durations(arr, low, high):
    """Custom quicksort implementation for duration sorting"""
    if low < high:
        pi = partition_durations(arr, low, high)
        quicksort_durations(arr, low, pi - 1)
        quicksort_durations(arr, pi + 1, high)
```

**Time Complexity**: O(n log n) average case, O(n²) worst case
**Space Complexity**: O(log n) for recursion stack

### Data Cleaning Pipeline

1. **Initial Validation**: Check for required fields and basic data types
2. **Coordinate Validation**: Verify NYC area boundaries (40.0-41.0°N, -75.0 to -73.0°W)
3. **Temporal Validation**: Parse multiple datetime formats, validate trip sequence
4. **Outlier Detection**: Use IQR method with custom quicksort for duration bounds
5. **Feature Engineering**: 
   - Haversine distance calculation (custom implementation)
   - Speed computation (distance/time)
   - Time categorization (morning/afternoon/evening/night)
   - Distance categorization (short/medium/long)

### Database Schema

```sql
CREATE TABLE taxi_trips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trip_id TEXT UNIQUE NOT NULL,
    vendor_id INTEGER NOT NULL,
    pickup_datetime TEXT NOT NULL,
    dropoff_datetime TEXT NOT NULL,
    passenger_count INTEGER NOT NULL,
    pickup_longitude REAL NOT NULL,
    pickup_latitude REAL NOT NULL,
    dropoff_longitude REAL NOT NULL,
    dropoff_latitude REAL NOT NULL,
    store_and_fwd_flag TEXT,
    trip_duration INTEGER NOT NULL,
    distance_km REAL NOT NULL,
    speed_kmh REAL NOT NULL,
    time_of_day TEXT NOT NULL,
    trip_distance_category TEXT NOT NULL,
    hour INTEGER NOT NULL,
    day_of_week INTEGER NOT NULL,
    month INTEGER NOT NULL
);
```

## Performance Optimizations

- **Batch Processing**: Data processed in 5,000-record chunks
- **Database Indexing**: Optimized indexes on commonly queried fields
- **Sampling for Outliers**: Uses statistical sampling for large datasets
- **Frontend Debouncing**: Prevents excessive API calls during filtering
- **Limited Dataset**: Processing limited to 10,000 records for demo performance

## Troubleshooting

### Common Issues

1. **"Database file not found"**
   - Run `python process.py` first to create and populate database

2. **"No data loaded. Please check if train.csv exists"**
   - Ensure `train.csv` is in the project root directory
   - Verify file permissions and content format

3. **Server won't start**
   - Check if port 5000 is available
   - Install dependencies with `pip install -r requirements.txt`

4. **Charts not loading**
   - Ensure internet connection (Chart.js loads from CDN)
   - Check browser console for JavaScript errors

5. **Slow performance**
   - Reduce the trip limit in the dashboard
   - Consider processing a smaller subset of data

### Data Quality Notes

- The system excludes trips with unrealistic durations, speeds, or coordinates
- Approximately 5-10% of raw records may be excluded during cleaning
- Processing logs show detailed exclusion reasons for transparency

## System Requirements

- **Minimum RAM**: 2GB (4GB recommended for larger datasets)
- **Storage**: 500MB free space for database and processing
- **CPU**: Any modern processor (multi-core recommended for large datasets)
- **Network**: Internet connection required for Chart.js CDN

## Contributing

For development and debugging:

1. Enable Flask debug mode: `set FLASK_DEBUG=1`
2. Check database contents: `python -c "import sqlite3; conn = sqlite3.connect('taxi_data.db'); print(conn.execute('SELECT COUNT(*) FROM taxi_trips').fetchone()[0])"`
3. View processing logs in console output
4. Use browser developer tools for frontend debugging

## License

This project is for educational purposes as part of a university assignment.

---

**Last Updated**: October 2025
**Assignment**: Urban Mobility Data Explorer Summative Assessment