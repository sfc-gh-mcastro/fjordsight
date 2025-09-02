"""
AI Sales Co-Pilot for FjordSight PoC
Provides intelligent sales recommendations based on production scenarios
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
import sys
import os

# Add parent directories to path to handle different execution contexts
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
grandparent_dir = os.path.dirname(parent_dir)
sys.path.append(parent_dir)
sys.path.append(grandparent_dir)

from config import Config

# Try relative import first, then absolute import
try:
    from .data_loader import DataLoader
except ImportError:
    from data_loader import DataLoader

class SalesCoPilot:
    """AI-powered sales recommendation system"""
    
    def __init__(self):
        self.config = Config()
        self.data_loader = DataLoader()
        self.logger = logging.getLogger(__name__)
        
        # Load customer data
        self.customers_df = self.data_loader.load_customer_data()
        
        # Scoring weights for recommendation algorithm
        self.scoring_weights = {
            'profitability': 0.3,
            'relationship': 0.25,
            'volume_match': 0.2,
            'product_preference': 0.15,
            'purchase_timing': 0.1
        }
    
    def calculate_customer_score(self, customer: pd.Series, scenario_params: Dict) -> Dict:
        """Calculate a comprehensive score for each customer based on the scenario"""
        
        scores = {}
        
        # Profitability Score (0-1)
        profitability_map = {'HIGH': 1.0, 'MEDIUM': 0.6, 'LOW': 0.3}
        scores['profitability'] = profitability_map.get(customer['PROFITABILITY_TIER'], 0.3)
        
        # Relationship Score (already 0-5, normalize to 0-1)
        scores['relationship'] = min(customer['RELATIONSHIP_SCORE'] / 5.0, 1.0)
        
        # Volume Match Score - how well does available volume match their typical order
        available_volume = scenario_params['available_volume']
        typical_volume = customer['AVERAGE_ORDER_SIZE_KG']
        
        if available_volume <= typical_volume * 1.2:
            # Good match - they can take most/all of the volume
            scores['volume_match'] = 1.0 - abs(available_volume - typical_volume) / typical_volume
        else:
            # Too much volume for them - partial match
            scores['volume_match'] = typical_volume / available_volume
        
        scores['volume_match'] = max(0.1, scores['volume_match'])  # Minimum score
        
        # Product Preference Score
        preferred_products = customer['PREFERRED_PRODUCTS']
        product_type = scenario_params['product_type']
        
        if isinstance(preferred_products, list):
            if product_type in preferred_products:
                scores['product_preference'] = 1.0
            elif any(pref in product_type or product_type in pref for pref in preferred_products):
                scores['product_preference'] = 0.7  # Partial match
            else:
                scores['product_preference'] = 0.3  # No match but still possible
        else:
            scores['product_preference'] = 0.5  # Default if data is unclear
        
        # Purchase Timing Score - based on when they last ordered vs their frequency
        last_order_date = customer['LAST_ORDER_DATE']
        frequency_days = customer['PURCHASE_FREQUENCY_DAYS']
        
        if isinstance(last_order_date, str):
            last_order_date = pd.to_datetime(last_order_date)
        
        days_since_last_order = (datetime.now() - last_order_date).days
        
        if days_since_last_order >= frequency_days * 0.8:
            scores['purchase_timing'] = 1.0  # Due for an order
        elif days_since_last_order >= frequency_days * 0.5:
            scores['purchase_timing'] = 0.7  # Could be interested
        else:
            scores['purchase_timing'] = 0.3  # Recently ordered
        
        # Calculate weighted total score
        total_score = sum(scores[key] * self.scoring_weights[key] for key in scores)
        
        return {
            'individual_scores': scores,
            'total_score': total_score
        }
    
    def calculate_recommended_volume(self, customer: pd.Series, available_volume: float, scenario_type: str) -> float:
        """Calculate the recommended volume to offer to this customer"""
        
        typical_volume = customer['AVERAGE_ORDER_SIZE_KG']
        risk_tolerance = customer['RISK_TOLERANCE']
        
        if scenario_type == "surplus":
            # We have extra volume - try to sell more than usual
            if risk_tolerance == 'HIGH':
                # High risk tolerance customers might take 20-50% more
                multiplier = np.random.uniform(1.2, 1.5)
            elif risk_tolerance == 'MEDIUM':
                # Medium risk tolerance - 10-30% more
                multiplier = np.random.uniform(1.1, 1.3)
            else:
                # Low risk tolerance - stick close to usual
                multiplier = np.random.uniform(1.0, 1.1)
            
            recommended = min(typical_volume * multiplier, available_volume)
            
        else:  # shortfall
            # We have less volume - prioritize based on relationship and profitability
            if customer['PROFITABILITY_TIER'] == 'HIGH' and customer['RELATIONSHIP_SCORE'] >= 4.0:
                # Top customers get priority - offer up to their usual amount
                recommended = min(typical_volume, available_volume)
            else:
                # Others get reduced amounts
                recommended = min(typical_volume * 0.8, available_volume)
        
        return max(50, recommended)  # Minimum 50kg order
    
    def calculate_expected_revenue(self, customer: pd.Series, volume: float, product_type: str) -> float:
        """Calculate expected revenue from this customer"""
        
        # Base price per kg based on product type and customer tier
        base_prices = {
            'Premium Atlantic Salmon': 16.0,
            'Standard Atlantic Salmon': 12.0,
            'Organic Salmon': 18.0,
            'Smoked Salmon': 25.0,
            'Whole Fish': 10.0,
            'Frozen Fillets': 11.0
        }
        
        base_price = base_prices.get(product_type, 12.0)
        
        # Adjust price based on customer tier and price sensitivity
        if customer['PROFITABILITY_TIER'] == 'HIGH':
            price_multiplier = 1.0  # Premium customers pay full price
        elif customer['PROFITABILITY_TIER'] == 'MEDIUM':
            price_multiplier = 0.95  # Small discount
        else:
            price_multiplier = 0.90  # Larger discount for low-tier customers
        
        # Further adjust for price sensitivity
        price_sensitivity = customer['PRICE_SENSITIVITY']
        price_multiplier *= (1.0 - price_sensitivity * 0.1)  # Up to 10% additional discount
        
        final_price = base_price * price_multiplier
        return volume * final_price
    
    def generate_recommendation_reasons(self, customer: pd.Series, scores: Dict, scenario_params: Dict) -> List[str]:
        """Generate human-readable reasons for the recommendation"""
        
        reasons = []
        individual_scores = scores['individual_scores']
        
        # Profitability reasons
        if individual_scores['profitability'] >= 0.8:
            reasons.append(f"High profitability tier customer ({customer['PROFITABILITY_TIER']})")
        elif individual_scores['profitability'] >= 0.5:
            reasons.append(f"Medium profitability customer with good margins")
        
        # Relationship reasons
        if individual_scores['relationship'] >= 0.8:
            reasons.append(f"Excellent relationship score ({customer['RELATIONSHIP_SCORE']:.1f}/5)")
        elif individual_scores['relationship'] >= 0.6:
            reasons.append(f"Good relationship history ({customer['RELATIONSHIP_SCORE']:.1f}/5)")
        
        # Volume match reasons
        if individual_scores['volume_match'] >= 0.8:
            reasons.append("Volume matches their typical order size well")
        elif individual_scores['volume_match'] >= 0.5:
            reasons.append("Can accommodate a reasonable portion of available volume")
        
        # Product preference reasons
        if individual_scores['product_preference'] >= 0.8:
            reasons.append(f"Strong preference for {scenario_params['product_type']}")
        elif individual_scores['product_preference'] >= 0.6:
            reasons.append("Product aligns with their preferences")
        
        # Timing reasons
        if individual_scores['purchase_timing'] >= 0.8:
            reasons.append("Due for their next regular order")
        elif individual_scores['purchase_timing'] >= 0.6:
            reasons.append("Good timing for additional purchase")
        
        # Risk tolerance reasons
        if scenario_params['scenario_type'] == 'surplus' and customer['RISK_TOLERANCE'] == 'HIGH':
            reasons.append("High risk tolerance - likely to accept extra volume")
        elif scenario_params['scenario_type'] == 'shortfall' and customer['PROFITABILITY_TIER'] == 'HIGH':
            reasons.append("Priority customer for limited volume allocation")
        
        return reasons[:4]  # Return top 4 reasons
    
    def generate_recommendations(self, available_volume: float, product_type: str, scenario_type: str = "surplus") -> List[Dict]:
        """Generate ranked sales recommendations"""
        
        if self.customers_df.empty:
            self.logger.warning("No customer data available")
            return []
        
        scenario_params = {
            'available_volume': available_volume,
            'product_type': product_type,
            'scenario_type': scenario_type
        }
        
        recommendations = []
        
        for _, customer in self.customers_df.iterrows():
            try:
                # Calculate scores
                scoring_result = self.calculate_customer_score(customer, scenario_params)
                
                # Calculate recommended volume and revenue
                recommended_volume = self.calculate_recommended_volume(customer, available_volume, scenario_type)
                expected_revenue = self.calculate_expected_revenue(customer, recommended_volume, product_type)
                
                # Calculate probability of success
                base_probability = scoring_result['total_score']
                
                # Adjust probability based on scenario
                if scenario_type == "surplus":
                    # Harder to sell extra volume
                    probability = base_probability * 0.8
                else:
                    # Easier to sell limited volume to good customers
                    probability = min(base_probability * 1.2, 1.0)
                
                # Generate reasons
                reasons = self.generate_recommendation_reasons(customer, scoring_result, scenario_params)
                
                recommendation = {
                    'customer_id': customer['CUSTOMER_ID'],
                    'customer_name': customer['CUSTOMER_NAME'],
                    'customer_type': customer['CUSTOMER_TYPE'],
                    'location': customer['LOCATION'],
                    'recommended_volume': recommended_volume,
                    'expected_revenue': expected_revenue,
                    'probability': probability,
                    'profitability_tier': customer['PROFITABILITY_TIER'],
                    'relationship_score': customer['RELATIONSHIP_SCORE'],
                    'risk_tolerance': customer['RISK_TOLERANCE'],
                    'total_score': scoring_result['total_score'],
                    'individual_scores': scoring_result['individual_scores'],
                    'reasons': reasons,
                    'expected_profit_margin': 0.25 + (0.1 if customer['PROFITABILITY_TIER'] == 'HIGH' else 0),
                    'confidence_level': min(probability * 1.2, 1.0)
                }
                
                recommendations.append(recommendation)
                
            except Exception as e:
                self.logger.error(f"Error processing customer {customer.get('CUSTOMER_NAME', 'Unknown')}: {e}")
                continue
        
        # Sort by total score * expected revenue (prioritize high-value opportunities)
        recommendations.sort(key=lambda x: x['total_score'] * x['expected_revenue'], reverse=True)
        
        return recommendations
    
    def simulate_call_outcome(self, customer_id: str, recommended_volume: float) -> Dict:
        """Simulate the outcome of a sales call (for demo purposes)"""
        
        customer = self.customers_df[self.customers_df['CUSTOMER_ID'] == customer_id].iloc[0]
        
        # Simulate call outcome based on customer characteristics
        base_success_rate = min(customer['RELATIONSHIP_SCORE'] / 5.0, 0.9)
        
        if customer['RISK_TOLERANCE'] == 'HIGH':
            success_rate = base_success_rate * 1.1
        elif customer['RISK_TOLERANCE'] == 'LOW':
            success_rate = base_success_rate * 0.8
        else:
            success_rate = base_success_rate
        
        success = np.random.random() < success_rate
        
        if success:
            # They accept, but might negotiate volume
            accepted_volume = recommended_volume * np.random.uniform(0.8, 1.0)
            outcome = "ACCEPTED"
            message = f"Great news! {customer['CUSTOMER_NAME']} accepted {accepted_volume:.0f} kg"
        else:
            # They decline or want to negotiate
            if np.random.random() < 0.3:
                outcome = "NEGOTIATION"
                message = f"{customer['CUSTOMER_NAME']} is interested but wants to negotiate terms"
            else:
                outcome = "DECLINED"
                reasons = ["Not needed right now", "Budget constraints", "Already have inventory", "Quality concerns"]
                reason = np.random.choice(reasons)
                message = f"{customer['CUSTOMER_NAME']} declined: {reason}"
            accepted_volume = 0
        
        return {
            'customer_name': customer['CUSTOMER_NAME'],
            'outcome': outcome,
            'accepted_volume': accepted_volume,
            'message': message,
            'call_timestamp': datetime.now().isoformat()
        }
    
    def get_customer_insights(self, customer_id: str) -> Dict:
        """Get detailed insights about a specific customer"""
        
        if self.customers_df.empty:
            return {}
        
        customer = self.customers_df[self.customers_df['CUSTOMER_ID'] == customer_id]
        
        if customer.empty:
            return {}
        
        customer = customer.iloc[0]
        
        # Calculate some insights
        days_since_last_order = (datetime.now() - pd.to_datetime(customer['LAST_ORDER_DATE'])).days
        
        insights = {
            'customer_name': customer['CUSTOMER_NAME'],
            'customer_type': customer['CUSTOMER_TYPE'],
            'location': customer['LOCATION'],
            'profitability_tier': customer['PROFITABILITY_TIER'],
            'relationship_score': customer['RELATIONSHIP_SCORE'],
            'total_lifetime_value': customer['TOTAL_LIFETIME_VALUE'],
            'average_order_size': customer['AVERAGE_ORDER_SIZE_KG'],
            'average_order_value': customer['AVERAGE_ORDER_VALUE'],
            'purchase_frequency': customer['PURCHASE_FREQUENCY_DAYS'],
            'days_since_last_order': days_since_last_order,
            'risk_tolerance': customer['RISK_TOLERANCE'],
            'price_sensitivity': customer['PRICE_SENSITIVITY'],
            'preferred_products': customer['PREFERRED_PRODUCTS'],
            'order_due_status': 'OVERDUE' if days_since_last_order > customer['PURCHASE_FREQUENCY_DAYS'] * 1.2 
                               else 'DUE' if days_since_last_order >= customer['PURCHASE_FREQUENCY_DAYS'] * 0.8 
                               else 'NOT_DUE'
        }
        
        return insights

if __name__ == "__main__":
    # Test the sales co-pilot
    copilot = SalesCoPilot()
    
    # Test surplus scenario
    recommendations = copilot.generate_recommendations(
        available_volume=500,
        product_type="Premium Atlantic Salmon",
        scenario_type="surplus"
    )
    
    print("Top 3 Sales Recommendations:")
    for i, rec in enumerate(recommendations[:3], 1):
        print(f"\n{i}. {rec['customer_name']}")
        print(f"   Volume: {rec['recommended_volume']:.0f} kg")
        print(f"   Revenue: ${rec['expected_revenue']:,.0f}")
        print(f"   Probability: {rec['probability']:.0%}")
        print(f"   Score: {rec['total_score']:.2f}")
        print(f"   Reasons: {', '.join(rec['reasons'])}")
