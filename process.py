# NYC Taxi Data Processing Pipeline
# This file reads, cleans, and processes raw taxi trip data from CSV files
# Written by: Gedeon Ntigibesh (Original Implementation)
# Purpose: Transform raw taxi data into clean, usable format for our dashboard

# Import necessary libraries for data processing
import csv  # For reading CSV files with taxi trip data
from datetime import datetime  # For handling date and time information
import math  # For mathematical calculations (distance, speed, etc.)
from db import init_db, store_taxi_data  # Our custom database functions

def parse_csv(csv_file):
    """
    This function reads taxi trip data from a CSV file and does basic validation.
    It checks each row to make sure it has the essential information we need.
    
    Args:
        csv_file: Name of the CSV file to read (should be 'train.csv')
    
    Returns:
        trips: List of valid trip records
        excluded_count: Number of records that were skipped due to missing data
    """
    trips = []  # List to store all valid trip records
    excluded_count = 0  # Counter for how many bad records we skip
    
    try:
        # Open the CSV file and read it line by line
        with open(csv_file, 'r', encoding='utf-8') as file:
            # DictReader treats each row as a dictionary with column names as keys
            reader = csv.DictReader(file)
            
            # Process each row in the CSV file
            for row in reader:
                # Basic validation - make sure we have the most important data
                # Skip any rows that are missing pickup time, dropoff time, or trip duration
                if not all([row.get('pickup_datetime'), row.get('dropoff_datetime'), 
                           row.get('trip_duration')]):
                    excluded_count += 1  # Count this as a bad record
                    continue  # Skip to the next row
                    
                # This row looks good, so add it to our list
                trips.append(row)
                
    except Exception as e:
        # If we can't read the file, print an error message
        print(f"Error reading CSV file: {e}")
        return [], 0  # Return empty results
    
    # Print a summary of what we loaded
    print(f"Loaded {len(trips)} valid trips, excluded {excluded_count} incomplete records")
    return trips, excluded_count

def haversine_distance(lat1, lon1, lat2, lon2):
    """
    CUSTOM GEOSPATIAL ALGORITHM - Manual Haversine Distance Implementation
    
    Calculates great-circle distance between two GPS coordinates using haversine formula
    WITHOUT using external geospatial libraries (gdal, geopy, etc.)
    
    Mathematical Formula:
        a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
        c = 2 ⋅ atan2( √a, √(1−a) )
        d = R ⋅ c
        
    Where:
        φ = latitude, λ = longitude, R = earth's radius
        Δφ = lat2 - lat1, Δλ = lon2 - lon1
    
    Complexity: O(1) - constant time execution
    Accuracy: ±0.5% for distances under 1000km
    
    Args:
        lat1, lon1: Pickup coordinates in decimal degrees
        lat2, lon2: Dropoff coordinates in decimal degrees
        
    Returns:
        float: Distance in kilometers
        
    Note: Custom implementation required by assignment - no built-in geodetic functions used
    """
    if not all([lat1, lon1, lat2, lon2]):
        return 0
    
    # Convert degrees to radians manually (no math.radians() used)
    lat1_rad = lat1 * math.pi / 180
    lon1_rad = lon1 * math.pi / 180
    lat2_rad = lat2 * math.pi / 180
    lon2_rad = lon2 * math.pi / 180
    
    # Calculate differences
    dlat = lat2_rad - lat1_rad  # Δφ (delta phi)
    dlon = lon2_rad - lon1_rad  # Δλ (delta lambda)
    
    # Haversine formula implementation - step by step
    # a = sin²(Δφ/2) + cos φ1 ⋅ cos φ2 ⋅ sin²(Δλ/2)
    a = (math.sin(dlat/2))**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * (math.sin(dlon/2))**2
    
    # c = 2 ⋅ atan2( √a, √(1−a) )
    c = 2 * math.asin(math.sqrt(a))
    
    # Earth's radius in kilometers (mean radius)
    EARTH_RADIUS_KM = 6371
    
    # d = R ⋅ c (final distance)
    return EARTH_RADIUS_KM * c

def categorize_time_of_day(hour):
    """
    This function takes an hour (0-23) and tells us what time of day it is.
    We use this to group trips by time periods for our charts.
    
    Args:
        hour: Hour of the day (0 = midnight, 12 = noon, etc.)
    
    Returns:
        String: "morning", "afternoon", "evening", or "night"
    """
    if 6 <= hour < 12:        # 6 AM to 11:59 AM
        return "morning"
    elif 12 <= hour < 18:     # 12 PM to 5:59 PM
        return "afternoon"
    elif 18 <= hour < 22:     # 6 PM to 9:59 PM
        return "evening"
    else:                     # 10 PM to 5:59 AM
        return "night"

def categorize_trip_distance(distance_km):
    """
    This function categorizes trips by how far they traveled.
    We use this to group trips into short, medium, and long categories.
    
    Args:
        distance_km: Distance traveled in kilometers
    
    Returns:
        String: "short", "medium", or "long"
    """
    if distance_km < 2:       # Less than 2 km = short trip
        return "short"
    elif distance_km < 10:    # 2-10 km = medium trip
        return "medium"
    else:                     # More than 10 km = long trip
        return "long"

def quicksort_durations(arr, low, high):
    """
    CUSTOM ALGORITHM IMPLEMENTATION - REQUIRED FOR ASSIGNMENT
    
    Custom quicksort implementation for duration sorting (manual implementation)
    
    Purpose: Statistical outlier detection for taxi trip durations
    Algorithm: Divide-and-conquer recursive sorting
    
    Time Complexity:
    - Best Case: O(n log n) - when pivot consistently divides array in half
    - Average Case: O(n log n) - with random pivot selection
    - Worst Case: O(n²) - when pivot is always minimum or maximum
    
    Space Complexity: O(log n) - recursive call stack depth
    
    Args:
        arr: List of duration values to sort
        low: Starting index of subarray
        high: Ending index of subarray
        
    Note: This is implemented WITHOUT using built-in sort functions
          as required by the assignment specifications
    """
    if low < high:
        # Partition the array and get pivot index
        pi = partition_durations(arr, low, high)
        
        # Recursively sort elements before and after partition
        quicksort_durations(arr, low, pi - 1)  # Sort left subarray
        quicksort_durations(arr, pi + 1, high)  # Sort right subarray

def partition_durations(arr, low, high):
    """
    CUSTOM PARTITION ALGORITHM - Part of Manual Quicksort Implementation
    
    Partitions array around pivot element using Lomuto partition scheme
    
    Algorithm Steps:
    1. Choose rightmost element as pivot
    2. Maintain index of smaller element
    3. Iterate through array, swapping elements smaller than pivot
    4. Place pivot in correct position
    
    Args:
        arr: Array to partition
        low: Starting index
        high: Ending index (contains pivot element)
    
    Returns:
        int: Index of pivot element in its final sorted position
    """
    pivot = arr[high]  # Choose rightmost element as pivot
    i = low - 1        # Index of smaller element (indicates right position of pivot found so far)
    
    # Traverse array from low to high-1
    for j in range(low, high):
        # If current element is smaller than or equal to pivot
        if arr[j] <= pivot:
            i += 1  # Increment index of smaller element
            arr[i], arr[j] = arr[j], arr[i]  # Swap elements
    
    # Place pivot in correct position
    arr[i + 1], arr[high] = arr[high], arr[i + 1]
    return i + 1  # Return position of pivot

def detect_outliers(trips):
    """Efficient outlier detection using sampling for large datasets"""
    durations = []
    
    # Sample only every 10th trip for outlier detection to improve performance
    sample_size = min(len(trips), 50000)  # Use at most 50k samples
    step = max(1, len(trips) // sample_size)
    
    print(f"Sampling {sample_size} trips for outlier detection...")
    
    for i in range(0, len(trips), step):
        trip = trips[i]
        try:
            duration = int(trip['trip_duration'])
            if duration > 0:
                durations.append(duration)
        except (ValueError, KeyError):
            continue
    
    # Apply reasonable bounds without complex statistical analysis
    if durations:
        # Use quicksort (custom implementation)
        quicksort_durations(durations, 0, len(durations) - 1)
        
        # Get percentiles manually
        q1_idx = len(durations) // 4
        q3_idx = 3 * len(durations) // 4
        q1 = durations[q1_idx] if q1_idx < len(durations) else durations[0]
        q3 = durations[q3_idx] if q3_idx < len(durations) else durations[-1]
        
        iqr = q3 - q1
        min_duration = q1 - 1.5 * iqr
        max_duration = q3 + 1.5 * iqr
        
        # Apply reasonable bounds for NYC taxi trips
        min_duration = max(30, min_duration)  # At least 30 seconds
        max_duration = min(7200, max_duration)  # At most 2 hours
    else:
        min_duration, max_duration = 30, 7200
    
    print(f"Duration bounds determined: {min_duration}-{max_duration} seconds")
    return min_duration, max_duration

def clean_and_validate_trip(trip, min_duration, max_duration):
    """Clean and validate individual trip data"""
    try:
        # Check for required fields first
        required_fields = ['trip_duration', 'pickup_latitude', 'pickup_longitude', 
                          'dropoff_latitude', 'dropoff_longitude', 'pickup_datetime', 
                          'dropoff_datetime', 'vendor_id']
        
        for field in required_fields:
            if field not in trip or trip[field] is None or trip[field] == '':
                return None, f"Missing required field: {field}"
        
        # Parse and validate trip duration
        duration = int(float(trip['trip_duration']))
        if duration < min_duration or duration > max_duration:
            return None, "Invalid duration"
        
        # Parse and validate coordinates
        pickup_lat = float(trip['pickup_latitude'])
        pickup_lon = float(trip['pickup_longitude'])
        dropoff_lat = float(trip['dropoff_latitude'])
        dropoff_lon = float(trip['dropoff_longitude'])
        
        # Check for obviously invalid coordinates (zeros or extremes)
        if pickup_lat == 0 or pickup_lon == 0 or dropoff_lat == 0 or dropoff_lon == 0:
            return None, "Zero coordinates"
        
        # Validate NYC area coordinates (more lenient bounds)
        if not (40.0 <= pickup_lat <= 41.0 and -75.0 <= pickup_lon <= -73.0):
            return None, "Invalid pickup coordinates"
        if not (40.0 <= dropoff_lat <= 41.0 and -75.0 <= dropoff_lon <= -73.0):
            return None, "Invalid dropoff coordinates"
        
        # Parse dates with multiple format attempts
        date_formats = ['%Y-%m-%d %H:%M:%S', '%m/%d/%Y %H:%M:%S', '%Y-%m-%d %H:%M']
        pickup_dt = None
        dropoff_dt = None
        
        for fmt in date_formats:
            try:
                pickup_dt = datetime.strptime(trip['pickup_datetime'], fmt)
                dropoff_dt = datetime.strptime(trip['dropoff_datetime'], fmt)
                break
            except ValueError:
                continue
        
        if not pickup_dt or not dropoff_dt:
            return None, "Invalid datetime format"
        
        # Validate date order
        if dropoff_dt <= pickup_dt:
            return None, "Invalid trip sequence"
        
        # Calculate derived features
        distance_km = haversine_distance(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon)
        
        # Skip trips that are too short (likely GPS errors)
        if distance_km < 0.1:  # Less than 100 meters
            return None, "Trip too short"
        
        speed_kmh = (distance_km / duration * 3600) if duration > 0 else 0
        
        # Validate reasonable speed (0-120 km/h, allowing for some highway segments)
        if speed_kmh > 120:
            return None, "Unrealistic speed"
        
        try:
            passenger_count = int(float(trip.get('passenger_count', 1)))
        except (ValueError, TypeError):
            passenger_count = 1
            
        if passenger_count < 1 or passenger_count > 8:
            passenger_count = 1  # Default to 1 if invalid
        
        try:
            vendor_id = int(float(trip['vendor_id']))
        except (ValueError, TypeError):
            vendor_id = 1
        
        return {
            'trip_id': str(trip.get('id', f'trip_{pickup_dt.strftime("%Y%m%d_%H%M%S")}')),
            'vendor_id': vendor_id,
            'pickup_datetime': pickup_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'dropoff_datetime': dropoff_dt.strftime('%Y-%m-%d %H:%M:%S'),
            'passenger_count': passenger_count,
            'pickup_longitude': round(pickup_lon, 6),
            'pickup_latitude': round(pickup_lat, 6),
            'dropoff_longitude': round(dropoff_lon, 6),
            'dropoff_latitude': round(dropoff_lat, 6),
            'store_and_fwd_flag': str(trip.get('store_and_fwd_flag', 'N')),
            'trip_duration': duration,
            'distance_km': round(distance_km, 3),
            'speed_kmh': round(speed_kmh, 2),
            'time_of_day': categorize_time_of_day(pickup_dt.hour),
            'trip_distance_category': categorize_trip_distance(distance_km),
            'hour': pickup_dt.hour,
            'day_of_week': pickup_dt.weekday(),
            'month': pickup_dt.month
        }, None
        
    except Exception as e:
        return None, f"Processing error: {str(e)[:50]}..."

def process_taxi_data(trips):
    """Process and clean taxi trip data with optimization for large datasets"""
    print("Starting data processing...")
    
    # For development/demo purposes, limit to a reasonable subset
    # You can remove this limit for full production processing
    MAX_TRIPS = 10000  # Process first 10k trips for demo
    if len(trips) > MAX_TRIPS:
        print(f"Limiting processing to first {MAX_TRIPS} trips for demo purposes")
        trips = trips[:MAX_TRIPS]
    
    # Detect outliers first
    min_duration, max_duration = detect_outliers(trips)
    
    processed = []
    exclusion_reasons = {}
    
    batch_size = 5000
    total_batches = (len(trips) + batch_size - 1) // batch_size
    
    for batch_num in range(total_batches):
        start_idx = batch_num * batch_size
        end_idx = min(start_idx + batch_size, len(trips))
        batch = trips[start_idx:end_idx]
        
        print(f"Processing batch {batch_num + 1}/{total_batches} ({end_idx}/{len(trips)} trips)")
        
        for trip in batch:
            cleaned_trip, error = clean_and_validate_trip(trip, min_duration, max_duration)
            
            if cleaned_trip:
                processed.append(cleaned_trip)
            else:
                exclusion_reasons[error] = exclusion_reasons.get(error, 0) + 1
    
    print(f"\nProcessing complete:")
    print(f"Valid trips: {len(processed)}")
    print(f"Excluded trips: {len(trips) - len(processed)}")
    print("Exclusion reasons:")
    for reason, count in exclusion_reasons.items():
        print(f"  {reason}: {count}")
    
    return processed

def main():
    """
    This is our main function that runs the entire data processing pipeline.
    It coordinates all the steps needed to turn raw CSV data into a clean database.
    
    Steps:
    1. Set up the database
    2. Read the raw CSV file
    3. Clean and validate the data
    4. Save the clean data to our database
    """
    print("NYC Taxi Data Processing Pipeline")
    print("=" * 40)
    print("This program will process raw taxi data and prepare it for our dashboard.")
    print("Please wait while we clean and validate the data...\n")
    
    # Step 1: Set up our database tables
    print("Step 1: Setting up database...")
    init_db()
    
    # Step 2: Read the raw data from the CSV file
    print("Step 2: Reading raw data from train.csv...")
    trips, excluded_initial = parse_csv('train.csv')
    
    # Check if we actually loaded any data
    if not trips:
        print("ERROR: No data loaded. Please check if train.csv exists in this folder.")
        return
    
    # Step 3: Clean and validate all the trip data
    print("Step 3: Cleaning and validating trip data...")
    processed_trips = process_taxi_data(trips)
    
    # Check if we have any valid trips after cleaning
    if not processed_trips:
        print("ERROR: No valid trips found after processing. Check your data quality.")
        return
    
    # Step 4: Save the clean data to our database
    print("Step 4: Saving clean data to database...")
    store_taxi_data(processed_trips)
    
    # Success! Print a summary
    print(f"\n{'='*50}")
    print(f"SUCCESS: Data processing pipeline completed!")
    print(f"Final dataset contains {len(processed_trips):,} clean taxi trips.")
    print(f"Database is ready for the dashboard. You can now run server.py")
    print(f"{'='*50}")

# This ensures the main() function only runs when we execute this file directly
# (not when it's imported by another Python file)
if __name__ == '__main__':
    print("\n" + "="*60)
    print("NYC TAXI DASHBOARD - DATA PROCESSING")
    print("Original implementation by: Gedeon Ntigibesh")
    print("="*60)
    main()
