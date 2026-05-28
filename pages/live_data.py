"""
Live Race Data Page - Real-time F1 data using FastF1

This page provides:
- Session selection (Practice, Qualifying, Race)
- Live lap times and sector analysis
- Telemetry visualization
- Weather conditions
- Driver performance metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastf1_integration import (
    get_season_schedule,
    get_session_data,
    get_lap_times,
    get_fastest_laps,
    get_weather_data,
    get_available_races,
    get_team_colors
)


def show():
    """Main function to display the live race data page."""
    
    st.markdown('<div class="main-header">📊 Live Race Data</div>', unsafe_allow_html=True)
    st.markdown("Access real Formula 1 data powered by FastF1 - lap times, telemetry, weather, and more.")
    
    # Sidebar controls
    st.sidebar.header("🏎️ Session Selection")
    
    # Year selection
    year = st.sidebar.selectbox(
        "Season",
        options=[2024, 2025, 2026],
        index=2
    )
    
    # Get available races
    with st.spinner("Loading race schedule..."):
        races = get_available_races(year)
    
    if not races:
        st.error("No races available for selected year.")
        return
    
    # Race selection
    selected_race = st.sidebar.selectbox(
        "Grand Prix",
        options=races,
        index=min(len(races)-1, 5)  # Default to 6th race or last available
    )
    
    # Session type selection
    session_type = st.sidebar.radio(
        "Session Type",
        options=['P1', 'P2', 'P3', 'Q', 'R'],
        format_func=lambda x: {
            'P1': 'Practice 1',
            'P2': 'Practice 2',
            'P3': 'Practice 3',
            'Q': 'Qualifying',
            'R': 'Race'
        }.get(x, x),
        index=4  # Default to Race
    )
    
    # Load session data
    with st.spinner(f"Loading {selected_race} {session_type} data..."):
        session = get_session_data(year, selected_race, session_type)
    
    if session is None:
        st.error("Failed to load session data. This session may not be available yet.")
        return
    
    # Display session info
    st.markdown("### Session Information")
    col1, col2, col3, col4 = st.columns(4)
    
    col1.metric("Circuit", session.event['EventName'])
    col2.metric("Date", str(session.event['EventDate'])[:10])
    col3.metric("Total Laps", len(session.laps))
    col4.metric("Weather Available", "✅" if hasattr(session, 'weather_data') else "❌")
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "⏱️ Lap Times", 
        "🚀 Telemetry Analysis", 
        "🌤️ Weather Conditions",
        "🏆 Fastest Laps"
    ])
    
    with tab1:
        show_lap_times(session)
    
    with tab2:
        show_telemetry_analysis(session)
    
    with tab3:
        show_weather_data(session)
    
    with tab4:
        show_fastest_laps(session)


def show_lap_times(session):
    """Display lap time analysis."""
    
    st.markdown("#### Lap Time Analysis")
    
    # Driver selection filter
    all_drivers = session.laps['Driver'].unique()
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_drivers = st.multiselect(
            "Select Drivers to Compare",
            options=all_drivers,
            default=all_drivers[:3] if len(all_drivers) >= 3 else all_drivers.tolist(),
            help="Select up to 5 drivers for comparison"
        )
    
    with col2:
        show_outliers = st.checkbox("Show Outlier Laps", value=False)
    
    if not selected_drivers:
        st.warning("Please select at least one driver.")
        return
    
    # Get lap times for selected drivers
    laps_data = get_lap_times(session)
    
    if laps_data.empty:
        st.warning("No lap time data available.")
        return
    
    # Filter for selected drivers
    filtered_laps = laps_data[laps_data['Driver'].isin(selected_drivers)]
    
    if filtered_laps.empty:
        st.warning("No data for selected drivers.")
        return
    
    # Remove outliers if requested
    if not show_outliers:
        # Filter out laps that are significantly slower (likely yellow flags, etc.)
        median_time = filtered_laps['LapTimeSeconds'].median()
        std_time = filtered_laps['LapTimeSeconds'].std()
        filtered_laps = filtered_laps[
            filtered_laps['LapTimeSeconds'] < (median_time + 2 * std_time)
        ]
    
    # Lap time evolution chart
    st.markdown("##### Lap Time Evolution")
    
    fig = px.line(
        filtered_laps,
        x='LapNumber',
        y='LapTimeSeconds',
        color='Driver',
        title=f"Lap Times - {session.event['EventName']} ({session.name})",
        labels={
            'LapNumber': 'Lap Number',
            'LapTimeSeconds': 'Lap Time (seconds)',
            'Driver': 'Driver'
        },
        markers=True
    )
    
    fig.update_layout(
        height=500,
        template='plotly_white',
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Sector times comparison
    st.markdown("##### Sector Time Comparison")
    
    sector_cols = ['Sector1TimeSeconds', 'Sector2TimeSeconds', 'Sector3TimeSeconds']
    
    # Calculate average sector times per driver
    sector_avg = filtered_laps.groupby('Driver')[sector_cols].mean().reset_index()
    
    # Melt for better visualization
    sector_melted = sector_avg.melt(
        id_vars=['Driver'],
        value_vars=sector_cols,
        var_name='Sector',
        value_name='Average Time (s)'
    )
    
    fig = px.bar(
        sector_melted,
        x='Driver',
        y='Average Time (s)',
        color='Sector',
        barmode='group',
        title="Average Sector Times by Driver",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Raw data table
    with st.expander("📋 View Raw Lap Data"):
        st.dataframe(
            filtered_laps[['Driver', 'LapNumber', 'LapTimeSeconds', 
                          'Sector1TimeSeconds', 'Sector2TimeSeconds', 'Sector3TimeSeconds', 
                          'Compound', 'TyreLife']],
            use_container_width=True,
            hide_index=True
        )


def show_telemetry_analysis(session):
    """Display telemetry data visualization."""
    
    st.markdown("#### Telemetry Analysis")
    st.info("Telemetry shows speed, throttle, brake, and gear data throughout a lap.")
    
    # Select driver for telemetry
    all_drivers = session.laps['Driver'].unique()
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_driver = st.selectbox(
            "Select Driver",
            options=all_drivers,
            index=0
        )
    
    with col2:
        lap_selection = st.radio(
            "Lap Selection",
            options=['Fastest', 'Average', 'Specific'],
            horizontal=True
        )
    
    # Get driver's laps
    driver_laps = session.laps.pick_driver(selected_driver)
    
    if len(driver_laps) == 0:
        st.warning("No laps found for selected driver.")
        return
    
    # Select specific lap
    if lap_selection == 'Fastest':
        selected_lap = driver_laps.pick_fastest()
    elif lap_selection == 'Average':
        # Find lap closest to median time
        valid_laps = driver_laps[driver_laps['LapTime'].notna()]
        median_time = valid_laps['LapTime'].median()
        closest_idx = (valid_laps['LapTime'] - median_time).abs().idxmin()
        selected_lap = valid_laps.loc[closest_idx]
    else:
        # Let user pick from dropdown
        lap_numbers = driver_laps['LapNumber'].tolist()
        selected_lap_num = st.selectbox("Select Lap Number", options=lap_numbers)
        selected_lap = driver_laps[driver_laps['LapNumber'] == selected_lap_num].iloc[0]
    
    # Display lap info
    st.markdown(f"**Selected Lap:** Lap {selected_lap['LapNumber']} | "
                f"Time: {selected_lap['LapTime']} | "
                f"Compound: {selected_lap['Compound']}")
    
    # Get telemetry data
    try:
        telemetry = selected_lap.get_telemetry()
        
        if telemetry is None or len(telemetry) == 0:
            st.warning("No telemetry data available for this lap.")
            return
        
        # Speed trace
        st.markdown("##### Speed Trace")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=telemetry['Distance'],
            y=telemetry['Speed'],
            mode='lines',
            name='Speed',
            line=dict(color='#FF1801', width=2)
        ))
        
        fig.update_layout(
            title=f"Speed vs Distance - {selected_driver} (Lap {selected_lap['LapNumber']})",
            xaxis_title="Distance (m)",
            yaxis_title="Speed (km/h)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Throttle and Brake
        st.markdown("##### Throttle & Brake Application")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=telemetry['Distance'],
            y=telemetry['Throttle'],
            mode='lines',
            name='Throttle (%)',
            line=dict(color='green', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=telemetry['Distance'],
            y=telemetry['Brake'],
            mode='lines',
            name='Brake (%)',
            line=dict(color='red', width=2)
        ))
        
        fig.update_layout(
            title=f"Throttle & Brake - {selected_driver}",
            xaxis_title="Distance (m)",
            yaxis_title="Application (%)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # RPM and Gear
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                telemetry,
                x='Distance',
                y='RPM',
                title="RPM Throughout Lap",
                labels={'RPM': 'Engine RPM'}
            )
            fig.update_layout(height=350, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                telemetry,
                x='Distance',
                y='nGear',
                title="Gear Changes",
                labels={'nGear': 'Gear'}
            )
            fig.update_layout(height=350, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        
        # DRS zones
        if 'DRS' in telemetry.columns:
            st.markdown("##### DRS Activation")
            
            drs_active = telemetry[telemetry['DRS'] > 0]
            
            if len(drs_active) > 0:
                fig = px.area(
                    drs_active,
                    x='Distance',
                    y='DRS',
                    title="DRS Zones",
                    labels={'DRS': 'DRS Level'}
                )
                fig.update_layout(height=300, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No DRS activation detected in this lap.")
    
    except Exception as e:
        st.error(f"Error loading telemetry: {e}")
        st.exception(e)


def show_weather_data(session):
    """Display weather conditions during the session."""
    
    st.markdown("#### Weather Conditions")
    
    try:
        weather_df = get_weather_data(session)
        
        if weather_df is None or weather_df.empty:
            st.warning("No weather data available for this session.")
            return
        
        # Convert Time to readable format
        weather_df['TimeMinutes'] = weather_df['Time'].apply(
            lambda x: x.total_seconds() / 60 if hasattr(x, 'total_seconds') else 0
        )
        
        # Temperature chart
        st.markdown("##### Track & Air Temperature")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=weather_df['TimeMinutes'],
            y=weather_df['TrackTemp'],
            mode='lines+markers',
            name='Track Temp (°C)',
            line=dict(color='#FF1801', width=2),
            marker=dict(size=6)
        ))
        
        fig.add_trace(go.Scatter(
            x=weather_df['TimeMinutes'],
            y=weather_df['AirTemp'],
            mode='lines+markers',
            name='Air Temp (°C)',
            line=dict(color='#15154e', width=2),
            marker=dict(size=6)
        ))
        
        fig.update_layout(
            title="Temperature Throughout Session",
            xaxis_title="Time (minutes)",
            yaxis_title="Temperature (°C)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Other weather metrics
        col1, col2 = st.columns(2)
        
        with col1:
            fig = px.line(
                weather_df,
                x='TimeMinutes',
                y='Humidity',
                title="Humidity (%)",
                labels={'Humidity': 'Relative Humidity (%)'}
            )
            fig.update_layout(height=350, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = px.line(
                weather_df,
                x='TimeMinutes',
                y='WindSpeed',
                title="Wind Speed (m/s)",
                labels={'WindSpeed': 'Wind Speed (m/s)'}
            )
            fig.update_layout(height=350, template='plotly_white')
            st.plotly_chart(fig, use_container_width=True)
        
        # Rain indicator
        if 'Rainfall' in weather_df.columns:
            st.markdown("##### Rainfall Detection")
            
            rain_periods = weather_df[weather_df['Rainfall'] > 0]
            
            if len(rain_periods) > 0:
                st.warning(f"🌧️ Rain detected during {len(rain_periods)} time periods!")
                
                fig = px.bar(
                    rain_periods,
                    x='TimeMinutes',
                    y='Rainfall',
                    title="Rainfall Events",
                    labels={'Rainfall': 'Rain Intensity'}
                )
                fig.update_layout(height=300, template='plotly_white')
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("☀️ No rainfall detected during this session.")
        
        # Summary statistics
        st.markdown("##### Weather Summary")
        
        col1, col2, col3, col4 = st.columns(4)
        
        col1.metric("Avg Track Temp", f"{weather_df['TrackTemp'].mean():.1f}°C")
        col2.metric("Avg Air Temp", f"{weather_df['AirTemp'].mean():.1f}°C")
        col3.metric("Avg Humidity", f"{weather_df['Humidity'].mean():.1f}%")
        col4.metric("Avg Wind Speed", f"{weather_df['WindSpeed'].mean():.1f} m/s")
    
    except Exception as e:
        st.error(f"Error displaying weather data: {e}")


def show_fastest_laps(session):
    """Display fastest laps comparison."""
    
    st.markdown("#### Fastest Laps Comparison")
    
    try:
        fastest = get_fastest_laps(session)
        
        if fastest is None or fastest.empty:
            st.warning("No fastest lap data available.")
            return
        
        # Display as table
        st.markdown("##### All Drivers - Fastest Lap Times")
        
        display_df = fastest[['Driver', 'Team', 'LapTime', 'LapTimeSeconds', 
                             'Speed', 'Compound']].copy()
        display_df.columns = ['Driver', 'Team', 'Lap Time', 'Time (s)', 
                             'Avg Speed (km/h)', 'Tire Compound']
        
        # Sort by time
        display_df = display_df.sort_values('Time (s)')
        
        # Add position column
        display_df.insert(0, 'Position', range(1, len(display_df) + 1))
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Position": st.column_config.NumberColumn(format="%d"),
                "Time (s)": st.column_config.NumberColumn(format="%.3f"),
            }
        )
        
        # Visualization
        st.markdown("##### Fastest Lap Time Comparison")
        
        top10 = display_df.head(10)
        
        fig = px.bar(
            top10,
            x='Driver',
            y='Time (s)',
            color='Team',
            title="Top 10 Fastest Laps",
            labels={'Time (s)': 'Lap Time (seconds)'},
            color_discrete_sequence=px.colors.qualitative.Set1
        )
        
        # Invert y-axis so fastest is on top
        fig.update_layout(
            yaxis=dict(autorange="reversed"),
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Gap to leader
        st.markdown("##### Gap to Leader")
        
        if len(top10) > 1:
            leader_time = top10.iloc[0]['Time (s)']
            top10 = top10.copy()
            top10['Gap (s)'] = top10['Time (s)'] - leader_time
            
            fig = px.bar(
                top10,
                x='Driver',
                y='Gap (s)',
                color='Gap (s)',
                color_continuous_scale=['green', 'yellow', 'red'],
                title="Time Gap to Fastest Lap",
                labels={'Gap (s)': 'Gap to Leader (seconds)'}
            )
            
            fig.update_layout(
                height=400,
                template='plotly_white'
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error displaying fastest laps: {e}")
