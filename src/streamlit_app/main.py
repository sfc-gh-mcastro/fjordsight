"""
FjordSight Digital Farm Command Center
Streamlit application for monitoring salmon farms and AI-powered insights
"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import json
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from models.hab_prediction_model import HABPredictionModel
from streamlit_app.sales_copilot import SalesCoPilot
from streamlit_app.data_loader import DataLoader

# Page configuration
st.set_page_config(
    page_title="FjordSight Digital Farm Command Center",
    page_icon="🐟",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #1f77b4, #17a2b8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin: 0.5rem 0;
    }
    .risk-high {
        background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-medium {
        background: linear-gradient(135deg, #feca57 0%, #ff9ff3 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .risk-low {
        background: linear-gradient(135deg, #48dbfb 0%, #0abde3 100%);
        color: white;
        padding: 0.5rem;
        border-radius: 5px;
        font-weight: bold;
    }
    .sidebar .sidebar-content {
        background: linear-gradient(180deg, #667eea 0%, #764ba2 100%);
    }
</style>
""", unsafe_allow_html=True)

class FjordSightApp:
    """Main Streamlit application class"""
    
    def __init__(self):
        self.config = Config()
        self.data_loader = DataLoader()
        self.hab_model = HABPredictionModel()
        self.sales_copilot = SalesCoPilot()
        
        # Initialize session state
        if 'selected_farm' not in st.session_state:
            st.session_state.selected_farm = self.config.FARM_LOCATIONS[0]['name']
        if 'alert_threshold' not in st.session_state:
            st.session_state.alert_threshold = self.config.HAB_RISK_THRESHOLD
        if 'auto_refresh' not in st.session_state:
            st.session_state.auto_refresh = False
    
    def render_header(self):
        """Render the main header"""
        st.markdown('<h1 class="main-header">🐟 FjordSight Digital Farm Command Center</h1>', 
                   unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.markdown("*Real-time monitoring and AI-powered insights for sustainable salmon farming*")
    
    def render_sidebar(self):
        """Render the sidebar with controls"""
        st.sidebar.markdown("## 🎛️ Control Panel")
        
        # Farm selection
        st.session_state.selected_farm = st.sidebar.selectbox(
            "Select Farm Location",
            [loc['name'] for loc in self.config.FARM_LOCATIONS],
            index=[loc['name'] for loc in self.config.FARM_LOCATIONS].index(st.session_state.selected_farm)
        )
        
        # Alert threshold
        st.session_state.alert_threshold = st.sidebar.slider(
            "HAB Risk Alert Threshold",
            0.0, 1.0, st.session_state.alert_threshold, 0.1
        )
        
        # Auto refresh
        st.session_state.auto_refresh = st.sidebar.checkbox(
            "Auto Refresh (30s)", st.session_state.auto_refresh
        )
        
        # Time range selection
        time_range = st.sidebar.selectbox(
            "Data Time Range",
            ["Last 1 Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days"],
            index=2
        )
        
        return time_range
    
    def get_time_filter(self, time_range: str) -> int:
        """Convert time range to hours"""
        mapping = {
            "Last 1 Hour": 1,
            "Last 6 Hours": 6,
            "Last 24 Hours": 24,
            "Last 7 Days": 168
        }
        return mapping.get(time_range, 24)
    
    def render_kpi_metrics(self, farm_data: pd.DataFrame):
        """Render key performance indicators"""
        st.markdown("## 📊 Real-time Farm Metrics")
        
        if farm_data.empty:
            st.warning("No recent data available for selected farm")
            return
        
        # Get latest values
        latest = farm_data.iloc[-1] if len(farm_data) > 0 else None
        
        if latest is None:
            st.warning("No data available")
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            temp = latest.get('WATER_TEMP_C', 0)
            temp_delta = (temp - farm_data['WATER_TEMP_C'].mean()) if 'WATER_TEMP_C' in farm_data.columns else 0
            st.metric(
                "Water Temperature",
                f"{temp:.1f}°C",
                delta=f"{temp_delta:.1f}°C"
            )
        
        with col2:
            oxygen = latest.get('OXYGEN_MG_L', 0)
            oxygen_delta = (oxygen - farm_data['OXYGEN_MG_L'].mean()) if 'OXYGEN_MG_L' in farm_data.columns else 0
            st.metric(
                "Dissolved Oxygen",
                f"{oxygen:.1f} mg/L",
                delta=f"{oxygen_delta:.1f} mg/L"
            )
        
        with col3:
            ph = latest.get('PH_LEVEL', 0)
            ph_delta = (ph - farm_data['PH_LEVEL'].mean()) if 'PH_LEVEL' in farm_data.columns else 0
            st.metric(
                "pH Level",
                f"{ph:.1f}",
                delta=f"{ph_delta:.1f}"
            )
        
        with col4:
            fish_count = latest.get('FISH_COUNT', 0)
            mortality_rate = latest.get('MORTALITY_RATE', 0) * 100
            st.metric(
                "Fish Population",
                f"{fish_count:,}",
                delta=f"Mortality: {mortality_rate:.2f}%"
            )
    
    def render_hab_risk_panel(self):
        """Render HAB risk assessment panel"""
        st.markdown("## 🚨 HAB Risk Assessment - v2")
        
        # Get HAB prediction
        try:
            prediction = self.hab_model.predict_hab_risk(st.session_state.selected_farm)
            with st.expander("Debug: View Raw Prediction Data"):
                st.json(prediction)
        except Exception as e:
            st.error(f"HAB model error: {e}")
            prediction = None
        
        if prediction and 'error' not in prediction:
            col1, col2 = st.columns([1, 2])
            
            with col1:
                risk_score = prediction['risk_score']
                risk_level = prediction['risk_level']
                
                # Risk gauge
                fig_gauge = go.Figure(go.Indicator(
                    mode = "gauge+number+delta",
                    value = risk_score,
                    domain = {'x': [0, 1], 'y': [0, 1]},
                    title = {'text': "HAB Risk Score"},
                    delta = {'reference': st.session_state.alert_threshold},
                    gauge = {
                        'axis': {'range': [None, 1]},
                        'bar': {'color': "darkblue"},
                        'steps': [
                            {'range': [0, 0.3], 'color': "lightgreen"},
                            {'range': [0.3, 0.7], 'color': "yellow"},
                            {'range': [0.7, 1], 'color': "red"}
                        ],
                        'threshold': {
                            'line': {'color': "red", 'width': 4},
                            'thickness': 0.75,
                            'value': st.session_state.alert_threshold
                        }
                    }
                ))
                fig_gauge.update_layout(height=300)
                st.plotly_chart(fig_gauge, use_container_width=True)
                
                # Risk level display
                risk_class = f"risk-{risk_level.lower()}"
                st.markdown(f'<div class="{risk_class}">Risk Level: {risk_level}</div>', 
                           unsafe_allow_html=True)
            
            with col2:
                # Contributing factors
                st.markdown("### Contributing Factors")
                factors = prediction.get('contributing_factors', [])
                if factors:
                    for factor in factors:
                        st.markdown(f"• {factor}")
                else:
                    st.markdown("• No significant risk factors detected")
                
                # Recommendations
                st.markdown("### Recommendations")
                recommendations = prediction.get('recommendations', [])
                for i, rec in enumerate(recommendations, 1):
                    st.markdown(f"{i}. {rec}")
                
                # Anomaly detection
                if prediction.get('anomaly_detected'):
                    st.error("⚠️ Anomalous conditions detected!")
                
            # Alert if risk is high
            if risk_score > st.session_state.alert_threshold:
                st.error(f"🚨 HIGH RISK ALERT: HAB risk score ({risk_score:.2f}) exceeds threshold ({st.session_state.alert_threshold:.2f})")
        
        else:
            st.error("Unable to load HAB risk prediction")
    
    def render_sensor_charts(self, farm_data: pd.DataFrame):
        """Render sensor data charts"""
        st.markdown("## 📈 Environmental Monitoring")
        
        if farm_data.empty:
            st.warning("No sensor data available")
            return
        
        # Create subplots
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=('Water Temperature', 'Dissolved Oxygen', 'pH Level', 'Turbidity'),
            vertical_spacing=0.08
        )
        
        # Water Temperature
        fig.add_trace(
            go.Scatter(x=farm_data['TIMESTAMP'], y=farm_data['WATER_TEMP_C'],
                      mode='lines', name='Water Temp (°C)', line=dict(color='#1f77b4')),
            row=1, col=1
        )
        
        # Dissolved Oxygen
        fig.add_trace(
            go.Scatter(x=farm_data['TIMESTAMP'], y=farm_data['OXYGEN_MG_L'],
                      mode='lines', name='Oxygen (mg/L)', line=dict(color='#ff7f0e')),
            row=1, col=2
        )
        
        # pH Level
        fig.add_trace(
            go.Scatter(x=farm_data['TIMESTAMP'], y=farm_data['PH_LEVEL'],
                      mode='lines', name='pH', line=dict(color='#2ca02c')),
            row=2, col=1
        )
        
        # Turbidity
        fig.add_trace(
            go.Scatter(x=farm_data['TIMESTAMP'], y=farm_data['TURBIDITY_NTU'],
                      mode='lines', name='Turbidity (NTU)', line=dict(color='#d62728')),
            row=2, col=2
        )
        
        fig.update_layout(height=600, showlegend=False)
        fig.update_xaxes(title_text="Time")
        st.plotly_chart(fig, use_container_width=True)
    
    def render_production_metrics(self, farm_data: pd.DataFrame):
        """Render production and business metrics"""
        st.markdown("## 🏭 Production Metrics")
        
        if farm_data.empty:
            st.warning("No production data available")
            return
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Growth rate over time
            fig_growth = px.line(
                farm_data, x='TIMESTAMP', y='GROWTH_RATE_PERCENT',
                title='Growth Rate Trend',
                labels={'GROWTH_RATE_PERCENT': 'Growth Rate (%)', 'TIMESTAMP': 'Time'}
            )
            fig_growth.update_traces(line_color='#2ca02c')
            st.plotly_chart(fig_growth, use_container_width=True)
        
        with col2:
            # Feed conversion ratio
            fig_fcr = px.line(
                farm_data, x='TIMESTAMP', y='FEED_CONVERSION_RATIO',
                title='Feed Conversion Ratio',
                labels={'FEED_CONVERSION_RATIO': 'FCR', 'TIMESTAMP': 'Time'}
            )
            fig_fcr.update_traces(line_color='#ff7f0e')
            st.plotly_chart(fig_fcr, use_container_width=True)
        
        # Production summary
        col3, col4, col5 = st.columns(3)
        
        with col3:
            avg_weight = farm_data['AVERAGE_WEIGHT_KG'].iloc[-1] if 'AVERAGE_WEIGHT_KG' in farm_data.columns else 0
            st.metric("Average Fish Weight", f"{avg_weight:.1f} kg")
        
        with col4:
            feed_inventory = farm_data['FEED_INVENTORY_KG'].iloc[-1] if 'FEED_INVENTORY_KG' in farm_data.columns else 0
            st.metric("Feed Inventory", f"{feed_inventory:,.0f} kg")
        
        with col5:
            growth_rate = farm_data['GROWTH_RATE_PERCENT'].iloc[-1] if 'GROWTH_RATE_PERCENT' in farm_data.columns else 0
            st.metric("Current Growth Rate", f"{growth_rate:.1f}%")
    
    def render_sales_copilot(self):
        """Render AI Sales Co-Pilot interface"""
        st.markdown("## 🤖 AI Sales Co-Pilot")
        
        # Scenario input
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.markdown("### Scenario: Prediction Error Occurred")
            st.markdown("*A harvested salmon batch has a different volume than predicted. Use AI to find the best customers to call.*")
            
            predicted_volume = st.number_input("Predicted Volume (kg)", value=1000.0, step=50.0)
            actual_volume = st.number_input("Actual Volume (kg)", value=1200.0, step=50.0)
            product_type = st.selectbox("Product Type", ["Premium Atlantic Salmon", "Standard Atlantic Salmon", "Organic Salmon"])
        
        with col2:
            volume_diff = actual_volume - predicted_volume
            if volume_diff > 0:
                st.success(f"Surplus: +{volume_diff:.0f} kg")
                st.markdown("**Opportunity**: Maximize profit from extra volume")
            else:
                st.error(f"Shortfall: {volume_diff:.0f} kg")
                st.markdown("**Challenge**: Minimize impact of reduced volume")
        
        if st.button("Generate Sales Recommendations", type="primary"):
            recommendations = self.sales_copilot.generate_recommendations(
                available_volume=abs(volume_diff),
                product_type=product_type,
                scenario_type="surplus" if volume_diff > 0 else "shortfall"
            )
            
            if recommendations:
                st.markdown("### 📞 Top Customer Recommendations")
                
                for i, rec in enumerate(recommendations[:3], 1):
                    with st.expander(f"#{i} - {rec['customer_name']} (Score: {rec['total_score']:.2f})"):
                        col_a, col_b = st.columns(2)
                        
                        with col_a:
                            st.metric("Recommended Volume", f"{rec['recommended_volume']:.0f} kg")
                            st.metric("Expected Revenue", f"${rec['expected_revenue']:,.0f}")
                            st.metric("Probability", f"{rec['probability']:.0%}")
                        
                        with col_b:
                            st.metric("Profitability Tier", rec['profitability_tier'])
                            st.metric("Relationship Score", f"{rec['relationship_score']:.1f}/5")
                            st.metric("Risk Level", rec['risk_tolerance'])
                        
                        st.markdown("**Why this customer:**")
                        for reason in rec['reasons']:
                            st.markdown(f"• {reason}")
                        
                        if st.button(f"Call {rec['customer_name']}", key=f"call_{i}"):
                            st.success(f"📞 Calling {rec['customer_name']}...")
                            # In a real app, this would integrate with CRM/phone system
            else:
                st.warning("No recommendations available")
    
    def render_farm_map(self):
        """Render interactive farm locations map"""
        st.markdown("## 🗺️ Farm Locations")
        
        # Create map data
        map_data = pd.DataFrame([
            {
                'name': loc['name'],
                'lat': loc['lat'],
                'lon': loc['lon'],
                'selected': loc['name'] == st.session_state.selected_farm
            }
            for loc in self.config.FARM_LOCATIONS
        ])
        
        # Create map
        fig_map = px.scatter_mapbox(
            map_data, 
            lat="lat", 
            lon="lon", 
            hover_name="name",
            color="selected",
            size_max=15,
            zoom=6,
            height=400
        )
        
        fig_map.update_layout(
            mapbox_style="open-street-map",
            margin={"r":0,"t":0,"l":0,"b":0}
        )
        
        st.plotly_chart(fig_map, use_container_width=True)
    
    def run(self):
        """Main application runner"""
        # Render components
        self.render_header()
        time_range = self.render_sidebar()
        
        # Load data
        hours_back = self.get_time_filter(time_range)
        farm_data = self.data_loader.load_farm_data(
            st.session_state.selected_farm, 
            hours_back
        )
        
        # Main content tabs
        tab1, tab2, tab3, tab4 = st.tabs(["🏠 Dashboard", "🚨 HAB Risk", "🤖 Sales Co-Pilot", "🗺️ Farm Map"])
        
        with tab1:
            self.render_kpi_metrics(farm_data)
            st.divider()
            self.render_sensor_charts(farm_data)
            st.divider()
            self.render_production_metrics(farm_data)
        
        with tab2:
            self.render_hab_risk_panel()
        
        with tab3:
            self.render_sales_copilot()
        
        with tab4:
            self.render_farm_map()
        
        # Auto-refresh (disabled by default to prevent issues)
        if st.session_state.auto_refresh:
            import time
            time.sleep(30)  # Wait 30 seconds before refresh
            st.rerun()

if __name__ == "__main__":
    app = FjordSightApp()
    app.run()
