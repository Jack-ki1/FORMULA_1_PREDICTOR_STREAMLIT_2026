"""
Circuit Analysis Page - Detailed track characteristics and historical data

Features:
- Circuit layout and characteristics
- Historical race data at each track
- Track-specific driver performance
- Overtaking opportunities analysis
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastf1_integration import (
    get_season_schedule,
    get_session_data,
    get_race_results,
    get_lap_times,
    get_available_races
)
from data.circuit_data import get_circuit


def show():
    """Main function to display the circuit analysis page."""
    
    st.markdown('<div class="main-header">🏎️ Circuit Analysis</div>', unsafe_allow_html=True)
    st.markdown("Explore circuit characteristics, historical data, and track-specific insights.")
    
    # Sidebar controls
    st.sidebar.header("🏁 Circuit Selection")
    
    # Get available circuits
    schedule = get_season_schedule(2026)
    
    if schedule is None:
        st.error("Could not load 2026 season schedule.")
        return
    
    # Map FastF1 event names to internal circuit IDs
    circuit_mapping = {
        "Australian Grand Prix": "australia",
        "Chinese Grand Prix": "china",
        "Japanese Grand Prix": "japan",
        "Bahrain Grand Prix": "bahrain",
        "Saudi Arabian Grand Prix": "saudi_arabia",
        "Miami Grand Prix": "miami",
        "Canadian Grand Prix": "canada",
        "Monaco Grand Prix": "monaco",
        "Spanish Grand Prix": "spain",
        "Austrian Grand Prix": "austria",
        "British Grand Prix": "britain",
        "Hungarian Grand Prix": "hungary",
        "Belgian Grand Prix": "belgium",
        "Dutch Grand Prix": "netherlands",
        "Italian Grand Prix": "italy",
        "Madrid Grand Prix": "madrid",
        "Azerbaijan Grand Prix": "azerbaijan",
        "Singapore Grand Prix": "singapore",
        "United States Grand Prix": "usa",
        "Mexico City Grand Prix": "mexico",
        "São Paulo Grand Prix": "brazil",
        "Las Vegas Grand Prix": "las_vegas",
        "Qatar Grand Prix": "qatar",
        "Abu Dhabi Grand Prix": "uae"
    }
    
    # Filter to only include circuits that are in the actual schedule and our mapping
    scheduled_events = schedule['EventName'].tolist()
    circuit_options = [name for name in circuit_mapping.keys() 
                     if name in scheduled_events]
    
    selected_circuit = st.sidebar.selectbox(
        "Select Circuit",
        options=circuit_options,
        index=0
    )
    
    # Get circuit ID from mapping
    circuit_id = circuit_mapping[selected_circuit]
    
    # Display circuit info
    display_circuit_info(selected_circuit, circuit_id)
    
    st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3 = st.tabs([
        "📊 Circuit Characteristics",
        "🏆 Historical Winners",
        "📈 Performance Analysis"
    ])
    
    with tab1:
        show_circuit_characteristics(circuit_id, selected_circuit)
    
    with tab2:
        show_historical_winners(selected_circuit)
    
    with tab3:
        show_performance_analysis(selected_circuit)


def display_circuit_info(circuit_name: str, circuit_id: str):
    """Display basic circuit information."""
    
    st.markdown(f"## {circuit_name}")
    
    # Try to get circuit data from internal database
    try:
        circuit_data = get_circuit(circuit_id)
        
        if circuit_data:
            col1, col2, col3, col4 = st.columns(4)
            
            col1.metric("Lap Count", circuit_data.get('lap_count', 'N/A'))
            col2.metric("Circuit Length", f"{circuit_data.get('length_km', 0)} km")
            col3.metric("SC Probability", f"{circuit_data.get('safety_car_probability', 0)*100:.0f}%")
            col4.metric("Rain Probability", f"{circuit_data.get('rain_probability_typical', 0)*100:.0f}%")
            
            # Circuit type
            circuit_type = circuit_data.get('type', 'Unknown')
            st.info(f"**Circuit Type:** {circuit_type.replace('_', ' ').title()}")
    except Exception as e:
        st.warning(f"Circuit data not available: {e}")


def show_circuit_characteristics(circuit_id: str, circuit_name: str):
    """Display detailed circuit characteristics."""
    
    st.markdown("### Circuit Profile")
    
    # Get circuit data
    try:
        circuit_data = get_circuit(circuit_id)
        
        if not circuit_data:
            st.info("Detailed circuit characteristics not available in database.")
            return
        
        # Create radar chart for circuit characteristics
        characteristics = circuit_data.get('characteristics', {})
        
        if characteristics:
            st.markdown("#### Circuit Characteristics Radar")
            
            categories = list(characteristics.keys())
            values = [characteristics[cat] * 10 for cat in categories]  # Scale to 0-10
            
            fig = go.Figure()
            
            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=[cat.replace('_', ' ').title() for cat in categories],
                fill='toself',
                name=circuit_name,
                line_color='#FF1801'
            ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 10]
                    )
                ),
                height=500,
                title="Circuit Characteristics Profile"
            )
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Track layout description
        if 'description' in circuit_data:
            st.markdown("#### Track Description")
            st.write(circuit_data['description'])
        
        # Key features
        if 'key_features' in circuit_data:
            st.markdown("#### Key Features")
            for feature in circuit_data['key_features']:
                st.markdown(f"- {feature}")
    
    except Exception as e:
        st.error(f"Error loading circuit characteristics: {e}")


def show_historical_winners(circuit_name: str):
    """Show historical race winners at this circuit."""
    
    st.markdown("### Historical Race Winners")
    
    # Collect results from multiple seasons
    all_winners = []
    
    seasons_to_check = [2024, 2025, 2026]
    
    for year in seasons_to_check:
        try:
            results = get_race_results(year, circuit_name)
            
            if results is not None and not results.empty:
                winner = results[results['Position'] == 1]
                
                if not winner.empty:
                    winner_row = winner.iloc[0]
                    all_winners.append({
                        'Year': year,
                        'Driver': winner_row['FullName'],
                        'Team': winner_row['TeamName'],
                        'Time': winner_row.get('Time/Retired', 'N/A')
                    })
        except:
            continue
    
    if not all_winners:
        st.info("No historical winner data available for this circuit yet.")
        return
    
    winners_df = pd.DataFrame(all_winners)
    
    # Display table
    st.dataframe(
        winners_df,
        use_container_width=True,
        hide_index=True
    )
    
    # Team dominance visualization
    st.markdown("#### Team Success at This Circuit")
    
    team_counts = winners_df['Team'].value_counts().reset_index()
    team_counts.columns = ['Team', 'Wins']
    
    fig = px.bar(
        team_counts,
        x='Team',
        y='Wins',
        color='Team',
        title="Constructor Wins at This Circuit",
        color_discrete_sequence=px.colors.qualitative.Set1
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_performance_analysis(circuit_name: str):
    """Analyze driver performance at this specific circuit."""
    
    st.markdown("### Driver Performance Analysis")
    
    # Get most recent race at this circuit
    latest_year = 2026
    
    try:
        race_results = get_race_results(latest_year, circuit_name)
        
        if race_results is None or race_results.empty:
            st.info("No race results available for analysis.")
            return
        
        # Top 10 finishers
        top10 = race_results.head(10)
        
        st.markdown("#### Final Classification")
        
        display_df = top10[['Position', 'Abbreviation', 'FullName', 
                           'TeamName', 'Points', 'Status']].copy()
        display_df.columns = ['Pos', 'Code', 'Driver', 'Team', 'Points', 'Status']
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Points distribution
        st.markdown("#### Points Distribution")
        
        fig = px.bar(
            top10,
            x='Abbreviation',
            y='Points',
            color='Points',
            color_continuous_scale='YlOrRd',
            title="Championship Points Awarded",
            labels={'Points': 'Points Scored'}
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Load lap times for pace analysis
        st.markdown("#### Lap Time Analysis")
        
        session = get_session_data(latest_year, circuit_name, 'R')
        
        if session:
            laps_data = get_lap_times(session)
            
            if not laps_data.empty:
                # Filter for top 5 drivers
                top5_codes = top10['Abbreviation'].head(5).tolist()
                filtered_laps = laps_data[laps_data['Driver'].isin(top5_codes)]
                
                if not filtered_laps.empty:
                    # Remove outliers
                    median_time = filtered_laps['LapTimeSeconds'].median()
                    std_time = filtered_laps['LapTimeSeconds'].std()
                    clean_laps = filtered_laps[
                        filtered_laps['LapTimeSeconds'] < (median_time + 2 * std_time)
                    ]
                    
                    # Average lap time by driver
                    avg_laps = clean_laps.groupby('Driver')['LapTimeSeconds'].mean().reset_index()
                    avg_laps = avg_laps.sort_values('LapTimeSeconds')
                    
                    fig = px.bar(
                        avg_laps,
                        x='Driver',
                        y='LapTimeSeconds',
                        color='LapTimeSeconds',
                        color_continuous_scale='Greens',
                        title="Average Lap Time (Top 5 Drivers)",
                        labels={'LapTimeSeconds': 'Avg Lap Time (seconds)'}
                    )
                    
                    fig.update_layout(
                        yaxis=dict(autorange="reversed"),
                        height=400,
                        template='plotly_white'
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
    
    except Exception as e:
        st.error(f"Error in performance analysis: {e}")
