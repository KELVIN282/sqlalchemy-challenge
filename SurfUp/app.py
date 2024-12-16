# Import the dependencies.
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
import datetime as dt

#################################################
# Database Setup
#################################################
# Create the engine to connect to the SQLite database
engine = create_engine("sqlite:///hawaii.sqlite")  # Update with your database file path

# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
Base.prepare(autoload_with=engine)

# Save references to each table
Measurement = Base.classes.measurement
Station = Base.classes.station

# Create our session (link) from Python to the DB
session = Session(engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################

# Root route to welcome users and provide available routes
@app.route("/")
def welcome():
    """List all available API routes."""
    return (
        f"Welcome to the Hawaii Climate API!<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/<start><br/>"
        f"/api/v1.0/<start>/<end>"
    )

# Precipitation Route: Return the last 12 months of precipitation data
@app.route("/api/v1.0/precipitation")
def precipitation():
    """Return the last 12 months of precipitation data."""
    # Calculate the date one year from the last date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Query precipitation data
    results = session.query(Measurement.date, Measurement.prcp).filter(
        Measurement.date >= one_year_ago).all()

    # Convert query results to a dictionary
    precipitation_data = {date: prcp for date, prcp in results}

    return jsonify(precipitation_data)

# Stations Route: Return a list of all station IDs
@app.route("/api/v1.0/stations")
def stations():
    """Return a list of stations."""
    results = session.query(Station.station).all()

    # Convert results to a list
    station_list = [station[0] for station in results]

    return jsonify(station_list)

# TOBS Route: Return temperature observations for the most active station
@app.route("/api/v1.0/tobs")
def tobs():
    """Return temperature observations for the most active station for the last 12 months."""
    # Find the most active station
    most_active_station = session.query(Measurement.station).group_by(Measurement.station)\
        .order_by(func.count(Measurement.station).desc()).first()[0]

    # Calculate the date one year from the last date in the dataset
    most_recent_date = session.query(func.max(Measurement.date)).scalar()
    most_recent_date = dt.datetime.strptime(most_recent_date, '%Y-%m-%d')
    one_year_ago = most_recent_date - dt.timedelta(days=365)

    # Query temperature observations for the most active station
    results = session.query(Measurement.date, Measurement.tobs).filter(
        Measurement.station == most_active_station,
        Measurement.date >= one_year_ago).all()

    # Convert query results into a list of dictionaries
    tobs_data = [{date: tobs} for date, tobs in results]

    return jsonify(tobs_data)

# Start Route: Return temperature stats from a given start date
@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start, end=None):
    """Return the minimum, average, and maximum temperatures for a date range."""
    # Select the functions to calculate temperature stats
    sel = [func.min(Measurement.tobs), func.avg(Measurement.tobs), func.max(Measurement.tobs)]

    # Handle optional end date
    if end:
        results = session.query(*sel).filter(
            Measurement.date >= start,
            Measurement.date <= end).all()
    else:
        results = session.query(*sel).filter(Measurement.date >= start).all()

    # Convert the query results to a dictionary
    temps = {
        "TMIN": results[0][0],
        "TAVG": round(results[0][1], 2),
        "TMAX": results[0][2]
    }

    return jsonify(temps)

#################################################
# Run the Flask App
#################################################
if __name__ == "__main__":
    app.run(debug=True)
