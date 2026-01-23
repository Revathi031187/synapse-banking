"""
Unit Tests for Micro Segmentation and Recommendations

Tests the core functionality of:
- Micro segmentation creation
- Product recommendations (similar, segment-based, search)
- Business constraint validation
"""

import pytest
import pandas as pd
import numpy as np
from agents.agent_a_academy_micro import AgentA_Academy_Micro
from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced


class TestMicroSegmentation:
    """Tests for micro segmentation agent"""
    
    @pytest.fixture
    def sample_customers_df(self):
        """Create sample customer data for testing"""
        return pd.DataFrame({
            'customer_id': [f'CUST_{i:05d}' for i in range(1, 101)],
            'cluster': [0] * 50 + [1] * 50,
            'search_specificity': np.random.uniform(1, 5, 100),
            'spec_expansion_rate': np.random.uniform(0, 1, 100),
            'bundle_affinity': np.random.uniform(0, 1, 100),
            'price_sort_frequency': np.random.uniform(0, 1, 100),
            'total_spend_12mo': np.random.uniform(100, 2000, 100),
            'purchase_frequency': np.random.randint(1, 15, 100),
            'avg_order_value': np.random.uniform(50, 500, 100),
            'recency_days': np.random.randint(1, 365, 100),
            'dominant_category': np.random.choice(['Tents', 'Sleeping Bags', 'Backpacks'], 100),
            'brand_loyalty': np.random.choice(['None', 'Coleman', 'Big Agnes'], 100),
            'return_rate': np.random.uniform(0, 0.3, 100)
        })
    
    @pytest.fixture
    def sample_personas(self):
        """Create sample persona definitions"""
        return {
            0: {
                'persona_name': '🏕️ First-Time Camper',
                'short_name': 'Novice',
                'size': 50,
                'percentage': 50.0
            },
            1: {
                'persona_name': '⛰️ Seasoned Pro',
                'short_name': 'Pro',
                'size': 50,
                'percentage': 50.0
            }
        }
    
    def test_micro_agent_initialization(self, sample_customers_df, sample_personas):
        """Test that micro agent initializes correctly"""
        agent = AgentA_Academy_Micro(sample_customers_df, sample_personas)
        assert agent.customers_df is not None
        assert agent.macro_personas is not None
        assert len(agent.macro_personas) == 2
    
    def test_micro_segmentation_execution(self, sample_customers_df, sample_personas):
        """Test that micro segmentation executes without errors"""
        agent = AgentA_Academy_Micro(sample_customers_df, sample_personas)
        result = agent.execute(macro_segment_id=0, n_micro_segments=3)
        
        assert result['status'] == 'success'
        assert 'micro_segments' in result
        assert len(result['micro_segments']) <= 3
        assert result['macro_segment_id'] == 0
    
    def test_micro_features_calculation(self, sample_customers_df, sample_personas):
        """Test that micro features are calculated correctly"""
        agent = AgentA_Academy_Micro(sample_customers_df, sample_personas)
        
        macro_customers = sample_customers_df[sample_customers_df['cluster'] == 0]
        features = agent._calculate_micro_features(macro_customers)
        
        assert 'brand_loyalty_score' in features.columns
        assert 'expertise_level' in features.columns
        assert 'ltv_tier' in features.columns
        assert 'category_focus' in features.columns
        
        # Check value ranges
        assert features['brand_loyalty_score'].between(0, 1).all()
        assert features['expertise_level'].between(0, 1).all()
        assert features['ltv_tier'].isin([0, 1, 2, 3]).all()
    
    def test_all_macro_segments_execution(self, sample_customers_df, sample_personas):
        """Test executing micro segmentation for all macro segments"""
        agent = AgentA_Academy_Micro(sample_customers_df, sample_personas)
        result = agent.execute_all_macro_segments(n_micro_segments=3)
        
        assert result['status'] == 'success'
        assert result['total_macro_segments'] == 2
        assert result['total_micro_segments'] >= 4  # At least 2 micro per macro


class TestRecommendations:
    """Tests for product recommendation agent"""
    
    @pytest.fixture
    def sample_products_df(self):
        """Create sample product data"""
        return pd.DataFrame({
            'product_id': [f'PROD_{i:05d}' for i in range(1, 51)],
            'product_name': [f'Product {i}' for i in range(1, 51)],
            'brand': np.random.choice(['Coleman', 'Big Agnes', 'MSR'], 50),
            'main_category': np.random.choice(['Tents', 'Sleeping Bags', 'Backpacks'], 50),
            'subcategory': np.random.choice(['Instant Tents', 'Dome Tents', 'Mummy Bags'], 50),
            'price': np.random.uniform(50, 500, 50),
            'in_stock': [True] * 50,
            'avg_rating': np.random.uniform(3.5, 5.0, 50),
            'num_reviews': np.random.randint(10, 500, 50)
        })
    
    @pytest.fixture
    def sample_customers_for_rec_df(self):
        """Create sample customer data for recommendations"""
        return pd.DataFrame({
            'customer_id': [f'CUST_{i:05d}' for i in range(1, 21)],
            'cluster': [0] * 10 + [1] * 10,
            'avg_order_value': np.random.uniform(100, 300, 20),
            'total_spend_12mo': np.random.uniform(500, 2000, 20)
        })
    
    @pytest.fixture
    def sample_purchases_df(self):
        """Create sample purchase data"""
        purchases = []
        for i in range(1, 21):
            n_purchases = np.random.randint(2, 8)
            for _ in range(n_purchases):
                purchases.append({
                    'purchase_id': f'PUR_{len(purchases):06d}',
                    'customer_id': f'CUST_{i:05d}',
                    'product_id': f'PROD_{np.random.randint(1, 51):05d}',
                    'price_paid': np.random.uniform(50, 400)
                })
        return pd.DataFrame(purchases)
    
    def test_recommendation_agent_initialization(
        self, 
        sample_customers_for_rec_df, 
        sample_products_df, 
        sample_purchases_df
    ):
        """Test that recommendation agent initializes correctly"""
        agent = AgentB_Academy_Enhanced(
            sample_customers_for_rec_df,
            sample_products_df,
            sample_purchases_df
        )
        assert agent.customers_df is not None
        assert agent.products_df is not None
        assert agent.purchases_df is not None
    
    def test_similar_products_recommendation(
        self,
        sample_customers_for_rec_df,
        sample_products_df,
        sample_purchases_df
    ):
        """Test similar products recommendation logic"""
        agent = AgentB_Academy_Enhanced(
            sample_customers_for_rec_df,
            sample_products_df,
            sample_purchases_df
        )
        
        result = agent.get_similar_products('CUST_00001', n_recommendations=3)
        
        assert result['customer_id'] == 'CUST_00001'
        assert result['type'] == 'similar_products'
        assert 'recommendations' in result
        assert 'price_range' in result
        
        # Check recommendation structure
        if len(result['recommendations']) > 0:
            rec = result['recommendations'][0]
            assert 'product_id' in rec
            assert 'product_name' in rec
            assert 'price' in rec
            assert 'reason' in rec
    
    def test_segment_based_recommendation(
        self,
        sample_customers_for_rec_df,
        sample_products_df,
        sample_purchases_df
    ):
        """Test segment-based recommendation logic"""
        agent = AgentB_Academy_Enhanced(
            sample_customers_for_rec_df,
            sample_products_df,
            sample_purchases_df
        )
        
        result = agent.get_segment_recommendations('CUST_00001')
        
        assert result['customer_id'] == 'CUST_00001'
        assert result['type'] == 'segment_based'
        assert 'recommendations' in result
        assert 'segment_type' in result
    
    def test_search_recommendation_fallback(
        self,
        sample_customers_for_rec_df,
        sample_products_df,
        sample_purchases_df
    ):
        """Test search-based recommendation with keyword fallback"""
        agent = AgentB_Academy_Enhanced(
            sample_customers_for_rec_df,
            sample_products_df,
            sample_purchases_df
        )
        
        result = agent.get_search_recommendations(
            'CUST_00001',
            'tent',
            chromadb_collection=None  # No ChromaDB, use fallback
        )
        
        assert result['customer_id'] == 'CUST_00001'
        assert result['search_term'] == 'tent'
        assert result['type'] == 'search_based'
        assert result['method'] == 'keyword_search'


class TestBusinessConstraints:
    """Tests for business constraint validation"""
    
    def test_constraint_validation_all_met(self):
        """Test constraint validation when all constraints are met"""
        from agents.agent_a_academy_chromadb import AgentA_Academy
        
        # This would require full integration test with actual data
        # Placeholder for structure
        pass
    
    def test_constraint_validation_size_violated(self):
        """Test constraint validation when size constraint is violated"""
        # Placeholder
        pass
    
    def test_constraint_validation_revenue_violated(self):
        """Test constraint validation when revenue constraint is violated"""
        # Placeholder
        pass


# Run tests with: pytest tests/test_micro_segmentation.py -v

