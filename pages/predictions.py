"""
Predictions Page - Interactive race outcome predictions using the existing prediction engine
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List
import sys
import os

# Add parent directory to path to import prediction engine
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.predictor import predict as run_predict, PredictionRequest
from data.circuit_data import get_circuit
from fastf1_integration import get_season_schedule


def show():
    """Main function to display the predictions page."""
    
    st.markdown('<div class="main-header">🏁 Race Predictions</div>', unsafe_allow_html=True)
    st.markdown("Use our probabilistic prediction engine to forecast race outcomes before they happen.")
    
    # Sidebar controls
    st.sidebar.header("⚙️ Prediction Settings")
    
    # Get available circuits
    try:
        schedule = get_season_schedule(2026)
        
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
        
        if schedule is not None:
            # Filter to only include circuits that are in the actual schedule and our mapping
            scheduled_events = schedule['EventName'].tolist()
            circuit_options = [name for name in circuit_mapping.keys() 
                             if name in scheduled_events]
        else:
            # Fallback to hardcoded list if schedule fails
            circuit_options = list(circuit_mapping.keys())
    except Exception as e:
        st.error(f"Error loading circuits: {e}")
        return
    
    # Circuit selection
    selected_circuit = st.sidebar.selectbox(
        "🏎️ Select Circuit",
        options=circuit_options,
        index=6  # Default to Canadian GP
    )
    
    circuit_id = circuit_mapping[selected_circuit]
    
    # Rain probability slider
    rain_prob = st.sidebar.slider(
        "🌧️ Rain Probability",
        min_value=0.0,
        max_value=1.0,
        value=0.2,
        step=0.05,
        help="Probability of rain during the race (0.0 = dry, 1.0 = guaranteed wet)"
    )
    
    # Number of simulations
    n_sims = st.sidebar.select_slider(
        "🔢 Number of Simulations",
        options=[1000, 2500, 5000, 10000, 20000],
        value=5000,
        help="More simulations = more accurate but slower"
    )
    
    # Grid override option
    use_grid_override = st.sidebar.checkbox(
        "🏁 Use Actual Grid Positions",
        value=False,
        help="Override predicted grid with actual qualifying results"
    )
    
    grid_overrides = {}
    if use_grid_override:
        st.sidebar.info("Enter grid positions as driver_code:position (e.g., VER:1, HAM:2)")
        grid_input = st.sidebar.text_area(
            "Grid Override",
            placeholder="VER:1\nHAM:2\nRUS:3",
            height=100
        )
        
        if grid_input:
            try:
                for line in grid_input.strip().split('\n'):
                    if ':' in line:
                        driver, pos = line.strip().split(':')
                        grid_overrides[driver.strip()] = int(pos.strip())
            except ValueError:
                st.sidebar.error("Invalid format. Use: DRIVER:POSITION per line")
    
    # Run prediction button
    col1, col2 = st.columns([3, 1])
    with col2:
        run_button = st.button("🚀 Run Prediction", type="primary", use_container_width=True)
    
    if run_button:
        with st.spinner(f"Running {n_sims:,} Monte Carlo simulations..."):
            try:
                # Create prediction request
                request = PredictionRequest(
                    circuit_id=circuit_id,
                    rain_probability=rain_prob,
                    n_simulations=n_sims,
                    seed=None,  # Non-deterministic for variety
                    grid_overrides=grid_overrides
                )
                
                # Run prediction
                result = run_predict(request)
                
                # Display results
                display_predictions(result, selected_circuit, rain_prob, n_sims)
                
            except Exception as e:
                st.error(f"Prediction failed: {str(e)}")
                st.exception(e)
    else:
        # Show example/placeholder
        st.info("👈 Configure settings in the sidebar and click 'Run Prediction' to see results!")
        
        # Show circuit info
        try:
            circuit = get_circuit(circuit_id)
            if circuit:
                st.markdown("### Selected Circuit Info")
                col1, col2, col3 = st.columns(3)
                col1.metric("Safety Car Probability", f"{circuit.get('safety_car_probability', 0.5)*100:.0f}%")
                col2.metric("Typical Rain Probability", f"{circuit.get('rain_probability_typical', 0.2)*100:.0f}%")
                col3.metric("Lap Count", circuit.get('lap_count', 'N/A'))
        except:
            pass


def display_predictions(result: Dict, circuit_name: str, rain_prob: float, n_sims: int):
    """Display prediction results with visualizations."""
    
    st.success(f"✅ Prediction complete! ({n_sims:,} simulations)")
    
    # Header with circuit info
    st.markdown(f"### 📊 {circuit_name} - Race Predictions")
    st.caption(f"Rain probability: {rain_prob*100:.0f}% | Simulations: {n_sims:,}")
    
    predictions = result.get('predictions', [])
    
    if not predictions:
        st.warning("No predictions available.")
        return
    
    # Convert to DataFrame
    df = pd.DataFrame(predictions)
    
    # Sort by predicted position
    df = df.sort_values('predicted_position')
    
    # Display metrics for top 3
    st.markdown("#### 🏆 Predicted Podium")
    col1, col2, col3 = st.columns(3)
    
    top3 = df.head(3)
    medals = ['🥇', '🥈', '🥉']
    
    for idx, (_, row) in enumerate(top3.iterrows()):
        with [col1, col2, col3][idx]:
            st.metric(
                label=f"{medals[idx]} {row['driver']}",
                value=f"{row['win_pct']:.1f}% Win",
                delta=f"P{row['predicted_position']}"
            )
    
    # Main prediction table
    st.markdown("#### Full Results")
    
    # Format the dataframe for display
    display_df = df[['predicted_position', 'driver', 'team', 'win_pct', 
                     'top3_pct', 'top10_pct', 'dnf_pct', 'confidence']].copy()
    display_df.columns = ['Pos', 'Driver', 'Team', 'Win %', 'Podium %', 
                          'Points %', 'DNF %', 'Confidence']
    
    # Style the table
    st.dataframe(
        display_df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Pos": st.column_config.NumberColumn(format="%d"),
            "Win %": st.column_config.ProgressColumn(
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Podium %": st.column_config.ProgressColumn(
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "Points %": st.column_config.ProgressColumn(
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
            "DNF %": st.column_config.ProgressColumn(
                format="%.1f%%",
                min_value=0,
                max_value=100,
            ),
        }
    )
    
    # Visualizations
    st.markdown("---")
    st.markdown("### 📈 Visualizations")
    
    tab1, tab2, tab3 = st.tabs(["Win & Podium Probabilities", "DNF Risk Analysis", "Position Distribution"])
    
    with tab1:
        # Win and Podium probabilities bar chart
        top10 = df.head(10)
        
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Win Probability',
            x=top10['driver'],
            y=top10['win_pct'],
            marker_color='#FF1801'
        ))
        
        fig.add_trace(go.Bar(
            name='Podium Probability',
            x=top10['driver'],
            y=top10['top3_pct'],
            marker_color='#15154e'
        ))
        
        fig.update_layout(
            title="Top 10 Drivers - Win vs Podium Probabilities",
            xaxis_title="Driver",
            yaxis_title="Probability (%)",
            barmode='group',
            height=500,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab2:
        # DNF risk analysis
        dnf_df = df.sort_values('dnf_pct', ascending=False).head(10)
        
        fig = px.bar(
            dnf_df,
            x='driver',
            y='dnf_pct',
            color='dnf_pct',
            color_continuous_scale=['green', 'yellow', 'red'],
            title="Highest DNF Risk Drivers",
            labels={'driver': 'Driver', 'dnf_pct': 'DNF Probability (%)'}
        )
        
        fig.update_layout(
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    with tab3:
        # Position distribution for top drivers
        top5 = df.head(5)
        
        fig = go.Figure()
        
        for _, row in top5.iterrows():
            # This would need position_distribution data from the prediction engine
            # For now, showing a simplified version
            fig.add_trace(go.Bar(
                name=row['driver'],
                x=[f"P{row['predicted_position']}"],
                y=[row['win_pct']],
            ))
        
        fig.update_layout(
            title="Expected Finishing Positions (Top 5)",
            xaxis_title="Position",
            yaxis_title="Win Probability (%)",
            barmode='group',
            height=400,
            template='plotly_white'
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # Key insights
    st.markdown("---")
    st.markdown("### 💡 Key Insights")
    
    insights_col1, insights_col2 = st.columns(2)
    
    with insights_col1:
        st.markdown("**Most Likely Winner:**")
        winner = df.iloc[0]
        st.write(f"- **{winner['driver']}** ({winner['team']})")
        st.write(f"- Win probability: {winner['win_pct']:.1f}%")
        st.write(f"- Confidence: {winner['confidence']}")
    
    with insights_col2:
        st.markdown("**Biggest Surprise Potential:**")
        # Find drivers outside top 5 with decent top10 chances
        surprises = df[(df['predicted_position'] > 5) & (df['top10_pct'] > 30)]
        if not surprises.empty:
            surprise = surprises.iloc[0]
            st.write(f"- **{surprise['driver']}** could finish P{surprise['predicted_position']}")
            st.write(f"- Points probability: {surprise['top10_pct']:.1f}%")
        else:
            st.write("No major surprises predicted")
    
    # Download results
    st.markdown("---")
    csv = display_df.to_csv(index=False)
    st.download_button(
        label="📥 Download Results as CSV",
        data=csv,
        file_name=f"{circuit_name.replace(' ', '_')}_predictions.csv",
        mime="text/csv"
    )
