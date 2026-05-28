"""
FastF1 Integration Module - Fetches and processes real F1 data

This module provides functions to:
- Load race sessions (practice, qualifying, race)
- Fetch telemetry data (speed, throttle, brake, etc.)
- Get lap times and sector analysis
- Retrieve weather data
- Access driver and team information
"""

import fastf1
from fastf1 import plotting
import pandas as pd
import numpy as np
from typing import Optional, Dict, List
import streamlit as st
from datetime import datetime
import os

# Enable FastF1 cache for faster subsequent loads
CACHE_DIR = ".fastf1_cache"
if not os.path.exists(CACHE_DIR):
    os.makedirs(CACHE_DIR)

fastf1.Cache.enable_cache(CACHE_DIR)

# Setup matplotlib with F1 colors
plotting.setup_mpl()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_season_schedule(year: int = 2026):
    """Get the complete season schedule."""
    try:
        schedule = fastf1.get_event_schedule(year)
        return schedule
    except Exception as e:
        st.error(f"Error fetching schedule: {e}")
        return None


@st.cache_data(ttl=3600)
def get_session_data(year: int, race_name: str, session_type: str = 'R'):
    """
    Load a specific F1 session.
    
    Args:
        year: Season year
        race_name: Race name or round number
        session_type: 'P1', 'P2', 'P3', 'Q', 'S', 'R' (Practice, Qualifying, Sprint, Race)
    
    Returns:
        Session object with loaded data
    """
    try:
        session = fastf1.get_session(year, race_name, session_type)
        session.load(telemetry=True, weather=True, messages=True)
        return session
    except Exception as e:
        st.error(f"Error loading session: {e}")
        return None


@st.cache_data(ttl=3600)
def get_lap_times(_session, driver_code: Optional[str] = None):
    """
    Extract lap times from a session.
    
    Args:
        _session: FastF1 session object (underscore prefix prevents caching issues)
        driver_code: Optional 3-letter driver code (e.g., 'VER', 'HAM')
    
    Returns:
        DataFrame with lap time data
    """
    try:
        laps = _session.laps
        
        if driver_code:
            laps = laps.pick_driver(driver_code)
        
        # Filter out invalid laps
        laps = laps[laps['LapTime'].notna()]
        
        # Convert LapTime to seconds for easier analysis
        laps_df = laps[['Driver', 'LapNumber', 'LapTime', 'Sector1Time', 
                        'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife',
                        'Team', 'Position']].copy()
        
        # Convert timedelta to seconds
        for col in ['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']:
            if col in laps_df.columns:
                laps_df[col] = laps_df[col].apply(lambda x: x.total_seconds() if pd.notna(x) else None)
        
        # Rename columns to indicate they're in seconds
        laps_df = laps_df.rename(columns={
            'LapTime': 'LapTimeSeconds',
            'Sector1Time': 'Sector1TimeSeconds',
            'Sector2Time': 'Sector2TimeSeconds',
            'Sector3Time': 'Sector3TimeSeconds'
        })
        
        return laps_df
    except Exception as e:
        st.error(f"Error extracting lap times: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_telemetry_data(lap, _session):
    """
    Get detailed telemetry for a specific lap.
    
    Args:
        lap: Lap object from session.laps
        _session: FastF1 session object (underscore prefix prevents caching issues)
    
    Returns:
        DataFrame with telemetry data (Speed, RPM, Throttle, Brake, Gear, etc.)
    """
    try:
        telemetry = lap.get_telemetry()
        
        # Add distance and time columns
        telemetry = telemetry[['Distance', 'Time', 'Speed', 'RPM', 'nGear', 
                               'Throttle', 'Brake', 'DRS']].copy()
        
        return telemetry
    except Exception as e:
        st.error(f"Error extracting telemetry: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_fastest_laps(_session):
    """Get fastest lap for each driver in the session."""
    try:
        fastest_laps = _session.laps.pick_fastest()
        
        result = fastest_laps[['Driver', 'Team', 'LapTime', 'Speed', 
                               'Compound', 'TyreLife']].copy()
        
        # Convert LapTime to seconds
        result['LapTimeSeconds'] = result['LapTime'].apply(
            lambda x: x.total_seconds() if pd.notna(x) else None
        )
        
        return result.sort_values('LapTimeSeconds')
    except Exception as e:
        st.error(f"Error getting fastest laps: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def get_qualifying_results(year: int, race_name: str):
    """Get qualifying results (Q1, Q2, Q3 times)."""
    try:
        session = get_session_data(year, race_name, 'Q')
        if session is None:
            return None
        
        results = session.results[['Abbreviation', 'FullName', 'TeamName', 
                                   'Q1', 'Q2', 'Q3', 'GridPosition']].copy()
        
        # Convert times to seconds
        for col in ['Q1', 'Q2', 'Q3']:
            if col in results.columns:
                results[col] = results[col].apply(
                    lambda x: x.total_seconds() if pd.notna(x) else None
                )
        
        return results
    except Exception as e:
        st.error(f"Error getting qualifying results: {e}")
        return None


@st.cache_data(ttl=3600)
def get_race_results(year: int, race_name: str):
    """Get final race results.

    Notes:
    - FastF1 result schemas can differ across seasons/events.
    - This function is defensive: it only selects columns that exist.
    """
    try:
        session = get_session_data(year, race_name, 'R')
        if session is None:
            return None

        required_cols = [
            'Position',
            'Abbreviation',
            'FullName',
            'TeamName',
            'Points',
            'Status',
            'Time/Retired',
            'FastestLap',
            'FastestLapTime',
            'AvgSpeed',
            'GridPosition',
        ]

        available_cols = [c for c in required_cols if c in session.results.columns]

        # Start from available columns to avoid KeyError
        results = session.results[available_cols].copy()

        # Ensure all required columns exist (fill missing with None)
        for col in required_cols:
            if col not in results.columns:
                results[col] = None

        return results
    except Exception as e:
        st.error(f"Error getting race results: {e}")
        return None


@st.cache_data(ttl=3600)
def get_weather_data(_session):
    """Get weather conditions throughout the session."""
    try:
        weather = _session.weather_data
        
        weather_df = weather[['Time', 'AirTemp', 'Humidity', 'Pressure', 
                              'Rainfall', 'TrackTemp', 'WindDirection', 
                              'WindSpeed']].copy()
        
        return weather_df
    except Exception as e:
        st.error(f"Error getting weather data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=86400)  # Cache for 24 hours
def get_driver_info():
    """Get list of all drivers with their details."""
    try:
        # Use current season to get driver list
        schedule = get_season_schedule(2026)
        if schedule is None or len(schedule) == 0:
            return pd.DataFrame()
        
        # Get first race to extract driver info
        first_race = schedule.iloc[0]
        session = get_session_data(2026, first_race['EventName'], 'R')
        
        if session is None:
            return pd.DataFrame()
        
        drivers = session.drivers
        
        driver_info = []
        for drv_code in drivers:
            drv = session.get_driver(drv_code)
            driver_info.append({
                'Code': drv_code,
                'FirstName': drv.get('FirstName', ''),
                'LastName': drv.get('LastName', ''),
                'FullName': drv.get('FullName', ''),
                'Team': drv.get('TeamName', ''),
                'TeamColor': drv.get('TeamColor', '#000000'),
                'HeadshotUrl': drv.get('HeadshotUrl', ''),
                'CountryCode': drv.get('CountryCode', ''),
                'BroadcastName': drv.get('BroadcastName', '')
            })
        
        return pd.DataFrame(driver_info)
    except Exception as e:
        st.error(f"Error getting driver info: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def compare_drivers_teardown(_session, driver1: str, driver2: str):
    """
    Compare telemetry between two drivers on their fastest laps.
    """
    try:
        # Get fastest laps
        lap1 = _session.laps.pick_driver(driver1).pick_fastest()
        lap2 = _session.laps.pick_driver(driver2).pick_fastest()

        # Get telemetry
        tel1 = lap1.get_telemetry().add_distance()
        tel2 = lap2.get_telemetry().add_distance()

        return {
            'driver1': {
                'lap_time': lap1['LapTime'],
                'telemetry': tel1,
                'compound': lap1['Compound'],
                'tyre_life': lap1['TyreLife']
            },
            'driver2': {
                'lap_time': lap2['LapTime'],
                'telemetry': tel2,
                'compound': lap2['Compound'],
                'tyre_life': lap2['TyreLife']
            }
        }
    except Exception as e:
        st.error(f"Error comparing drivers: {e}")
        return None


def get_available_races(year: int = 2026):
    """Get list of available races for a given year."""
    schedule = get_season_schedule(year)
    if schedule is None:
        return []
    
    return schedule['EventName'].tolist()


def get_team_colors(session):
    """Get team color mapping for consistent visualization."""
    try:
        return plotting.get_team_color_mapping(session)
    except:
        return {}
