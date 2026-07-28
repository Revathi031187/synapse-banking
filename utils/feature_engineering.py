"""Feature engineering utilities for customer segmentation."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List


class FeatureEngineer:
    """Feature engineering for customer behavior analysis."""
    
    def __init__(self):
        self.reference_date = datetime.now()
    
    def compute_rfm_features(self, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Compute RFM (Recency, Frequency, Monetary) features."""
        # Convert transaction_date to datetime if string
        if transactions_df['transaction_date'].dtype == 'object':
            transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
        
        rfm = transactions_df.groupby('customer_id').agg({
            'transaction_date': lambda x: (self.reference_date - pd.to_datetime(x.max())).days,  # Recency
            'transaction_id': 'count',  # Frequency
            'total_amount': 'sum'  # Monetary
        }).reset_index()
        
        rfm.columns = ['customer_id', 'recency_days', 'frequency', 'monetary_value']
        
        # Add derived features
        rfm['avg_transaction_value'] = rfm['monetary_value'] / rfm['frequency']
        
        return rfm
    
    def compute_behavioral_features(
        self, 
        transactions_df: pd.DataFrame,
        behavioral_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Compute behavioral features from transactions and events."""
        features_list = []
        
        # Transaction-based features
        if not transactions_df.empty:
            trans_features = transactions_df.groupby('customer_id').agg({
                'product_id': 'nunique',  # Product diversity
                'channel': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'web',  # Preferred channel
                'discount_pct': 'mean',  # Avg discount sensitivity
                'is_returned': 'mean',  # Return rate
                'customer_rating': lambda x: x.dropna().mean() if x.dropna().shape[0] > 0 else 3.5
            }).reset_index()
            
            trans_features.columns = [
                'customer_id', 'product_diversity', 'preferred_channel',
                'avg_discount_pct', 'return_rate', 'avg_rating'
            ]
            features_list.append(trans_features)
        
        # Behavioral event features
        if not behavioral_df.empty:
            behavioral_df['timestamp'] = pd.to_datetime(behavioral_df['timestamp'])
            
            behavior_features = behavioral_df.groupby('customer_id').agg({
                'event_id': 'count',  # Total events
                'session_id': 'nunique',  # Number of sessions
                'device': lambda x: x.mode()[0] if len(x.mode()) > 0 else 'desktop',
                'duration_seconds': lambda x: x.dropna().mean() if x.dropna().shape[0] > 0 else 0
            }).reset_index()
            
            behavior_features.columns = [
                'customer_id', 'total_events', 'num_sessions',
                'preferred_device', 'avg_session_duration'
            ]
            
            # Add event type counts
            event_pivot = behavioral_df.pivot_table(
                index='customer_id',
                columns='event_type',
                values='event_id',
                aggfunc='count',
                fill_value=0
            ).reset_index()
            
            behavior_features = behavior_features.merge(event_pivot, on='customer_id', how='left')
            features_list.append(behavior_features)
        
        # Merge all features
        if len(features_list) > 1:
            result = features_list[0]
            for df in features_list[1:]:
                result = result.merge(df, on='customer_id', how='outer')
            return result.fillna(0)
        elif len(features_list) == 1:
            return features_list[0]
        else:
            return pd.DataFrame()
    
    def detect_intent(self, behavioral_df: pd.DataFrame, transactions_df: pd.DataFrame) -> pd.DataFrame:
        """Detect customer intent based on recent behavior."""
        intent_data = []
        
        # Get recent behavior (last 30 days)
        cutoff_date = self.reference_date - timedelta(days=30)
        
        if not behavioral_df.empty:
            behavioral_df['timestamp'] = pd.to_datetime(behavioral_df['timestamp'])
            recent_behavior = behavioral_df[behavioral_df['timestamp'] >= cutoff_date]
        else:
            recent_behavior = pd.DataFrame()
        
        if not transactions_df.empty:
            transactions_df['transaction_date'] = pd.to_datetime(transactions_df['transaction_date'])
            recent_transactions = transactions_df[transactions_df['transaction_date'] >= cutoff_date]
        else:
            recent_transactions = pd.DataFrame()
        
        # Determine all unique customers
        all_customers = set()
        if not behavioral_df.empty:
            all_customers.update(behavioral_df['customer_id'].unique())
        if not transactions_df.empty:
            all_customers.update(transactions_df['customer_id'].unique())
        
        for customer_id in all_customers:
            # Get customer's recent behavior
            cust_behavior = recent_behavior[recent_behavior['customer_id'] == customer_id] if not recent_behavior.empty else pd.DataFrame()
            cust_transactions = recent_transactions[recent_transactions['customer_id'] == customer_id] if not recent_transactions.empty else pd.DataFrame()
            
            # Intent logic
            intent = "dormant"  # Default
            confidence = 0.5
            
            if not cust_behavior.empty:
                add_to_cart_count = (cust_behavior['event_type'] == 'add_to_cart').sum()
                product_view_count = (cust_behavior['event_type'] == 'product_view').sum()
                
                if add_to_cart_count > 0 and cust_transactions.empty:
                    intent = "abandoned_cart"
                    confidence = 0.85
                elif product_view_count > 10:
                    intent = "comparison_shopping"
                    confidence = 0.75
                elif product_view_count > 0:
                    intent = "exploring"
                    confidence = 0.65
            
            if not cust_transactions.empty:
                if len(cust_transactions) >= 3:
                    intent = "loyalty"
                    confidence = 0.90
                elif len(cust_transactions) >= 1:
                    intent = "ready_to_buy"
                    confidence = 0.80
            
            intent_data.append({
                'customer_id': customer_id,
                'intent': intent,
                'intent_confidence': confidence
            })
        
        return pd.DataFrame(intent_data)
    
    def create_feature_matrix(
        self,
        customers_df: pd.DataFrame,
        transactions_df: pd.DataFrame,
        behavioral_df: pd.DataFrame
    ) -> pd.DataFrame:
        """Create complete feature matrix for all customers."""
        # Compute RFM
        rfm_features = self.compute_rfm_features(transactions_df)
        
        # Compute behavioral features
        behavioral_features = self.compute_behavioral_features(transactions_df, behavioral_df)
        
        # Detect intent
        intent_features = self.detect_intent(behavioral_df, transactions_df)
        
        # Merge all features with customer base
        feature_matrix = customers_df[['customer_id', 'life_event', 'income_range', 'loyalty_tier']].copy()
        
        feature_matrix = feature_matrix.merge(rfm_features, on='customer_id', how='left')
        feature_matrix = feature_matrix.merge(behavioral_features, on='customer_id', how='left')
        feature_matrix = feature_matrix.merge(intent_features, on='customer_id', how='left')
        
        # Fill missing values
        feature_matrix = feature_matrix.fillna({
            'recency_days': 365,
            'frequency': 0,
            'monetary_value': 0,
            'avg_transaction_value': 0,
            'product_diversity': 0,
            'intent': 'dormant',
            'intent_confidence': 0.5
        })
        
        return feature_matrix

