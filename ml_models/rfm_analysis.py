"""
RFM (Recency, Frequency, Monetary) Analysis Module
Implements customer segmentation based on purchase behavior
"""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any, Tuple
from utils.logger import get_logger

logger = get_logger("RFM")


class RFMAnalysis:
    """RFM Analysis for customer segmentation."""
    
    def __init__(self):
        logger.info("💰 RFM Analysis module initialized")
    
    def calculate_rfm(
        self, 
        transactions_df: pd.DataFrame,
        customer_id_col: str = 'customer_id',
        date_col: str = 'transaction_date',
        amount_col: str = 'total_amount',
        reference_date: datetime = None
    ) -> pd.DataFrame:
        """
        Calculate RFM scores for each customer.
        """
        logger.info("📊 Calculating RFM scores...")
        
        df = transactions_df.copy()
        
        # Convert date column to datetime with error handling
        try:
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            # Drop rows with invalid dates
            df = df.dropna(subset=[date_col])
        except Exception as e:
            logger.error(f"Error parsing dates: {e}")
            raise
        
        # Ensure amount is numeric
        df[amount_col] = pd.to_numeric(df[amount_col], errors='coerce')
        df = df.dropna(subset=[amount_col])
        
        # Set reference date
        if reference_date is None:
            reference_date = df[date_col].max() + timedelta(days=1)
        
        # Calculate RFM metrics
        rfm = df.groupby(customer_id_col, as_index=False).agg({
            date_col: lambda x: (reference_date - x.max()).days,  # Recency
            amount_col: ['count', 'sum']  # Frequency and Monetary
        })
        
        # Flatten column names
        rfm.columns = [customer_id_col, 'recency', 'frequency', 'monetary']
        
        logger.info(f"✅ RFM calculated for {len(rfm)} customers")
        return rfm
    
    def score_rfm(self, rfm_df: pd.DataFrame, n_bins: int = 5) -> pd.DataFrame:
        """Score RFM metrics into bins (1-5, where 5 is best)."""
        logger.info(f"🏆 Scoring RFM into {n_bins} bins...")
        
        df = rfm_df.copy()
        
        try:
            # Score Recency (lower is better, so reverse)
            df['r_score'] = pd.qcut(
                df['recency'], 
                q=n_bins, 
                labels=range(n_bins, 0, -1), 
                duplicates='drop'
            ).astype(int)
        except Exception as e:
            logger.warning(f"Could not qcut recency, using simple binning: {e}")
            df['r_score'] = pd.cut(df['recency'], bins=n_bins, labels=range(n_bins, 0, -1), duplicates='drop').astype(int)
        
        try:
            # Score Frequency (higher is better)
            df['f_score'] = pd.qcut(
                df['frequency'], 
                q=n_bins, 
                labels=range(1, n_bins + 1), 
                duplicates='drop'
            ).astype(int)
        except Exception as e:
            logger.warning(f"Could not qcut frequency, using simple binning: {e}")
            df['f_score'] = pd.cut(df['frequency'], bins=n_bins, labels=range(1, n_bins + 1), duplicates='drop').astype(int)
        
        try:
            # Score Monetary (higher is better)
            df['m_score'] = pd.qcut(
                df['monetary'], 
                q=n_bins, 
                labels=range(1, n_bins + 1), 
                duplicates='drop'
            ).astype(int)
        except Exception as e:
            logger.warning(f"Could not qcut monetary, using simple binning: {e}")
            df['m_score'] = pd.cut(df['monetary'], bins=n_bins, labels=range(1, n_bins + 1), duplicates='drop').astype(int)
        
        # Fill any NaN scores with middle value
        df['r_score'] = df['r_score'].fillna(3)
        df['f_score'] = df['f_score'].fillna(3)
        df['m_score'] = df['m_score'].fillna(3)
        
        # Combined RFM score
        df['rfm_score'] = df['r_score'].astype(str) + df['f_score'].astype(str) + df['m_score'].astype(str)
        
        # Overall score (average)
        df['rfm_score_avg'] = (df['r_score'] + df['f_score'] + df['m_score']) / 3
        
        logger.info("✅ RFM scored successfully")
        return df
    
    def segment_customers(self, rfm_scored_df: pd.DataFrame) -> pd.DataFrame:
        """
        Segment customers based on RFM scores into meaningful segments.
        
        Args:
            rfm_scored_df: DataFrame with RFM scores
            
        Returns:
            DataFrame with segment labels
        """
        logger.info("🎯 Segmenting customers based on RFM...")
        
        df = rfm_scored_df.copy()
        
        def get_segment(row):
            """Determine segment based on RFM scores."""
            r, f, m = row['r_score'], row['f_score'], row['m_score']
            
            # Champions: Bought recently, buy often, spend the most
            if r >= 4 and f >= 4 and m >= 4:
                return 'Champions'
            
            # Loyal Customers: Spend good money, responsive to promotions
            elif r >= 3 and f >= 3 and m >= 3:
                return 'Loyal Customers'
            
            # Potential Loyalists: Recent customers, spent good amount, bought more than once
            elif r >= 4 and f <= 3 and m >= 3:
                return 'Potential Loyalists'
            
            # New Customers: Bought recently, but not often
            elif r >= 4 and f <= 2:
                return 'New Customers'
            
            # At Risk: Spent big money, purchased often but long time ago
            elif r <= 2 and f >= 3 and m >= 3:
                return 'At Risk'
            
            # Can't Lose Them: Made big purchases and often, but long time ago
            elif r <= 2 and f >= 4 and m >= 4:
                return "Can't Lose Them"
            
            # Hibernating: Last purchase was long ago, low spenders
            elif r <= 2 and f <= 2 and m <= 2:
                return 'Hibernating'
            
            # Price Sensitive: Recent buyers, low frequency and monetary
            elif r >= 3 and f <= 2 and m <= 2:
                return 'Price Sensitive'
            
            # Default
            else:
                return 'Needs Attention'
        
        df['rfm_segment'] = df.apply(get_segment, axis=1)
        
        # Calculate segment statistics
        segment_stats = df.groupby('rfm_segment').agg({
            'customer_id': 'count',
            'recency': 'mean',
            'frequency': 'mean',
            'monetary': 'mean',
            'rfm_score_avg': 'mean'
        }).reset_index()
        
        segment_stats.columns = ['segment', 'count', 'avg_recency', 'avg_frequency', 'avg_monetary', 'avg_score']
        segment_stats['percentage'] = (segment_stats['count'] / len(df) * 100).round(2)
        
        logger.info(f"✅ Segmented into {len(segment_stats)} segments")
        logger.info(f"Segments: {segment_stats['segment'].tolist()}")
        
        return df, segment_stats
    
    def get_rfm_features(self, rfm_df: pd.DataFrame) -> pd.DataFrame:
        """
        Get normalized RFM features for clustering.
        
        Args:
            rfm_df: DataFrame with RFM metrics
            
        Returns:
            DataFrame with normalized features
        """
        features = rfm_df[['recency', 'frequency', 'monetary']].copy()
        
        # Log transform monetary and frequency to handle skewness
        features['log_frequency'] = np.log1p(features['frequency'])
        features['log_monetary'] = np.log1p(features['monetary'])
        
        return features


# Global instance
rfm_analyzer = RFMAnalysis()

