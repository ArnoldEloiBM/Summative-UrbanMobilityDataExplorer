# NYC Taxi Dashboard - Web Server
# This file creates a Flask web server to serve our taxi data dashboard
# Written by: Gedeon Ntigibesh (Original Implementation)
# Purpose: Provide API endpoints for taxi trip data visualization

# Import necessary libraries
from flask import Flask, jsonify, request, send_from_directory  # Web framework for creating our server
import sqlite3  # Database connection library
from db import get_unique_vendors, get_trip_stats  # Our custom database functions
import traceback  # For detailed error messages
import os  # For file system operations

# Create our Flask web application
app = Flask(__name__)
# Define where our database file is located
DB_PATH = 'taxi_data.db'

# Function to connect to our SQLite database
def get_db():
    """
    This function creates a connection to our taxi database.
    It checks if the database file exists and connects to it.
    Returns: A database connection object that we can use to run queries
    """
    try:
        # Check if the database file actually exists on our computer
        if not os.path.exists(DB_PATH):
            raise FileNotFoundError(f"Database file {DB_PATH} not found. Please run process.py first.")
        
        # Create connection to the SQLite database
        conn = sqlite3.connect(DB_PATH)
        # This makes query results act like dictionaries (easier to work with)
        conn.row_factory = sqlite3.Row
        return conn
    except Exception as e:
        # If something goes wrong, print the error and stop the program
        print(f"Error connecting to database: {str(e)}")
        raise

# Route handlers - these tell our server what to do when users visit different web pages

@app.route('/')
def index():
    """
    This handles the main page of our website (when someone visits http://localhost:5000/)
    It sends them our main HTML file (index.html)
    """
    return send_from_directory('.', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    """
    This handles requests for other files like CSS, JavaScript, images, etc.
    For example: style.css, script.js, or any other files in our project folder
    """
    return send_from_directory('.', path)

@app.route('/data')
def get_data():
    """
    This is our main API endpoint that provides taxi trip data to the web page.
    It handles filtering by time of day, vendor, and distance categories.
    The JavaScript on our webpage calls this to get data for charts and tables.
    """
    try:
        # Get filter parameters from the web page request
        # These come from the dropdown menus on our dashboard
        time_of_day = request.args.get('time_of_day', 'all')  # morning, afternoon, evening, night, or all
        vendor_id = request.args.get('vendor_id', 'all')      # specific taxi company ID or all
        distance_category = request.args.get('distance_category', 'all')  # short, medium, long, or all
        limit = int(request.args.get('limit', '1000'))        # how many records to show (default 1000)
        
        # Print what filters are being used (helpful for debugging)
        print(f"Processing request - Time: {time_of_day}, Vendor: {vendor_id}, Distance: {distance_category}")
        
        # Connect to our database
        conn = get_db()
        if not conn:
            raise Exception("Could not connect to database")

        # Create our main SQL query to get taxi trip data
        # This is a complex query that:
        # 1. Gets all the trip information we need
        # 2. Calculates statistics like averages and totals
        # 3. Allows us to filter the data based on user selections
        query = """
            WITH filtered_trips AS (
                SELECT 
                    trip_id,                    -- Unique ID for each trip
                    vendor_id,                  -- Which taxi company
                    pickup_datetime,            -- When the trip started
                    dropoff_datetime,           -- When the trip ended
                    passenger_count,            -- How many passengers
                    pickup_longitude,           -- Where trip started (longitude)
                    pickup_latitude,            -- Where trip started (latitude)
                    dropoff_longitude,          -- Where trip ended (longitude)
                    dropoff_latitude,           -- Where trip ended (latitude)
                    trip_duration,              -- How long the trip took (minutes)
                    distance_km,                -- Distance traveled (kilometers)
                    speed_kmh,                  -- Average speed (km per hour)
                    time_of_day,                -- morning, afternoon, evening, or night
                    trip_distance_category,     -- short, medium, or long trip
                    hour,                       -- Hour of day (0-23)
                    day_of_week,                -- Day of week (Monday=0, Sunday=6)
                    month,                      -- Month of year (1-12)
                    COUNT(*) OVER() as total_count,      -- Total trips matching our filters
                    AVG(trip_duration) OVER() as avg_duration,  -- Average trip time
                    AVG(distance_km) OVER() as avg_distance     -- Average trip distance
                FROM taxi_trips 
                WHERE 1=1                   -- Always true, makes it easy to add more filters
        """
        # List to store our filter values (prevents SQL injection attacks)
        params = []

        # Add filters to our query based on what the user selected
        # Only add filters if user didn't select "all" (which means no filter)
        
        if time_of_day != 'all':
            query += " AND time_of_day = ?"  # Filter by time of day (morning, afternoon, etc.)
            params.append(time_of_day)
        
        if vendor_id != 'all':
            query += " AND vendor_id = ?"     # Filter by specific taxi company
            params.append(int(vendor_id))
            
        if distance_category != 'all':
            query += " AND trip_distance_category = ?"  # Filter by trip distance (short, medium, long)
            params.append(distance_category)

        query += f"""
            )
            SELECT * FROM filtered_trips
            ORDER BY pickup_datetime DESC
            LIMIT ?
        """
        params.append(limit)

        print(f"Executing query with {len(params)} params")
        
        try:
            trips = conn.execute(query, params).fetchall()
            trips = [dict(trip) for trip in trips]
        except sqlite3.Error as e:
            print(f"Database error: {str(e)}")
            raise

        # Get data for our "Time of Day" chart (pie chart showing trip distribution)
        # This shows how many trips happen during morning, afternoon, evening, night
        time_chart_query = """
            SELECT 
                time_of_day,                    -- morning, afternoon, evening, night
                COUNT(*) as count,              -- how many trips in each time period
                AVG(trip_duration) as avg_duration,  -- average trip duration for each time
                AVG(distance_km) as avg_distance     -- average distance for each time
            FROM taxi_trips
            WHERE 1=1                           -- base condition for adding filters
        """
        chart_params = []  # parameters for the chart query
        
        if vendor_id != 'all':
            time_chart_query += " AND vendor_id = ?"
            chart_params.append(int(vendor_id))
            
        if distance_category != 'all':
            time_chart_query += " AND trip_distance_category = ?"
            chart_params.append(distance_category)
        
        time_chart_query += """
            GROUP BY time_of_day 
            ORDER BY 
                CASE time_of_day 
                    WHEN 'morning' THEN 1
                    WHEN 'afternoon' THEN 2 
                    WHEN 'evening' THEN 3
                    WHEN 'night' THEN 4
                END
        """
        
        try:
            time_chart = conn.execute(time_chart_query, chart_params).fetchall()
        except sqlite3.Error as e:
            print(f"Chart query error: {str(e)}")
            raise

        # Get data for our "Distance Category" chart (bar chart showing trip types)
        # This shows how many short, medium, and long trips we have
        distance_chart_query = """
            SELECT 
                trip_distance_category,         -- short, medium, or long trips
                COUNT(*) as count,              -- how many trips in each category
                AVG(speed_kmh) as avg_speed     -- average speed for each trip type
            FROM taxi_trips
            WHERE 1=1                           -- base condition for filters
        """
        
        if time_of_day != 'all':
            distance_chart_query += " AND time_of_day = ?"
        if vendor_id != 'all':
            distance_chart_query += " AND vendor_id = ?"
        
        distance_chart_query += """
            GROUP BY trip_distance_category 
            ORDER BY 
                CASE trip_distance_category 
                    WHEN 'short' THEN 1
                    WHEN 'medium' THEN 2 
                    WHEN 'long' THEN 3
                END
        """
        
        distance_chart_params = []
        if time_of_day != 'all':
            distance_chart_params.append(time_of_day)
        if vendor_id != 'all':
            distance_chart_params.append(int(vendor_id))
        
        try:
            distance_chart = conn.execute(distance_chart_query, distance_chart_params).fetchall()
        except sqlite3.Error as e:
            print(f"Distance chart query error: {str(e)}")
            raise

        conn.close()

        # Get unique vendors
        try:
            vendors = get_unique_vendors()
        except Exception as e:
            print(f"Error getting unique vendors: {str(e)}")
            vendors = []

        # Calculate summary statistics to show on the dashboard
        total_count = trips[0]['total_count'] if trips else 0  # Total number of trips found
        avg_duration = round(trips[0]['avg_duration'], 2) if trips and trips[0]['avg_duration'] else 0  # Average trip time
        avg_distance = round(trips[0]['avg_distance'], 2) if trips and trips[0]['avg_distance'] else 0  # Average trip distance

        # Build the response data that gets sent back to our web page
        # This contains everything the JavaScript needs to update the charts and table
        response_data = {
            'trips': trips,  # Individual trip records for the data table
            'time_chart_data': {  # Data for the time-of-day pie chart
                'labels': [row['time_of_day'] for row in time_chart],  # morning, afternoon, etc.
                'values': [row['count'] for row in time_chart],        # number of trips
                'avg_duration': [round(row['avg_duration'], 2) for row in time_chart],  # average time
                'avg_distance': [round(row['avg_distance'], 2) for row in time_chart]   # average distance
            },
            'distance_chart_data': {  # Data for the distance category bar chart
                'labels': [row['trip_distance_category'] for row in distance_chart],  # short, medium, long
                'values': [row['count'] for row in distance_chart],                    # number of trips
                'avg_speed': [round(row['avg_speed'], 2) for row in distance_chart]    # average speed
            },
            'total_count': total_count,      # Summary statistic: total trips
            'avg_duration': avg_duration,    # Summary statistic: average duration
            'avg_distance': avg_distance,    # Summary statistic: average distance
            'vendors': vendors               # List of taxi companies for the dropdown
        }

        print(f"Successfully processed request. Found {total_count} trips.")
        return jsonify(response_data)

    except Exception as e:
        error_msg = f"Error in get_data: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        return jsonify({'error': str(e), 'details': error_msg}), 500

@app.route('/stats')
def get_stats():
    """
    This endpoint provides overall statistics about our entire taxi dataset.
    It's called when the page first loads to show general information.
    Returns things like total number of trips, date ranges, etc.
    """
    try:
        # Get statistics from our database helper function
        stats = get_trip_stats()
        return jsonify(stats)  # Send the stats as JSON to the web page
    except Exception as e:
        # If something goes wrong, send an error message
        print(f"Error getting stats: {str(e)}")
        return jsonify({'error': str(e)}), 500

# This is the main part that starts our web server
# Only runs if we execute this file directly (not if it's imported by another file)
if __name__ == '__main__':
    print("\n=== NYC Taxi Dashboard Server ===")
    print("Starting server... Visit http://localhost:5000 to view the dashboard")
    print("Press Ctrl+C to stop the server")
    print("=====================================\n")
    # Start the Flask web server in debug mode (shows detailed error messages)
    app.run(debug=True)
