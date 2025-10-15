# NYC Taxi Database Manager
# This file handles all database operations for our taxi dashboard
# Written by: Gedeon Ntigibesh (Original Implementation)
# Purpose: Create, manage, and query our SQLite database with taxi trip data

# Import libraries for database operations
import sqlite3  # SQLite database library (built into Python)
import os      # Operating system functions (check if files exist)

# Define the name of our database file
DB_NAME = 'taxi_data.db'  # This file will store all our processed taxi data

def init_db():
    """
    This function sets up our database from scratch.
    It creates the main table and indexes to make queries fast.
    If tables already exist, it deletes them first (fresh start).
    """
    try:
        # Connect to our SQLite database (creates file if it doesn't exist)
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()  # Cursor lets us run SQL commands
        
        # Delete any existing tables to start fresh
        # This prevents errors if we run the setup multiple times
        c.execute('DROP TABLE IF EXISTS transactions')  # Old table (if exists)
        c.execute('DROP TABLE IF EXISTS taxi_trips')    # Main table (if exists)
        
        # Create our main table to store all taxi trip information
        # Each row will represent one taxi trip with all its details
        c.execute('''
            CREATE TABLE taxi_trips (
                id INTEGER PRIMARY KEY AUTOINCREMENT,    -- Unique ID for each record (auto-generated)
                trip_id TEXT UNIQUE NOT NULL,            -- Unique identifier for each trip
                vendor_id INTEGER NOT NULL,              -- Which taxi company (1, 2, etc.)
                pickup_datetime TEXT NOT NULL,           -- When the trip started
                dropoff_datetime TEXT NOT NULL,          -- When the trip ended
                passenger_count INTEGER NOT NULL,        -- How many passengers
                pickup_longitude REAL NOT NULL,          -- Where trip started (longitude coordinate)
                pickup_latitude REAL NOT NULL,           -- Where trip started (latitude coordinate)
                dropoff_longitude REAL NOT NULL,         -- Where trip ended (longitude coordinate)
                dropoff_latitude REAL NOT NULL,          -- Where trip ended (latitude coordinate)
                store_and_fwd_flag TEXT,                 -- Technical flag (not important for our analysis)
                trip_duration INTEGER NOT NULL,          -- How long the trip took (in seconds)
                distance_km REAL NOT NULL,               -- Distance traveled (in kilometers)
                speed_kmh REAL NOT NULL,                 -- Average speed (km per hour)
                time_of_day TEXT NOT NULL,               -- morning, afternoon, evening, or night
                trip_distance_category TEXT NOT NULL,    -- short, medium, or long trip
                hour INTEGER NOT NULL,                   -- Hour when trip started (0-23)
                day_of_week INTEGER NOT NULL,            -- Day of week (0=Monday, 6=Sunday)
                month INTEGER NOT NULL                   -- Month of the year (1-12)
            )
        ''')
        
        # Create indexes to make our queries run faster
        # Think of indexes like a phone book - they help find data quickly
        # Without indexes, the database has to look through every single row
        print("Creating database indexes for fast queries...")
        c.execute('CREATE INDEX idx_pickup_datetime ON taxi_trips(pickup_datetime)')      # For date filtering
        c.execute('CREATE INDEX idx_vendor_id ON taxi_trips(vendor_id)')                 # For vendor filtering
        c.execute('CREATE INDEX idx_time_of_day ON taxi_trips(time_of_day)')             # For time period charts
        c.execute('CREATE INDEX idx_distance_category ON taxi_trips(trip_distance_category)')  # For distance charts
        c.execute('CREATE INDEX idx_hour ON taxi_trips(hour)')                           # For hourly analysis
        c.execute('CREATE INDEX idx_day_of_week ON taxi_trips(day_of_week)')             # For weekly patterns
        c.execute('CREATE INDEX idx_month ON taxi_trips(month)')                         # For monthly trends
        c.execute('CREATE INDEX idx_duration ON taxi_trips(trip_duration)')             # For duration analysis
        c.execute('CREATE INDEX idx_distance ON taxi_trips(distance_km)')               # For distance analysis
        c.execute('CREATE INDEX idx_speed ON taxi_trips(speed_kmh)')                     # For speed analysis
        
        conn.commit()
        conn.close()
        print("Taxi database initialized successfully with proper indexing")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise

def store_taxi_data(data):
    """
    This function takes our clean taxi data and saves it to the database.
    It inserts each trip as a new row in our taxi_trips table.
    
    Args:
        data: List of cleaned trip dictionaries from process.py
    """
    try:
        # Connect to the database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        print(f"Saving {len(data):,} trips to database...")
        
        # Insert each trip into the database
        # We use a loop to process each trip one by one
        for item in data:
            # Use INSERT OR IGNORE to skip duplicates (if we run this twice)
            # The ? marks are placeholders that prevent SQL injection attacks
            c.execute('''
                INSERT OR IGNORE INTO taxi_trips (
                    trip_id, vendor_id, pickup_datetime, dropoff_datetime,
                    passenger_count, pickup_longitude, pickup_latitude,
                    dropoff_longitude, dropoff_latitude, store_and_fwd_flag,
                    trip_duration, distance_km, speed_kmh, time_of_day,
                    trip_distance_category, hour, day_of_week, month
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                # Map each piece of trip data to the correct database column
                item['trip_id'], item['vendor_id'], item['pickup_datetime'],
                item['dropoff_datetime'], item['passenger_count'],
                item['pickup_longitude'], item['pickup_latitude'],
                item['dropoff_longitude'], item['dropoff_latitude'],
                item['store_and_fwd_flag'], item['trip_duration'],
                item['distance_km'], item['speed_kmh'], item['time_of_day'],
                item['trip_distance_category'], item['hour'],
                item['day_of_week'], item['month']
            ))
        
        conn.commit()
        conn.close()
        print(f"Successfully stored {len(data)} taxi trips")
    except Exception as e:
        print(f"Error storing taxi data: {str(e)}")
        raise

def get_unique_vendors():
    """
    This function gets a list of all different taxi companies in our database.
    The web page uses this to populate the vendor dropdown menu.
    
    Returns:
        List of vendor IDs as strings (e.g., ['1', '2', '3'])
    """
    try:
        # First, check if our database file exists
        if not os.path.exists(DB_NAME):
            raise FileNotFoundError(f"Database file {DB_NAME} not found")
        
        # Connect to the database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Get all unique vendor IDs from our trips table
        # DISTINCT means no duplicates, ORDER BY sorts them
        vendors = c.execute('''
            SELECT DISTINCT vendor_id 
            FROM taxi_trips 
            ORDER BY vendor_id
        ''').fetchall()
        conn.close()  # Always close the connection when done
        
        # Convert the results to a list of strings
        # vendors comes back as [(1,), (2,), (3,)] so we extract the first item
        return [str(v[0]) for v in vendors]
        
    except Exception as e:
        # If something goes wrong, print error and return empty list
        print(f"Error getting unique vendors: {str(e)}")
        return []

def get_trip_stats():
    """
    This function calculates overall statistics about all trips in our database.
    It's used to show summary information on the dashboard.
    
    Returns:
        Dictionary with statistics like total trips, averages, date range, etc.
    """
    try:
        # Check if database exists
        if not os.path.exists(DB_NAME):
            return {}  # Return empty dict if no database
        
        # Connect to database
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        
        # Run a query to calculate various statistics about all trips
        stats = c.execute('''
            SELECT 
                COUNT(*) as total_trips,            -- How many trips total
                AVG(trip_duration) as avg_duration,  -- Average time per trip
                AVG(distance_km) as avg_distance,    -- Average distance per trip
                AVG(speed_kmh) as avg_speed,         -- Average speed across all trips
                MIN(pickup_datetime) as earliest_trip, -- Oldest trip in our data
                MAX(pickup_datetime) as latest_trip    -- Newest trip in our data
            FROM taxi_trips
        ''').fetchone()  # fetchone() gets just the first (and only) row
        
        conn.close()  # Close database connection
        
        # If we got results, format them nicely
        if stats:
            return {
                'total_trips': stats[0],  # Keep total as integer
                'avg_duration': round(stats[1], 2) if stats[1] else 0,  # Round to 2 decimal places
                'avg_distance': round(stats[2], 2) if stats[2] else 0,  # Round to 2 decimal places
                'avg_speed': round(stats[3], 2) if stats[3] else 0,     # Round to 2 decimal places
                'earliest_trip': stats[4],  # Keep as string (datetime)
                'latest_trip': stats[5]     # Keep as string (datetime)
            }
        
        # If no results, return empty dictionary
        return {}
        
    except Exception as e:
        # If anything goes wrong, print error and return empty dict
        print(f"Error getting trip stats: {str(e)}")
        return {}
