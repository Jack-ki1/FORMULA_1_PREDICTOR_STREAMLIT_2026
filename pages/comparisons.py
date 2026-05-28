"""
Comparisons Page - Side-by-side driver and team comparisons

Features:
- Head-to-head driver comparisons with telemetry
- Team performance comparisons
- Season-long battles
- Custom comparison tools
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
    get_driver_info,
    get_lap_times,
    compare_drivers_teardown,
    get_race_results,
    get_available_races
)


def show():
    """Main function to display the comparisons page."""
    
    st.markdown('<div class="main-header">⚖️ Driver & Team Comparisons</div>', unsafe_allow_html=True)
    st.markdown("Compare drivers head-to-head with detailed telemetry and performance metrics.")
    
    # Sidebar controls
    st.sidebar.header("🔍 Comparison Settings")
    
    # Get driver list
    with st.spinner("Loading driver information..."):
        drivers_df = get_driver_info()
    
    if drivers_df is None or drivers_df.empty:
        st.error("Could not load driver information.")
        return
    
    # Create display names
    drivers_df['DisplayName'] = drivers_df.apply(
        lambda row: f"{row['Code']} - {row['FullName']}", axis=1
    )
    
    # Driver 1 selection
    driver1_display = st.sidebar.selectbox(
        "Driver 1",
        options=drivers_df['DisplayName'].tolist(),
        index=0,
        key='driver1'
    )
    
    # Driver 2 selection
    driver2_display = st.sidebar.selectbox(
        "Driver 2",
        options=drivers_df['DisplayName'].tolist(),
        index=1 if len(drivers_df) > 1 else 0,
        key='driver2'
    )
    
    driver1_code = drivers_df[drivers_df['DisplayName'] == driver1_display].iloc[0]['Code']
    driver2_code = drivers_df[drivers_df['DisplayName'] == driver2_display].iloc[0]['Code']
    
    if driver1_code == driver2_code:
        st.warning("Please select two different drivers for comparison.")
        return
    
    # Race/Session selection
    year = st.sidebar.selectbox("Season", options=[2024, 2025, 2026], index=2)
    
    races = get_available_races(year)
    
    if not races:
        st.error("No races available.")
        return
    
    selected_race = st.sidebar.selectbox(
        "Grand Prix",
        options=races,
        index=min(len(races)-1, 3)
    )
    
    session_type = st.sidebar.radio(
        "Session Type",
        options=['Q', 'R'],
        format_func=lambda x: 'Qualifying' if x == 'Q' else 'Race',
        horizontal=True
    )
    
    # Main content
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"### 🏎️ {driver1_code}")
        driver1_info = drivers_df[drivers_df['Code'] == driver1_code].iloc[0]
        st.write(f"**{driver1_info['FullName']}**")
        st.write(f"Team: {driver1_info['Team']}")
    
    with col2:
        st.markdown(f"### 🏎️ {driver2_code}")
        driver2_info = drivers_df[drivers_df['Code'] == driver2_code].iloc[0]
        st.write(f"**{driver2_info['FullName']}**")
        st.write(f"Team: {driver2_info['Team']}")
    
    st.markdown("---")
    
    # Tabs for different comparison types
    tab1, tab2, tab3 = st.tabs([
        "📊 Season Performance",
        "🚀 Telemetry Comparison",
        "🏁 Race Results"
    ])
    
    with tab1:
        show_season_comparison(driver1_code, driver2_code, year)
    
    with tab2:
        show_telemetry_comparison(driver1_code, driver2_code, year, selected_race, session_type)
    
    with tab3:
        show_race_results_comparison(driver1_code, driver2_code, year, selected_race)


def show_season_comparison(driver1: str, driver2: str, year: int):
    """Compare drivers across the entire season."""
    
    st.markdown(f"### {year} Season Head-to-Head")
    
    schedule = get_season_schedule(year)
    
    if schedule is None:
        return
    
    # Collect race-by-race results
    comparison_data = []
    
    sample_races = schedule.head(min(10, len(schedule)))
    
    progress_bar = st.progress(0)
    
    for idx, (_, race) in enumerate(sample_races.iterrows()):
        race_name = race['EventName']
        
        try:
            results = get_race_results(year, race_name)
            
            if results is not None and not results.empty:
                d1_result = results[results['Abbreviation'] == driver1]
                d2_result = results[results['Abbreviation'] == driver2]
                
                if not d1_result.empty and not d2_result.empty:
                    d1_row = d1_result.iloc[0]
                    d2_row = d2_result.iloc[0]
                    
                    comparison_data.append({
                        'Race': race_name[:20],
                        'Round': race['RoundNumber'],
                        'D1_Position': d1_row['Position'],
                        'D2_Position': d2_row['Position'],
                        'D1_Points': d1_row['Points'],
                        'D2_Points': d2_row['Points'],
                        'D1_Status': d1_row['Status'],
                        'D2_Status': d2_row['Status']
                    })
        except:
            pass
        
        progress_bar.progress((idx + 1) / len(sample_races))
    
    progress_bar.empty()
    
    if not comparison_data:
        st.info("No comparable race results found for these drivers.")
        return
    
    comp_df = pd.DataFrame(comparison_data)
    
    # Summary statistics
    st.markdown("#### Season Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    d1_wins = len(comp_df[comp_df['D1_Position'] < comp_df['D2_Position']])
    d2_wins = len(comp_df[comp_df['D2_Position'] < comp_df['D1_Position']])
    d1_total_points = comp_df['D1_Points'].sum()
    d2_total_points = comp_df['D2_Points'].sum()
    
    col1.metric(f"{driver1} Better Finishes", d1_wins)
    col2.metric(f"{driver2} Better Finishes", d2_wins)
    col3.metric(f"{driver1} Total Points", int(d1_total_points))
    col4.metric(f"{driver2} Total Points", int(d2_total_points))
    
    # Position comparison chart
    st.markdown("#### Race Positions Comparison")
    
    # Melt for grouped bar chart
    positions_df = pd.melt(
        comp_df,
        id_vars=['Race'],
        value_vars=['D1_Position', 'D2_Position'],
        var_name='Driver',
        value_name='Position'
    )
    
    positions_df['Driver'] = positions_df['Driver'].map({
        'D1_Position': driver1,
        'D2_Position': driver2
    })
    
    fig = px.bar(
        positions_df,
        x='Race',
        y='Position',
        color='Driver',
        barmode='group',
        title="Finishing Positions by Race",
        labels={'Position': 'Finishing Position'},
        color_discrete_map={driver1: '#FF1801', driver2: '#15154e'}
    )
    
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=500,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Points comparison
    st.markdown("#### Points Scored by Race")
    
    points_df = pd.melt(
        comp_df,
        id_vars=['Race'],
        value_vars=['D1_Points', 'D2_Points'],
        var_name='Driver',
        value_name='Points'
    )
    
    points_df['Driver'] = points_df['Driver'].map({
        'D1_Points': driver1,
        'D2_Points': driver2
    })
    
    fig = px.bar(
        points_df,
        x='Race',
        y='Points',
        color='Driver',
        barmode='group',
        title="Championship Points by Race",
        color_discrete_map={driver1: '#FF1801', driver2: '#15154e'}
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_telemetry_comparison(driver1: str, driver2: str, year: int, 
                             race_name: str, session_type: str):
    """Compare telemetry data between two drivers."""
    
    st.markdown("### Telemetry Comparison")
    st.info("This compares the fastest laps of both drivers in the selected session.")
    
    # Load session
    with st.spinner("Loading session data..."):
        session = get_session_data(year, race_name, session_type)
    
    if session is None:
        st.error("Could not load session data.")
        return
    
    # Check if both drivers participated
    session_drivers = session.laps['Driver'].unique()
    
    if driver1 not in session_drivers:
        st.warning(f"{driver1} did not participate in this session.")
        return
    
    if driver2 not in session_drivers:
        st.warning(f"{driver2} did not participate in this session.")
        return
    
    # Get fastest laps
    try:
        lap1 = session.laps.pick_driver(driver1).pick_fastest()
        lap2 = session.laps.pick_driver(driver2).pick_fastest()
        
        st.markdown("#### Fastest Lap Information")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**{driver1}**")
            st.write(f"Lap Time: {lap1['LapTime']}")
            st.write(f"Tire Compound: {lap1['Compound']}")
            st.write(f"Tire Life: {lap1['TyreLife']} laps")
        
        with col2:
            st.markdown(f"**{driver2}**")
            st.write(f"Lap Time: {lap2['LapTime']}")
            st.write(f"Tire Compound: {lap2['Compound']}")
            st.write(f"Tire Life: {lap2['TyreLife']} laps")
        
        # Calculate time difference
        time_diff = (lap1['LapTime'] - lap2['LapTime']).total_seconds()
        
        if time_diff < 0:
            st.success(f"🏆 **{driver1}** was faster by {abs(time_diff):.3f} seconds")
        else:
            st.success(f"🏆 **{driver2}** was faster by {abs(time_diff):.3f} seconds")
        
        # Get telemetry
        tel1 = lap1.get_telemetry().add_distance()
        tel2 = lap2.get_telemetry().add_distance()
        
        # Speed comparison
        st.markdown("#### Speed Trace Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=tel1['Distance'],
            y=tel1['Speed'],
            mode='lines',
            name=f'{driver1}',
            line=dict(color='#FF1801', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=tel2['Distance'],
            y=tel2['Speed'],
            mode='lines',
            name=f'{driver2}',
            line=dict(color='#15154e', width=2)
        ))
        
        fig.update_layout(
            title="Speed vs Distance - Fastest Laps",
            xaxis_title="Distance (m)",
            yaxis_title="Speed (km/h)",
            height=500,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Throttle comparison
        st.markdown("#### Throttle Application Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=tel1['Distance'],
            y=tel1['Throttle'],
            mode='lines',
            name=f'{driver1}',
            line=dict(color='#FF1801', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=tel2['Distance'],
            y=tel2['Throttle'],
            mode='lines',
            name=f'{driver2}',
            line=dict(color='#15154e', width=2)
        ))
        
        fig.update_layout(
            title="Throttle Application",
            xaxis_title="Distance (m)",
            yaxis_title="Throttle (%)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Brake comparison
        st.markdown("#### Brake Application Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=tel1['Distance'],
            y=tel1['Brake'],
            mode='lines',
            name=f'{driver1}',
            line=dict(color='#FF1801', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=tel2['Distance'],
            y=tel2['Brake'],
            mode='lines',
            name=f'{driver2}',
            line=dict(color='#15154e', width=2)
        ))
        
        fig.update_layout(
            title="Brake Application",
            xaxis_title="Distance (m)",
            yaxis_title="Brake (%)",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # RPM comparison
        st.markdown("#### Engine RPM Comparison")
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatter(
            x=tel1['Distance'],
            y=tel1['RPM'],
            mode='lines',
            name=f'{driver1}',
            line=dict(color='#FF1801', width=2)
        ))
        
        fig.add_trace(go.Scatter(
            x=tel2['Distance'],
            y=tel2['RPM'],
            mode='lines',
            name=f'{driver2}',
            line=dict(color='#15154e', width=2)
        ))
        
        fig.update_layout(
            title="Engine RPM Throughout Lap",
            xaxis_title="Distance (m)",
            yaxis_title="RPM",
            height=400,
            template='plotly_white',
            hovermode='x unified'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error comparing telemetry: {e}")
        st.exception(e)


def show_race_results_comparison(driver1: str, driver2: str, year: int, race_name: str):
    """Show detailed race results comparison."""
    
    st.markdown("### Race Results Comparison")
    
    try:
        results = get_race_results(year, race_name)
        
        if results is None or results.empty:
            st.info("No race results available.")
            return
        
        d1_result = results[results['Abbreviation'] == driver1]
        d2_result = results[results['Abbreviation'] == driver2]
        
        if d1_result.empty or d2_result.empty:
            st.warning("One or both drivers did not finish this race.")
            return
        
        d1_row = d1_result.iloc[0]
        d2_row = d2_result.iloc[0]
        
        # Side-by-side comparison table
        st.markdown("#### Detailed Comparison")
        
        comparison_dict = {
            'Metric': [
                'Finishing Position',
                'Grid Position',
                'Points Scored',
                'Status',
                'Fastest Lap',
                'Average Speed'
            ],
            driver1: [
                f"P{d1_row['Position']}",
                f"P{d1_row.get('GridPosition', 'N/A')}",
                d1_row['Points'],
                d1_row['Status'],
                d1_row.get('FastestLapTime', 'N/A'),
                f"{d1_row.get('AvgSpeed', 0):.1f} km/h" if pd.notna(d1_row.get('AvgSpeed')) else 'N/A'
            ],
            driver2: [
                f"P{d2_row['Position']}",
                f"P{d2_row.get('GridPosition', 'N/A')}",
                d2_row['Points'],
                d2_row['Status'],
                d2_row.get('FastestLapTime', 'N/A'),
                f"{d2_row.get('AvgSpeed', 0):.1f} km/h" if pd.notna(d2_row.get('AvgSpeed')) else 'N/A'
            ]
        }
        
        comparison_df = pd.DataFrame(comparison_dict)
        
        st.dataframe(
            comparison_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Visual comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                label=f"{driver1} Position",
                value=f"P{d1_row['Position']}",
                delta=None
            )
            st.metric(
                label=f"{driver1} Points",
                value=d1_row['Points']
            )
        
        with col2:
            st.metric(
                label=f"{driver2} Position",
                value=f"P{d2_row['Position']}",
                delta=None
            )
            st.metric(
                label=f"{driver2} Points",
                value=d2_row['Points']
            )
    
    except Exception as e:
        st.error(f"Error loading race results: {e}")
