"""
Driver Analytics Page - Comprehensive driver performance analysis

Features:
- Driver career statistics
- Season performance trends
- Head-to-head teammate comparisons
- Track-specific performance
- Historical race results
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastf1_integration import (
    get_season_schedule,
    get_session_data,
    get_lap_times,
    get_race_results,
    get_qualifying_results,
    get_driver_info,
    get_available_races
)


def show():
    """Main function to display the driver analytics page."""
    
    st.markdown('<div class="main-header">👤 Driver Analytics</div>', unsafe_allow_html=True)
    st.markdown("Deep dive into driver performance with comprehensive statistics and visualizations.")
    
    # Sidebar controls
    st.sidebar.header("🏎️ Driver Selection")
    
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
    
    # Driver selection
    selected_driver_display = st.sidebar.selectbox(
        "Select Driver",
        options=drivers_df['DisplayName'].tolist(),
        index=0
    )
    
    # Get selected driver info
    selected_row = drivers_df[drivers_df['DisplayName'] == selected_driver_display].iloc[0]
    driver_code = selected_row['Code']
    driver_name = selected_row['FullName']
    team_name = selected_row['Team']
    
    # Display driver header
    col1, col2 = st.columns([1, 3])
    
    with col1:
        if selected_row.get('HeadshotUrl'):
            try:
                st.image(selected_row['HeadshotUrl'], width=150)
            except:
                st.write(f"### {driver_code}")
        else:
            st.write(f"### {driver_code}")
    
    with col2:
        st.markdown(f"## {driver_name}")
        st.markdown(f"**Team:** {team_name} | **Code:** {driver_code}")
        
        # Country flag (if available)
        if selected_row.get('CountryCode'):
            st.markdown(f"**Nationality:** {selected_row['CountryCode']}")
    
    st.markdown("---")
    
    # Main tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 2026 Season Performance",
        "🏁 Race Results History",
        "⚖️ Teammate Comparison",
        "📈 Qualifying vs Race"
    ])
    
    with tab1:
        show_season_performance(driver_code, driver_name, team_name)
    
    with tab2:
        show_race_history(driver_code, driver_name)
    
    with tab3:
        show_teammate_comparison(driver_code, team_name)
    
    with tab4:
        show_qualifying_vs_race(driver_code, driver_name)


def show_season_performance(driver_code: str, driver_name: str, team_name: str):
    """Display current season performance metrics."""
    
    st.markdown("### 2026 Season Performance")
    
    # Get 2026 schedule
    schedule = get_season_schedule(2026)
    
    if schedule is None or len(schedule) == 0:
        st.warning("No 2026 season data available yet.")
        return
    
    # Collect race-by-race results
    race_results = []
    
    races_completed = min(len(schedule), 10)  # Limit to first 10 races for speed
    
    progress_bar = st.progress(0)
    
    for idx, (_, race) in enumerate(schedule.head(races_completed).iterrows()):
        race_name = race['EventName']
        
        try:
            results = get_race_results(2026, race_name)
            
            if results is not None and not results.empty:
                driver_result = results[results['Abbreviation'] == driver_code]
                
                if not driver_result.empty:
                    result_row = driver_result.iloc[0]
                    race_results.append({
                        'Race': race_name[:20],  # Shorten name
                        'Round': race['RoundNumber'],
                        'Position': result_row['Position'],
                        'Points': result_row['Points'],
                        'Status': result_row['Status'],
                        'FastestLap': result_row.get('FastestLapTime', None)
                    })
        except Exception as e:
            # Skip races that aren't available yet
            pass
        
        progress_bar.progress((idx + 1) / races_completed)
    
    progress_bar.empty()
    
    if not race_results:
        st.info("No race results available for this driver in 2026 yet.")
        return
    
    # Convert to DataFrame
    results_df = pd.DataFrame(race_results)
    
    # Summary metrics
    st.markdown("#### Season Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_points = results_df['Points'].sum()
    avg_finish = results_df['Position'].mean()
    best_finish = results_df['Position'].min()
    finishes_in_points = len(results_df[results_df['Position'] <= 10])
    
    col1.metric("Total Points", int(total_points))
    col2.metric("Avg Finish Position", f"{avg_finish:.1f}")
    col3.metric("Best Finish", f"P{int(best_finish)}")
    col4.metric("Points Finishes", finishes_in_points)
    
    # Position progression chart
    st.markdown("#### Championship Position Progression")
    
    fig = px.line(
        results_df,
        x='Round',
        y='Position',
        title=f"Race Finishing Positions - {driver_name}",
        labels={'Position': 'Finishing Position', 'Round': 'Race Round'},
        markers=True
    )
    
    # Invert y-axis so P1 is at top
    fig.update_layout(
        yaxis=dict(autorange="reversed"),
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Points accumulation
    st.markdown("#### Points Accumulation")
    
    results_df['CumulativePoints'] = results_df['Points'].cumsum()
    
    fig = px.area(
        results_df,
        x='Round',
        y='CumulativePoints',
        title=f"Championship Points Over Time - {driver_name}",
        labels={'CumulativePoints': 'Total Points'}
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Detailed results table
    with st.expander("📋 View Detailed Race Results"):
        st.dataframe(
            results_df[['Race', 'Position', 'Points', 'Status']],
            use_container_width=True,
            hide_index=True
        )


def show_race_history(driver_code: str, driver_name: str):
    """Show historical race results across multiple seasons."""
    
    st.markdown("### Career Race History")
    
    # Season selector
    seasons = [2024, 2025, 2026]
    selected_season = st.selectbox("Select Season", options=seasons, index=2)
    
    # Get schedule for selected season
    schedule = get_season_schedule(selected_season)
    
    if schedule is None or len(schedule) == 0:
        st.warning(f"No data available for {selected_season} season.")
        return
    
    # Collect results
    all_results = []
    
    # Sample a few races to demonstrate (for performance)
    sample_races = schedule.head(min(8, len(schedule)))
    
    for _, race in sample_races.iterrows():
        race_name = race['EventName']
        
        try:
            results = get_race_results(selected_season, race_name)
            
            if results is not None and not results.empty:
                driver_result = results[results['Abbreviation'] == driver_code]
                
                if not driver_result.empty:
                    result_row = driver_result.iloc[0]
                    all_results.append({
                        'Grand Prix': race_name,
                        'Date': str(race['EventDate'])[:10],
                        'Position': result_row['Position'],
                        'Points': result_row['Points'],
                        'Grid': result_row.get('GridPosition', 'N/A'),
                        'Status': result_row['Status']
                    })
        except:
            continue
    
    if not all_results:
        st.info(f"No race results found for {driver_name} in {selected_season}.")
        return
    
    results_df = pd.DataFrame(all_results)
    
    # Display table
    st.dataframe(
        results_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Position": st.column_config.NumberColumn(format="P%d"),
        }
    )
    
    # Visualization
    fig = px.bar(
        results_df,
        x='Grand Prix',
        y='Points',
        color='Position',
        color_continuous_scale=['green', 'yellow', 'red'],
        title=f"Points Scored by Race - {selected_season}",
        labels={'Points': 'Championship Points'}
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white',
        xaxis_tickangle=-45
    )
    
    st.plotly_chart(fig, use_container_width=True)


def show_teammate_comparison(driver_code: str, team_name: str):
    """Compare driver with their teammate."""
    
    st.markdown("### Teammate Comparison")
    
    # Get all drivers to find teammate
    drivers_df = get_driver_info()
    
    if drivers_df is None or drivers_df.empty:
        st.warning("Could not load driver information.")
        return
    
    # Find teammate (same team, different driver)
    teammates = drivers_df[
        (drivers_df['Team'] == team_name) & 
        (drivers_df['Code'] != driver_code)
    ]
    
    if teammates.empty:
        st.warning(f"No teammate found for {driver_code} in team {team_name}.")
        return
    
    teammate_code = teammates.iloc[0]['Code']
    teammate_name = teammates.iloc[0]['FullName']
    
    st.info(f"Comparing **{driver_code}** vs **{teammate_code}** ({teammate_name})")
    
    # Get current season races
    schedule = get_season_schedule(2026)
    
    if schedule is None:
        return
    
    # Compare qualifying and race results
    qual_comparisons = []
    race_comparisons = []
    
    sample_races = schedule.head(min(6, len(schedule)))
    
    for _, race in sample_races.iterrows():
        race_name = race['EventName']
        
        try:
            # Get qualifying results
            qual_results = get_qualifying_results(2026, race_name)
            
            if qual_results is not None and not qual_results.empty:
                driver_qual = qual_results[qual_results['Abbreviation'] == driver_code]
                teammate_qual = qual_results[qual_results['Abbreviation'] == teammate_code]
                
                if not driver_qual.empty and not teammate_qual.empty:
                    d_q3 = driver_qual.iloc[0].get('Q3', None)
                    t_q3 = teammate_qual.iloc[0].get('Q3', None)
                    
                    if pd.notna(d_q3) and pd.notna(t_q3):
                        gap = d_q3 - t_q3
                        qual_comparisons.append({
                            'Race': race_name[:20],
                            'Driver_Q3': d_q3,
                            'Teammate_Q3': t_q3,
                            'Gap_Seconds': gap,
                            'Winner': driver_code if gap < 0 else teammate_code
                        })
            
            # Get race results
            race_results = get_race_results(2026, race_name)
            
            if race_results is not None and not race_results.empty:
                driver_race = race_results[race_results['Abbreviation'] == driver_code]
                teammate_race = race_results[race_results['Abbreviation'] == teammate_code]
                
                if not driver_race.empty and not teammate_race.empty:
                    d_pos = driver_race.iloc[0]['Position']
                    t_pos = teammate_race.iloc[0]['Position']
                    d_pts = driver_race.iloc[0]['Points']
                    t_pts = teammate_race.iloc[0]['Points']
                    
                    race_comparisons.append({
                        'Race': race_name[:20],
                        'Driver_Pos': d_pos,
                        'Teammate_Pos': t_pos,
                        'Driver_Points': d_pts,
                        'Teammate_Points': t_pts,
                        'Winner': driver_code if d_pos < t_pos else teammate_code
                    })
        except:
            continue
    
    # Display qualifying comparison
    if qual_comparisons:
        st.markdown("#### Qualifying Head-to-Head")
        
        qual_df = pd.DataFrame(qual_comparisons)
        
        col1, col2 = st.columns(2)
        
        driver_wins = len(qual_df[qual_df['Winner'] == driver_code])
        teammate_wins = len(qual_df[qual_df['Winner'] == teammate_code])
        
        col1.metric(f"{driver_code} Pole Positions", driver_wins)
        col2.metric(f"{teammate_code} Pole Positions", teammate_wins)
        
        # Gap visualization
        fig = px.bar(
            qual_df,
            x='Race',
            y='Gap_Seconds',
            color='Winner',
            title="Qualifying Q3 Gap (Negative = Driver Faster)",
            labels={'Gap_Seconds': 'Time Gap (seconds)'},
            color_discrete_map={driver_code: '#FF1801', teammate_code: '#15154e'}
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Display race comparison
    if race_comparisons:
        st.markdown("#### Race Performance Head-to-Head")
        
        race_df = pd.DataFrame(race_comparisons)
        
        col1, col2, col3 = st.columns(3)
        
        driver_wins = len(race_df[race_df['Winner'] == driver_code])
        teammate_wins = len(race_df[race_df['Winner'] == teammate_code])
        total_points_d = race_df['Driver_Points'].sum()
        total_points_t = race_df['Teammate_Points'].sum()
        
        col1.metric(f"{driver_code} Race Wins", driver_wins)
        col2.metric(f"{teammate_code} Race Wins", teammate_wins)
        col3.metric("Points Ratio", f"{total_points_d}/{total_points_t}")
        
        # Points comparison chart
        points_df = pd.melt(
            race_df,
            id_vars=['Race'],
            value_vars=['Driver_Points', 'Teammate_Points'],
            var_name='Driver',
            value_name='Points'
        )
        
        points_df['Driver'] = points_df['Driver'].map({
            'Driver_Points': driver_code,
            'Teammate_Points': teammate_code
        })
        
        fig = px.bar(
            points_df,
            x='Race',
            y='Points',
            color='Driver',
            barmode='group',
            title="Championship Points by Race",
            color_discrete_map={driver_code: '#FF1801', teammate_code: '#15154e'}
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)


def show_qualifying_vs_race(driver_code: str, driver_name: str):
    """Analyze qualifying performance vs race results."""
    
    st.markdown("### Qualifying vs Race Performance")
    
    # Get current season schedule
    schedule = get_season_schedule(2026)
    
    if schedule is None:
        return
    
    # Collect data
    comparison_data = []
    
    sample_races = schedule.head(min(8, len(schedule)))
    
    for _, race in sample_races.iterrows():
        race_name = race['EventName']
        
        try:
            qual_results = get_qualifying_results(2026, race_name)
            race_results = get_race_results(2026, race_name)
            
            if qual_results is not None and race_results is not None:
                driver_qual = qual_results[qual_results['Abbreviation'] == driver_code]
                driver_race = race_results[race_results['Abbreviation'] == driver_code]
                
                if not driver_qual.empty and not driver_race.empty:
                    grid_pos = driver_qual.iloc[0].get('GridPosition', None)
                    race_pos = driver_race.iloc[0]['Position']
                    
                    if pd.notna(grid_pos):
                        positions_gained = int(grid_pos) - int(race_pos)
                        
                        comparison_data.append({
                            'Race': race_name[:20],
                            'Grid': int(grid_pos),
                            'Finish': int(race_pos),
                            'Positions_Gained': positions_gained
                        })
        except:
            continue
    
    if not comparison_data:
        st.info("No qualifying vs race data available yet.")
        return
    
    comp_df = pd.DataFrame(comparison_data)
    
    # Scatter plot: Grid vs Finish
    st.markdown("#### Grid Position vs Finishing Position")
    
    fig = px.scatter(
        comp_df,
        x='Grid',
        y='Finish',
        text='Race',
        title=f"Qualifying vs Race Result - {driver_name}",
        labels={'Grid': 'Grid Position', 'Finish': 'Finishing Position'}
    )
    
    # Add diagonal line (no change)
    max_pos = max(comp_df['Grid'].max(), comp_df['Finish'].max())
    fig.add_trace(go.Scatter(
        x=[1, max_pos],
        y=[1, max_pos],
        mode='lines',
        name='No Change',
        line=dict(color='gray', dash='dash')
    ))
    
    fig.update_traces(textposition='top center')
    fig.update_layout(
        height=500,
        template='plotly_white',
        xaxis=dict(autorange="reversed"),
        yaxis=dict(autorange="reversed")
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Positions gained/lost bar chart
    st.markdown("#### Positions Gained/Lost in Race")
    
    fig = px.bar(
        comp_df,
        x='Race',
        y='Positions_Gained',
        color='Positions_Gained',
        color_continuous_scale='RdYlGn',
        title="Race Craft - Positions Changed from Grid to Finish",
        labels={'Positions_Gained': 'Positions Gained (+) / Lost (-)'}
    )
    
    fig.update_layout(
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Summary stats
    col1, col2, col3 = st.columns(3)
    
    avg_gain = comp_df['Positions_Gained'].mean()
    races_gained = len(comp_df[comp_df['Positions_Gained'] > 0])
    races_lost = len(comp_df[comp_df['Positions_Gained'] < 0])
    
    col1.metric("Avg Positions Changed", f"{avg_gain:+.1f}")
    col2.metric("Races Gained Positions", races_gained)
    col3.metric("Races Lost Positions", races_lost)
