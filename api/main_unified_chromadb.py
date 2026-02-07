"""
Multi-Industry NBA Platform API
K-Prototypes clustering + feature-based personalization

Endpoints:
- /api/academy/* - All Academy Sports endpoints
- /api/banking/* - All Banking endpoints (NEW)
- /api/chromadb/stats - Get ChromaDB statistics
"""
import sys
import os

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import traceback
from datetime import datetime
import pandas as pd
import numpy as np

# Import logger
from utils.logger import get_logger
logger = get_logger("API_Academy")

# Import Academy Sports agents only
from agents.agent_a_academy_enhanced import AgentA_Academy_Enhanced
from agents.agent_b_academy_chromadb import AgentB_Academy
from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced
from agents.agent_b_logit_enhanced import AgentB_LogitEnhanced
from agents.agent_b_nested_logit import AgentB_NestedLogit

# Import ChromaDB client
from utils.chromadb_client import get_chroma_client

# Initialize FastAPI
app = FastAPI(title="Academy Sports NBA Platform API", version="4.0.0")

# Global variable to track Academy Sports dataset version and cached data
academy_dataset_version = "v1"  # Default to V1
academy_cached_data = {
    'customers_df': None,
    'interactions_df': None,
    'purchases_df': None,
    'products_df': None,
    'loaded': False,
    'version': None
}

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Academy agents need correct path (relative to project root, not api dir)
from pathlib import Path
project_root = Path(__file__).parent.parent
academy_data_path = project_root / 'data' / 'preloaded' / 'academy_sports'
# Use the ENHANCED agent with business constraints and dynamic clustering
academy_agent_a = AgentA_Academy_Enhanced(data_path=str(academy_data_path))
academy_agent_b = AgentB_Academy(data_path=str(academy_data_path), agent_a=academy_agent_a)

# F&M Bank agents
from agents.agent_a_banking_enhanced import AgentA_Banking_Enhanced
from agents.agent_b_banking_enhanced_v2 import AgentB_Banking_Enhanced
from agents.agent_b_banking_chromadb import AgentB_Banking  # Rule-based chromadb agent
from agents.agent_b_banking_logit_enhanced import AgentB_Banking_LogitEnhanced  # Hybrid ML agent
from agents.agent_b_banking_enhanced import AgentB_Banking_Enhanced as AgentB_Banking_Modal  # Customer modal agent

fmb_data_path = project_root / 'data' / 'preloaded' / 'fmb_bank'  # F&M Bank data
banking_agent_a = AgentA_Banking_Enhanced(data_path=str(fmb_data_path))
banking_agent_b = None  # Lazy init after Agent A runs
banking_agent_b_chromadb = None  # Rule-based agent (lazy init)
banking_agent_b_logit = None  # Hybrid ML agent (lazy init)
banking_agent_b_modal = None  # Customer modal agent (lazy init)

def init_banking_agent_b():
    """Initialize Banking Agent B after Agent A has created personas"""
    global banking_agent_b, banking_agent_b_chromadb, banking_agent_b_logit, banking_agent_b_modal
    if banking_agent_b is None and system_state['banking']['agent_a_results']:
        try:
            # Legacy agent
            banking_agent_b = AgentB_Banking_Enhanced(
                customers_df=banking_agent_a.customers_df,
                products_df=banking_agent_a.products_df,
                transactions_df=banking_agent_a.transactions_df,
                personas=banking_agent_a.personas
            )
            
            # Rule-based chromadb agent
            banking_agent_b_chromadb = AgentB_Banking(
                data_path=str(fmb_data_path),
                agent_a=banking_agent_a
            )
            
            # Hybrid ML agent
            banking_agent_b_logit = AgentB_Banking_LogitEnhanced(
                products_df=banking_agent_a.products_df,
                customers_df=banking_agent_a.customers_df,
                transactions_df=banking_agent_a.transactions_df,
                personas=banking_agent_a.personas
            )
            
            # Customer modal agent
            banking_agent_b_modal = AgentB_Banking_Modal(
                customers_df=banking_agent_a.customers_df,
                products_df=banking_agent_a.products_df,
                transactions_df=banking_agent_a.transactions_df,
                personas=banking_agent_a.personas
            )
            
            logger.info("✅ All Banking Agent B variants initialized with persona data")
        except Exception as e:
            logger.error(f"Error initializing Banking Agent B: {e}")
            raise

chroma_client = get_chroma_client()

# System state - Academy Sports and Banking
system_state = {
    'academy': {
        'agent_a_results': None,
        'agent_b_results': None,
        'agent_b_logit_results': None,
        'agent_b_nested_logit_results': None,
        'academy_micro_segments': {}
    },
    'banking': {
        'agent_a_results': None,
        'agent_b_results': None,
        'banking_micro_segments': {}
    }
}


# ============================================================================
# REQUEST MODELS - Academy Sports Only
# ============================================================================
class AgentAConfigAcademy(BaseModel):
    n_clusters: int = 3
    gamma: float = 0.5


class AgentBConfigAcademy(BaseModel):
    customer_id: Optional[str] = None  # Optional: for customer-specific recommendations
    persona: Optional[str] = None  # Required if no customer_id
    search_query: Optional[str] = ''
    category: Optional[str] = None
    top_n: int = 10
    explain: bool = True


class AgentBLogitConfig(BaseModel):
    customer_id: Optional[str] = None
    persona: Optional[str] = None
    search_query: Optional[str] = ''
    category: Optional[str] = None
    top_n: int = 10
    mode: str = "hybrid_weighted"  # logit_only, hybrid_average, hybrid_weighted


class InitializeRequest(BaseModel):
    dataset_path: Optional[str] = None
    n_clusters: int = 5


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_dataset_file_path(filename: str) -> str:
    """Get the correct file path based on loaded dataset version"""
    global academy_dataset_version
    
    # Map base filename to versioned filename
    base_name, ext = filename.rsplit('.', 1)
    
    if academy_dataset_version == "v2":
        versioned_filename = f"{base_name}_v2.{ext}"
    else:
        versioned_filename = filename
    
    return f'data/preloaded/academy_sports/{versioned_filename}'


def preload_academy_data(dataset_version: str, max_retries: int = 3):
    """
    Preload Academy Sports data with retry logic and caching
    
    Args:
        dataset_version: 'v1' or 'v2'
        max_retries: Maximum number of retry attempts
    
    Returns:
        Dict with status and loaded dataframes
    """
    import pandas as pd
    import time
    from pathlib import Path
    
    global academy_cached_data, academy_dataset_version
    
    # Check if already loaded for this version
    if (academy_cached_data['loaded'] and 
        academy_cached_data['version'] == dataset_version and
        academy_cached_data['customers_df'] is not None):
        logger.info(f"✅ Using cached data for {dataset_version}")
        return {
            'success': True,
            'cached': True,
            'customer_count': len(academy_cached_data['customers_df']),
            'product_count': len(academy_cached_data['products_df']) if academy_cached_data['products_df'] is not None else 0
        }
    
    project_root = Path(__file__).parent.parent
    data_path = project_root / 'data' / 'preloaded' / 'academy_sports'
    
    # Determine file paths
    if dataset_version == 'v2':
        customers_file = data_path / 'customers_v2.csv'
        interactions_file = data_path / 'interactions_v2.csv'
        purchases_file = data_path / 'purchases_v2.csv'
    else:
        customers_file = data_path / 'customers.csv'
        interactions_file = data_path / 'interactions.csv'
        purchases_file = data_path / 'purchases.csv'
    
    products_file = data_path / 'products.csv'  # Shared across versions
    
    # Retry logic with exponential backoff
    for attempt in range(max_retries):
        try:
            logger.info(f"📂 Preloading Academy Sports {dataset_version} data (attempt {attempt + 1}/{max_retries})...")
            
            # Check files exist
            required_files = [customers_file, interactions_file, purchases_file, products_file]
            missing_files = [f for f in required_files if not f.exists()]
            
            if missing_files:
                logger.error(f"❌ Missing files: {[f.name for f in missing_files]}")
                return {
                    'success': False,
                    'error': f"Missing required files: {[f.name for f in missing_files]}",
                    'attempt': attempt + 1
                }
            
            # Load all files with retry
            logger.info(f"   Loading {customers_file.name}...")
            customers_df = pd.read_csv(customers_file)
            
            logger.info(f"   Loading {interactions_file.name}...")
            interactions_df = pd.read_csv(interactions_file)
            
            logger.info(f"   Loading {purchases_file.name}...")
            purchases_df = pd.read_csv(purchases_file)
            
            logger.info(f"   Loading {products_file.name}...")
            products_df = pd.read_csv(products_file)
            
            # Validate data
            if len(customers_df) == 0:
                raise ValueError("Customers file is empty")
            if len(products_df) == 0:
                raise ValueError("Products file is empty")
            
            # Cache the data
            academy_cached_data['customers_df'] = customers_df
            academy_cached_data['interactions_df'] = interactions_df
            academy_cached_data['purchases_df'] = purchases_df
            academy_cached_data['products_df'] = products_df
            academy_cached_data['loaded'] = True
            academy_cached_data['version'] = dataset_version
            
            # Update global version
            academy_dataset_version = dataset_version
            
            logger.info(f"✅ Successfully preloaded {dataset_version}:")
            logger.info(f"   - {len(customers_df):,} customers")
            logger.info(f"   - {len(interactions_df):,} interactions")
            logger.info(f"   - {len(purchases_df):,} purchases")
            logger.info(f"   - {len(products_df):,} products")
            
            return {
                'success': True,
                'cached': False,
                'customer_count': len(customers_df),
                'interaction_count': len(interactions_df),
                'purchase_count': len(purchases_df),
                'product_count': len(products_df),
                'attempt': attempt + 1
            }
            
        except Exception as e:
            logger.error(f"❌ Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                wait_time = (2 ** attempt) * 0.5  # Exponential backoff: 0.5s, 1s, 2s
                logger.info(f"⏳ Retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                logger.error(f"❌ All {max_retries} attempts failed")
                return {
                    'success': False,
                    'error': str(e),
                    'attempt': attempt + 1
                }
    
    return {
        'success': False,
        'error': 'Max retries exceeded',
        'attempt': max_retries
    }


def numpy_to_python_types(obj):
    """Recursively convert numpy types to Python native types"""
    import numpy as np
    import pandas as pd
    import math
    
    # Handle pandas DataFrame
    if isinstance(obj, pd.DataFrame):
        # Convert DataFrame to dict and then recursively process
        return numpy_to_python_types(obj.to_dict('records'))
    
    # Handle pandas Series
    elif isinstance(obj, pd.Series):
        return numpy_to_python_types(obj.tolist())
    
    elif isinstance(obj, dict):
        return {str(key): numpy_to_python_types(value) for key, value in obj.items()}
    
    elif isinstance(obj, list):
        return [numpy_to_python_types(item) for item in obj]
    
    elif isinstance(obj, (np.int64, np.int32, np.int16, np.int8, np.uint64, np.uint32, np.uint16, np.uint8)):
        return int(obj)
    
    elif isinstance(obj, (np.float64, np.float32, np.float16)):
        val = float(obj)
        if math.isinf(val) or math.isnan(val):
            return None
        return val
    
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    elif isinstance(obj, np.ndarray):
        return numpy_to_python_types(obj.tolist())
    
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    
    elif isinstance(obj, int):
        return int(obj)
    
    else:
        return obj


# ============================================================================
# GENERAL ENDPOINTS
# ============================================================================
@app.get("/")
async def root():
    """API root - health check"""
    return {
        "name": "Academy Sports NBA Platform API",
        "version": "4.0.0",
        "status": "operational",
        "industry": "Academy Sports - Camping Gear",
        "docs": "/docs"
    }


@app.get("/api/config/together-api-key")
async def get_together_api_key():
    """Get Together AI API key from environment variables"""
    api_key = os.getenv('TOGETHER_API_KEY', '')
    return {
        "api_key": api_key,
        "configured": bool(api_key and api_key != 'your_together_api_key_here')
    }


@app.get("/api/industries")
async def list_industries():
    """List available industries - Academy Sports and Banking"""
    return {
        "industries": [
            {
                "id": "academy",
                "name": "Academy Sports - Camping Gear",
                "description": "K-Prototypes clustering + feature-based personalization for camping products",
                "icon": "🏕️",
                "use_cases": ["Persona Identification", "Feature-Based Recommendations", "Micro-Segmentation"]
            },
            {
                "id": "banking",
                "name": "Banking Platform",
                "description": "K-Prototypes clustering + personalized product recommendations for banking customers",
                "icon": "🏦",
                "use_cases": ["Customer Segmentation", "Product Recommendations", "Cross-Sell & Up-Sell", "Churn Prediction"]
            }
        ]
    }


# ============================================================================
# ACADEMY SPORTS ENDPOINTS
# ============================================================================
@app.get("/api/academy/datasets")
async def list_academy_datasets():
    """List available Academy Sports datasets - Both V1 and V2"""
    import pandas as pd
    from pathlib import Path
    
    try:
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "preloaded" / "academy_sports"
        
        logger.info(f"📂 Checking for datasets in: {data_path}")
        
        # Create directory if it doesn't exist
        data_path.mkdir(parents=True, exist_ok=True)
        
        datasets = []
        
        # Check what files actually exist
        if data_path.exists():
            csv_files = list(data_path.glob("*.csv"))
            logger.info(f"📄 Found CSV files: {[f.name for f in csv_files]}")
        
        # V1 Dataset (Original)
        customers_v1 = data_path / "customers.csv"
        products_v1 = data_path / "products.csv"
        purchases_v1 = data_path / "purchases.csv"
        
        if customers_v1.exists():
            try:
                customers_df = pd.read_csv(customers_v1)
                customer_count = len(customers_df)
                
                product_count = 57  # Default
                if products_v1.exists():
                    products_df = pd.read_csv(products_v1)
                    product_count = len(products_df)
                
                purchase_count = 0
                if purchases_v1.exists():
                    purchases_df = pd.read_csv(purchases_v1)
                    purchase_count = len(purchases_df)
                
                datasets.append({
                    "name": "academy_sports_v1",
                    "display_name": "Academy Sports V1 (Original)",
                    "version": "v1",
                    "description": f"Original dataset with {customer_count} customers and rich behavioral data",
                    "tables": ["customers", "products", "purchases", "feature_affinity", "interactions"],
                    "loaded": True,
                    "status": "ready",
                    "customer_count": customer_count,
                    "product_count": product_count,
                    "purchase_count": purchase_count,
                    "path": str(data_path)
                })
                logger.info(f"✅ V1 dataset: {customer_count} customers, {product_count} products, {purchase_count} purchases")
            except Exception as e:
                logger.error(f"❌ Error reading V1 dataset: {e}")
        else:
            # Always show V1 as available (even if not generated yet)
            datasets.append({
                "name": "academy_sports_v1",
                "display_name": "Academy Sports V1 (Original)",
                "version": "v1",
                "description": "Original dataset - Generate by running: py -3.10 utils/academy_sports_data_generator_fast.py",
                "tables": ["customers", "products", "purchases", "feature_affinity", "interactions"],
                "loaded": False,
                "status": "not_generated",
                "customer_count": 5000,
                "product_count": 57,
                "path": str(data_path)
            })
            logger.warning(f"⚠️ V1 dataset not found at {customers_v1}")
        
        # V2 Dataset (Balanced)
        customers_v2 = data_path / "customers_v2.csv"
        products_v2 = data_path / "products.csv"  # V2 uses same products
        purchases_v2 = data_path / "purchases_v2.csv"
        
        if customers_v2.exists():
            try:
                customers_df = pd.read_csv(customers_v2)
                customer_count = len(customers_df)
                
                product_count = 57
                if products_v2.exists():
                    products_df = pd.read_csv(products_v2)
                    product_count = len(products_df)
                
                purchase_count = 0
                if purchases_v2.exists():
                    purchases_df = pd.read_csv(purchases_v2)
                    purchase_count = len(purchases_df)
                
                datasets.append({
                    "name": "academy_sports_v2",
                    "display_name": "Academy Sports V2 (Balanced)",
                    "version": "v2",
                    "description": f"Balanced distribution dataset with {customer_count} customers for testing",
                    "tables": ["customers", "products", "purchases", "feature_affinity", "interactions"],
                    "loaded": True,
                    "status": "ready",
                    "customer_count": customer_count,
                    "product_count": product_count,
                    "purchase_count": purchase_count,
                    "path": str(data_path)
                })
                logger.info(f"✅ V2 dataset: {customer_count} customers, {product_count} products, {purchase_count} purchases")
            except Exception as e:
                logger.error(f"❌ Error reading V2 dataset: {e}")
        else:
            # Always show V2 as available (even if not generated yet)
            datasets.append({
                "name": "academy_sports_v2",
                "display_name": "Academy Sports V2 (Balanced)",
                "version": "v2",
                "description": "Balanced distribution dataset - Generate by running: py -3.10 utils/academy_sports_data_generator_fast.py --version v2",
                "tables": ["customers", "products", "purchases", "feature_affinity", "interactions"],
                "loaded": False,
                "status": "not_generated",
                "customer_count": 5000,
                "product_count": 57,
                "path": str(data_path)
            })
            logger.warning(f"⚠️ V2 dataset not found at {customers_v2}")
        
        logger.info(f"📊 Returning {len(datasets)} datasets")
        return {"datasets": datasets}
        
    except Exception as e:
        logger.error(f"❌ Error listing datasets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"datasets": [], "error": str(e)}


@app.post("/api/academy/datasets/load")
async def load_academy_dataset(request: dict):
    """
    Load Academy Sports dataset (V1 or V2) with automatic preloading and retry logic
    """
    global academy_dataset_version
    
    dataset_name = request.get("dataset_name", "academy_sports_v1")
    
    # Extract version from dataset name
    if "v2" in dataset_name:
        version = "v2"
        version_msg = "V2 (Test dataset)"
    else:
        version = "v1"
        version_msg = "V1 (Original dataset)"
    
    logger.info(f"📊 Loading Academy Sports {version_msg}")
    
    # Preload data with retry logic (3 attempts)
    preload_result = preload_academy_data(version, max_retries=3)
    
    if not preload_result['success']:
        error_msg = f"Failed to load dataset after {preload_result.get('attempt', 3)} attempts: {preload_result.get('error', 'Unknown error')}"
        logger.error(f"❌ {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)
    
    logger.info(f"✅ Academy Sports {version_msg} loaded successfully")
    
    return {
        "status": "success",
        "message": f"Academy Sports {version_msg} loaded",
        "dataset": dataset_name,
        "version": version,
        "customer_count": preload_result.get('customer_count', 0),
        "product_count": preload_result.get('product_count', 0),
        "cached": preload_result.get('cached', False),
        "attempts": preload_result.get('attempt', 1)
    }


@app.get("/api/academy/datasets/view/{dataset_name}/{table_name}")
async def view_academy_table(dataset_name: str, table_name: str):
    """View a specific Academy Sports table from CSV files"""
    try:
        import pandas as pd
        from pathlib import Path
        
        # Map dataset name to directory (use absolute path from project root)
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "preloaded" / "academy_sports"
        
        # Determine if V2 dataset
        is_v2 = "v2" in dataset_name.lower()
        
        # Build filename - append _v2 suffix for V2 datasets (except products which is shared)
        if is_v2 and table_name != "products":
            filename = f"{table_name}_v2.csv"
        else:
            filename = f"{table_name}.csv"
        
        file_path = data_path / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found at {file_path}")
        
        df = pd.read_csv(file_path)
        records = df.head(100).to_dict('records')  # Limit to first 100 rows
        
        # Convert types
        records = [numpy_to_python_types(record) for record in records]
        
        return {
            "table_name": table_name,
            "dataset_name": dataset_name,
            "records": records,
            "record_count": len(df),
            "preview_count": len(records)
        }
    except Exception as e:
        logger.error(f"Error viewing table {table_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/dataset-version")
async def get_academy_dataset_version():
    """Get currently selected Academy Sports dataset version"""
    global academy_dataset_version
    return {
        "version": academy_dataset_version,
        "name": f"academy_sports_{academy_dataset_version}"
    }


@app.get("/api/academy/debug/cache-status")
async def get_cache_status():
    """Get current cache status for debugging"""
    global academy_cached_data, academy_dataset_version
    
    return {
        "cache_loaded": academy_cached_data['loaded'],
        "cache_version": academy_cached_data['version'],
        "current_version": academy_dataset_version,
        "customers_loaded": academy_cached_data['customers_df'] is not None,
        "products_loaded": academy_cached_data['products_df'] is not None,
        "purchases_loaded": academy_cached_data['purchases_df'] is not None,
        "customer_count": len(academy_cached_data['customers_df']) if academy_cached_data['customers_df'] is not None else 0,
        "product_count": len(academy_cached_data['products_df']) if academy_cached_data['products_df'] is not None else 0,
        "agent_a_run": system_state['academy']['agent_a_results'] is not None
    }


@app.get("/api/academy/debug/test-recommendations/{customer_id}")
async def test_recommendations(customer_id: str):
    """Debug endpoint to test recommendation generation"""
    try:
        global academy_cached_data, academy_dataset_version
        
        # Ensure data loaded
        if not academy_cached_data['loaded']:
            preload_result = preload_academy_data(academy_dataset_version, max_retries=3)
            if not preload_result['success']:
                return {"error": "Failed to preload data", "details": preload_result}
        
        import pandas as pd
        customers_df = academy_cached_data['customers_df'].copy()
        products_df = academy_cached_data['products_df'].copy()
        purchases_df = academy_cached_data['purchases_df'].copy()
        
        # Check customer exists
        if customer_id not in customers_df['customer_id'].values:
            return {"error": f"Customer {customer_id} not found", "available_customers": customers_df['customer_id'].head(10).tolist()}
        
        # Get customer info
        customer_info = customers_df[customers_df['customer_id'] == customer_id].iloc[0]
        
        # Check purchases
        customer_purchases = purchases_df[purchases_df['customer_id'] == customer_id]
        
        # Initialize Agent B with personas if available
        from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        rec_agent = AgentB_Academy_Enhanced(
            customers_df=customers_df,
            products_df=products_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Test get_similar_products
        similar_result = rec_agent.get_similar_products(customer_id, n_recommendations=3)
        
        # Test get_segment_recommendations
        segment_result = rec_agent.get_segment_recommendations(customer_id, n_recommendations=3)
        
        # Test get_all_recommendations
        all_result = rec_agent.get_all_recommendations(customer_id)
        
        return {
            "success": True,
            "customer_id": customer_id,
            "customer_info": {
                "name": customer_info.get('customer_name', 'N/A'),
                "total_spend": float(customer_info.get('total_spend_12mo', 0)),
                "purchase_frequency": float(customer_info.get('purchase_frequency', 0)),
                "dominant_category": customer_info.get('dominant_category', 'N/A')
            },
            "purchase_count": len(customer_purchases),
            "similar_products_count": len(similar_result.get('recommendations', [])),
            "segment_products_count": len(segment_result.get('recommendations', [])),
            "all_recommendations": {
                "tailored_count": len(all_result.get('tailored_recommendations', [])),
                "similar_count": len(all_result.get('similar_products', [])),
                "segment_count": len(all_result.get('segment_recommendations', []))
            },
            "sample_similar_products": similar_result.get('recommendations', [])[:2],
            "sample_segment_products": segment_result.get('recommendations', [])[:2],
            "similar_result_keys": list(similar_result.keys()),
            "all_result_keys": list(all_result.keys())
        }
        
    except Exception as e:
        logger.error(f"Test recommendations failed: {e}")
        logger.error(traceback.format_exc())
        return {"error": str(e), "traceback": traceback.format_exc()}


@app.get("/api/academy/status")
async def get_academy_status():
    """Get Academy Sports system status"""
    try:
        global academy_dataset_version
        
        # Academy Sports works from CSV files, not ChromaDB
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        
        # Check for the currently selected version
        if academy_dataset_version == 'v2':
            customers_path = project_root / "data" / "preloaded" / "academy_sports" / "customers_v2.csv"
        else:
            customers_path = project_root / "data" / "preloaded" / "academy_sports" / "customers.csv"
        
        data_loaded = customers_path.exists()
        
        if data_loaded:
            import pandas as pd
            df = pd.read_csv(customers_path)
            customer_count = len(df)
        else:
            customer_count = 0
        
        return {
            "data_loaded": data_loaded,
            "current_dataset": f"academy_sports_{academy_dataset_version}",
            "dataset_version": academy_dataset_version,
            "agent_a_complete": False,
            "agent_b_complete": False,
            "customers_count": customer_count,
            "backend": "CSV Files (On-Demand Processing)"
        }
    except Exception as e:
        logger.error(f"Error getting Academy Sports status: {e}")
        return {
            "data_loaded": False,
            "current_dataset": None,
            "dataset_version": "v1",
            "agent_a_complete": False,
            "agent_b_complete": False,
            "customers_count": 0,
            "backend": "CSV Files (On-Demand Processing)"
        }


# ============================================================================
# CHROMADB MANAGEMENT ENDPOINTS
# ============================================================================
@app.get("/api/chromadb/stats")
async def get_chromadb_stats():
    """Get ChromaDB statistics"""
    try:
        collections = chroma_client.list_collections()
        stats = {}
        
        for collection_name in collections:
            collection_stats = chroma_client.collection_stats(collection_name)
            stats[collection_name] = collection_stats
        
        return {
            "total_collections": len(collections),
            "collections": stats
        }
    except Exception as e:
        logger.error(f"Error getting ChromaDB stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chromadb/initialize")
async def initialize_chromadb(request: InitializeRequest, background_tasks: BackgroundTasks):
    """Initialize or refresh ChromaDB data for Academy Sports (runs in background)"""
    def run_initialization():
        try:
            from scripts.initialize_chromadb import ChromaDBInitializer
            initializer = ChromaDBInitializer()
            
            dataset_path = request.dataset_path or "data/preloaded/academy_sports"
            initializer.initialize_academy(dataset_path, request.n_clusters)
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            logger.error(traceback.format_exc())
    
    background_tasks.add_task(run_initialization)
    
    return {
        "message": "Initialization started for Academy Sports",
        "status": "running_in_background",
        "check_status_at": "/api/chromadb/stats"
    }

# ============================================================================
# ACADEMY SPORTS ENDPOINTS
# ============================================================================
@app.post("/api/academy/agent_a/execute")
async def execute_academy_agent_a(config: AgentAConfigAcademy):
    """Execute Academy Sports Agent A - Enhanced with Business Constraints"""
    try:
        logger.info("="*80)
        logger.info(f"🏕️  ACADEMY SPORTS AGENT A - ENHANCED CLUSTERING WITH BUSINESS CONSTRAINTS")
        logger.info(f"   Requested clusters: {config.n_clusters} (will auto-adjust to meet constraints)")
        logger.info("="*80)
        
        # ENSURE DATA IS PRELOADED BEFORE EXECUTION
        global academy_dataset_version, academy_cached_data
        
        # Check if data is already cached for current version
        if not academy_cached_data['loaded'] or academy_cached_data['version'] != academy_dataset_version:
            logger.info(f"⏳ Data not cached, preloading {academy_dataset_version}...")
            preload_result = preload_academy_data(academy_dataset_version, max_retries=3)
            
            if not preload_result['success']:
                error_msg = f"Failed to preload data: {preload_result.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
            
            logger.info(f"✅ Data preloaded successfully")
        else:
            logger.info(f"✅ Using cached data for {academy_dataset_version}")
        
        start_time = datetime.now()
        
        # Execute NEW Enhanced Agent A (with business constraints) - USE USER'S GAMMA
        results = academy_agent_a.execute({
            'dataset_version': academy_dataset_version,
            'n_clusters': config.n_clusters,
            'gamma': config.gamma  # USE USER INPUT, NOT HARDCODED
        })
        
        # Store results
        system_state['academy']['agent_a_results'] = results
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Academy Agent A completed in {execution_time:.2f}s")
        logger.info(f"   Generated {results.get('n_clusters', 0)} personas with business constraints")
        
        # Convert numpy types
        results = numpy_to_python_types(results)
        
        return {
            "success": True,
            "result": results,
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat(),
            "data_cached": academy_cached_data['loaded']
        }
        
    except Exception as e:
        logger.error(f"❌ Academy Agent A failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/academy/agent_a/results")
async def clear_academy_agent_a_results():
    """Clear Academy Sports Agent A results (useful for testing/demos)"""
    system_state['academy']['agent_a_results'] = None
    system_state['academy']['academy_micro_segments'] = {}
    logger.info("🗑️  Cleared all Academy Agent A results and micro segments")
    return {"success": True, "message": "Agent A results cleared"}

@app.get("/api/academy/agent_a/results")
async def get_academy_agent_a_results():
    """Get Academy Sports Agent A results with dynamic data overview"""
    if not system_state['academy']['agent_a_results']:
        raise HTTPException(status_code=404, detail="No Agent A results available. Please execute Agent A first.")
    
    results = system_state['academy']['agent_a_results']
    
    # Add dynamic product catalog information
    try:
        products_df = academy_agent_a.products_df
        if products_df is not None and len(products_df) > 0:
            results['product_count'] = int(len(products_df))
            results['price_range'] = {
                'min': int(products_df['price'].min()),
                'max': int(products_df['price'].max())
            }
            results['brand_count'] = int(products_df['brand'].nunique())
        else:
            results['product_count'] = "1,000+"
            results['price_range'] = {'min': 10, 'max': 500}
            results['brand_count'] = "50+"
    except Exception as e:
        logger.warning(f"Could not get product stats: {e}")
        results['product_count'] = "1,000+"
        results['price_range'] = {'min': 10, 'max': 500}
        results['brand_count'] = "50+"
    
    results = numpy_to_python_types(results)
    return {"success": True, "results": results}


@app.get("/api/academy/personas")
async def list_academy_personas():
    """List all Academy Sports personas"""
    try:
        # Get personas from Agent A results or execute if not available
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        else:
            result = academy_agent_a.execute()
            personas = result.get('personas', {})
            system_state['academy']['agent_a_results'] = result
        
        personas_list = [
            {
                'id': persona['short_name'],
                'name': persona['persona_name'],
                'description': persona['description'],
                'size': persona['size'],
                'percentage': persona['percentage']
            }
            for persona in personas.values()
        ]
        
        return {"success": True, "personas": personas_list}
        
    except Exception as e:
        logger.error(f"Error listing personas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/macro-segments")
async def get_academy_macro_segments():
    """
    Get Academy Sports macro segments with business constraints validation
    
    Returns summary of macro segments with metadata including:
    - Segment details (name, size, revenue)
    - Business constraints validation
    - Special flags (high_value, price_sensitive, etc.)
    - Last refresh timestamp
    """
    try:
        # Get Agent A results
        if not system_state['academy']['agent_a_results']:
            raise HTTPException(status_code=404, detail="No macro segments available. Please execute Agent A first.")
        
        results = system_state['academy']['agent_a_results']
        personas = results.get('personas', {})
        constraints = results.get('constraints_validation', {})
        
        # Build segments summary
        segments = []
        for cluster_id, persona in personas.items():
            segment = {
                'cluster_id': cluster_id,
                'segment_name': persona['persona_name'],
                'short_name': persona['short_name'],
                'description': persona['description'],
                'size': persona['size'],
                'percentage': persona['percentage'],
                'min_customers': persona['size'],
                'avg_revenue_potential': persona['revenue_metrics']['avg_customer_value'],
                'total_revenue': persona['revenue_metrics']['total_revenue_12mo'],
                'special_flags': persona.get('special_flags', []),
                'name_explanation': persona.get('name_explanation', ''),  # Add name explanation
                'segment_explanation': persona.get('segment_explanation', {}),  # Add full segment explanation
                'characteristics': {
                    'search_specificity': persona['characteristics']['avg_search_specificity'],
                    'bundle_affinity': persona['characteristics']['avg_bundle_affinity'],
                    'price_sensitivity': persona['characteristics']['avg_price_sort_frequency'],
                    'avg_spend': persona['characteristics']['avg_spend_12mo'],
                    'purchase_frequency': persona['characteristics']['avg_purchase_frequency']
                }
            }
            segments.append(segment)
        
        return {
            "success": True,
            "segments": segments,
            "constraints_met": constraints.get('all_constraints_met', True),
            "constraints_validation": constraints,
            "last_refreshed": results.get('last_refreshed', datetime.now().isoformat()),
            "total_customers": results.get('total_customers', 0),
            "total_revenue": results.get('total_revenue', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting macro segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/agent_a/export")
async def export_academy_personas():
    """Export persona assignments to CSV for marketing campaigns"""
    try:
        from fastapi.responses import StreamingResponse
        import io
        
        # Get CSV string from agent
        csv_string = academy_agent_a.export_persona_assignments()
        
        # Create streaming response
        output = io.StringIO(csv_string)
        output.seek(0)
        
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=academy_sports_personas.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting personas: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW: Academy Sports - Customer-Level Personalization Endpoints
# ============================================================================

@app.get("/api/academy/agent_a/customers")
async def get_academy_customers(
    skip: int = 0,
    limit: int = 50,
    persona_filter: str = None,
    search: str = None
):
    """
    Get paginated list of all customers with persona assignments
    
    Query Parameters:
    - skip: Number of records to skip (default: 0)
    - limit: Number of records to return (default: 50)
    - persona_filter: Filter by persona short name (Novice, Family_Socializer, Seasoned_Pro)
    - search: Search by customer name or ID
    """
    try:
        customers_data = academy_agent_a.get_all_customers(
            skip=skip,
            limit=limit,
            persona_filter=persona_filter,
            search_query=search
        )
        
        # Convert numpy types
        customers_data = numpy_to_python_types(customers_data)
        
        return {
            "success": True,
            "data": customers_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting customers: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/agent_a/customer/{customer_id}")
async def get_academy_customer_details(customer_id: str):
    """
    Get detailed information for a specific customer
    
    Path Parameters:
    - customer_id: Customer ID (e.g., CUST_00001)
    
    Returns customer metrics, persona assignment, comparisons to persona averages,
    and behavioral insights
    """
    try:
        customer_details = academy_agent_a.get_customer_details(customer_id)
        
        # Convert numpy types
        customer_details = numpy_to_python_types(customer_details)
        
        return {
            "success": True,
            "data": customer_details
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting customer details: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/academy/agent_a/customer/{customer_id}/explain")
async def explain_customer_persona(
    customer_id: str,
    api_key: str = Body(..., embed=True, description="Together AI API key")
):
    """
    Generate AI-powered explanation for why a customer fits their persona
    
    Path Parameters:
    - customer_id: Customer ID (e.g., CUST_00001)
    
    Request Body:
    - api_key: Together AI API key for LLM-powered explanation
    
    Returns AI-generated explanation with behavioral analysis and recommendations
    """
    try:
        explanation_data = academy_agent_a.generate_persona_explanation(
            customer_id=customer_id,
            together_api_key=api_key
        )
        
        return {
            "success": True,
            "data": explanation_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating explanation: {e}")
        logger.error(traceback.format_exc())
        
        # Return fallback explanation on API error
        try:
            customer_details = academy_agent_a.get_customer_details(customer_id)
            from agents.agent_a_academy_chromadb import AgentA_Academy
            fallback_explanation = academy_agent_a._generate_rule_based_explanation(customer_details)
            
            return {
                "success": True,
                "data": {
                    "customer_id": customer_id,
                    "customer_name": customer_details['customer_name'],
                    "persona": customer_details['persona'],
                    "confidence": customer_details['confidence'],
                    "explanation": fallback_explanation,
                    "status": "fallback",
                    "note": "Using rule-based explanation (API error)"
                }
            }
        except:
            raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/academy/agent_a/explain-visualization")
async def explain_visualization(
    visualization_type: str = Body(..., description="Type of visualization"),
    data: Dict = Body(..., description="Visualization data"),
    personas: Dict = Body(..., description="Personas data"),
    api_key: str = Body(None, description="Together AI API key (optional, uses system config if not provided)")
):
    """
    Generate AI-powered explanation for a specific visualization
    
    Request Body:
    - visualization_type: Type of chart (e.g., 'revenue', 'confidence', 'radar')
    - data: The visualization data
    - personas: Persona information
    - api_key: Together AI API key (optional, uses system config if not provided)
    
    Returns AI-generated insights about the visualization
    """
    try:
        # Use provided API key or get from system config
        if not api_key:
            api_key = system_state.get('together_api_key', os.getenv('TOGETHER_API_KEY', ''))
        
        explanation = academy_agent_a.generate_visualization_explanation(
            visualization_type=visualization_type,
            data=data,
            personas=personas,
            together_api_key=api_key
        )
        
        return {
            "success": True,
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"Error generating visualization explanation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/agent_a/customer/{customer_id}/recommendations")
async def get_customer_recommendations(customer_id: str):
    """
    Get PERSONALIZED PRODUCT recommendations for a specific customer
    
    Path Parameters:
    - customer_id: Customer ID (e.g., CUST_00001)
    
    Returns actual product recommendations with detailed explanations of why
    each product suits this specific customer based on their tier, preferences,
    and purchase history
    """
    try:
        global academy_cached_data, academy_dataset_version
        
        # ENSURE data is preloaded before generating recommendations
        if not academy_cached_data['loaded'] or academy_cached_data['version'] != academy_dataset_version:
            logger.info(f"⏳ Data not cached, preloading {academy_dataset_version}...")
            preload_result = preload_academy_data(academy_dataset_version, max_retries=3)
            
            if not preload_result['success']:
                error_msg = f"Failed to preload data: {preload_result.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Use cached data if available, otherwise load from files
        import pandas as pd
        
        if academy_cached_data['loaded'] and academy_cached_data['customers_df'] is not None:
            logger.info(f"✅ Using cached data for recommendations")
            customers_df = academy_cached_data['customers_df']
            products_df = academy_cached_data['products_df']
            purchases_df = academy_cached_data['purchases_df']
        else:
            logger.info(f"⚠️ Loading data from files (cache not available)")
            customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
            products_df = pd.read_csv(get_dataset_file_path('products.csv'))
            purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Check if Agent A has been run and use clustered data if available
        if system_state['academy']['agent_a_results']:
            customers_with_clusters = system_state['academy']['agent_a_results'].get('customers_with_clusters')
            if customers_with_clusters is not None and isinstance(customers_with_clusters, pd.DataFrame):
                customers_df = customers_with_clusters
                logger.info(f"✅ Using clustered customer data from Agent A results")
        
        # Verify customer exists
        if customer_id not in customers_df['customer_id'].values:
            raise ValueError(f"Customer {customer_id} not found")
        
        logger.info(f"🎯 Generating recommendations for customer {customer_id}")
        logger.info(f"   Customers: {len(customers_df)}, Products: {len(products_df)}, Purchases: {len(purchases_df)}")
        
        # Initialize Enhanced Agent B for recommendations with personas
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        agent_b_enhanced = AgentB_Academy_Enhanced(
            customers_df=customers_df,
            products_df=products_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Pass Agent B to Agent A so it can get real product recommendations
        recommendations = academy_agent_a.get_customer_recommendations(
            customer_id=customer_id,
            agent_b=agent_b_enhanced  # Pass Enhanced Agent B with get_similar_products
        )
        
        logger.info(f"✅ Generated {len(recommendations.get('products', []))} recommendations")
        
        # Convert numpy types
        recommendations = numpy_to_python_types(recommendations)
        
        return {
            "success": True,
            "data": recommendations
        }
        
    except ValueError as e:
        logger.error(f"❌ ValueError: {e}")
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Error getting recommendations: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# End of Customer-Level Personalization Endpoints
# ============================================================================


@app.post("/api/academy/agent_b/execute")
async def execute_academy_agent_b(config: AgentBConfigAcademy):
    """Execute Academy Sports Agent B - feature-based recommendations"""
    try:
        global academy_dataset_version
        
        # Determine if using customer-based or persona-based recommendations
        if config.customer_id:
            logger.info("="*80)
            logger.info(f"🎯 ACADEMY SPORTS AGENT B - RECOMMENDATIONS FOR CUSTOMER {config.customer_id}")
            logger.info("="*80)
        else:
            logger.info("="*80)
            logger.info(f"🎯 ACADEMY SPORTS AGENT B - RECOMMENDATIONS FOR {config.persona} PERSONA")
            logger.info("="*80)
        
        start_time = datetime.now()
        
        # Execute Agent B
        results = academy_agent_b.execute({
            'customer_id': config.customer_id,
            'persona': config.persona,
            'search_query': config.search_query or '',
            'category': config.category,
            'top_n': config.top_n,
            'explain': config.explain,
            'dataset_version': academy_dataset_version
        })
        
        # FILTER OUT-OF-STOCK PRODUCTS
        # Separate in-stock and out-of-stock recommendations
        import pandas as pd
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        
        # Convert in_stock column to boolean
        if 'in_stock' in products_df.columns:
            products_df['in_stock'] = products_df['in_stock'].astype(str).str.lower().isin(['true', '1', 'yes'])
        
        # Create a lookup dict for in_stock status
        in_stock_lookup = dict(zip(products_df['product_id'], products_df['in_stock']))
        
        # Separate recommendations
        in_stock_recommendations = []
        out_of_stock_recommendations = []
        
        for rec in results.get('recommendations', []):
            product_id = rec.get('product_id')
            is_in_stock = in_stock_lookup.get(product_id, True)
            
            # Add in_stock field to recommendation
            rec['in_stock'] = bool(is_in_stock)
            
            if is_in_stock:
                in_stock_recommendations.append(rec)
            else:
                out_of_stock_recommendations.append(rec)
        
        # Update results with separated recommendations
        results['recommendations'] = in_stock_recommendations
        results['out_of_stock_recommendations'] = out_of_stock_recommendations
        results['in_stock_count'] = len(in_stock_recommendations)
        results['out_of_stock_count'] = len(out_of_stock_recommendations)
        
        # Store results
        system_state['academy']['agent_b_results'] = results
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Academy Agent B completed in {execution_time:.2f}s")
        logger.info(f"   In-stock: {len(in_stock_recommendations)} | Out-of-stock: {len(out_of_stock_recommendations)}")
        
        # Convert numpy types
        results = numpy_to_python_types(results)
        
        return {
            "success": True,
            "results": results,
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Academy Agent B failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/agent_b/results")
async def get_academy_agent_b_results():
    """Get Academy Sports Agent B results"""
    if not system_state['academy']['agent_b_results']:
        raise HTTPException(status_code=404, detail="No Agent B results available. Please execute Agent B first.")
    
    results = numpy_to_python_types(system_state['academy']['agent_b_results'])
    return {"success": True, "results": results}


@app.post("/api/academy/agent_b/logit")
async def execute_academy_agent_b_logit(config: AgentBLogitConfig):
    """
    Execute Academy Sports Agent B with Hybrid ML Model
    
    Uses 70% ML (Logistic Regression) + 30% Business Rules
    """
    try:
        logger.info("="*80)
        logger.info(f"🤖 ACADEMY SPORTS AGENT B - HYBRID ML MODEL")
        if config.customer_id:
            logger.info(f"   Customer: {config.customer_id}")
        else:
            logger.info(f"   Persona: {config.persona}")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Load data
        import pandas as pd
        customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Get personas from Agent A results
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        # Initialize Hybrid Agent B
        agent_b_logit = AgentB_LogitEnhanced(
            products_df=products_df,
            customers_df=customers_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Get recommendations
        try:
            results = agent_b_logit.recommend(
                customer_id=config.customer_id,
                persona_name=config.persona,
                search_query=config.search_query or '',
                category=config.category or '',
                top_n=config.top_n
            )
        except (FileNotFoundError, ValueError) as e:
            # Model not trained yet - train it now
            logger.warning("⚠️ ML model not found or untrained. Training now (first time only)...")
            agent_b_logit.train_logit_model()
            logger.info("✅ Model trained successfully. Generating recommendations...")
            
            results = agent_b_logit.recommend(
                customer_id=config.customer_id,
                persona_name=config.persona,
                search_query=config.search_query or '',
                category=config.category or '',
                top_n=config.top_n
            )
        
        # Separate in-stock and out-of-stock
        in_stock_lookup = dict(zip(products_df['product_id'], products_df.get('in_stock', True)))
        
        in_stock_recommendations = []
        out_of_stock_recommendations = []
        
        for rec in results.get('recommendations', []):
            product_id = rec.get('product_id')
            is_in_stock = in_stock_lookup.get(product_id, True)
            rec['in_stock'] = bool(is_in_stock)
            
            # Add scoring details for UI
            rec['score'] = rec.get('final_score', 0)
            rec['match_level'] = (
                'Perfect Match' if rec['score'] > 0.7 else
                'Great Match' if rec['score'] > 0.5 else
                'Good Option' if rec['score'] > 0.3 else
                'Consider Alternatives'
            )
            
            if is_in_stock:
                in_stock_recommendations.append(rec)
            else:
                out_of_stock_recommendations.append(rec)
        
        # Calculate metrics from recommendations
        metrics = results.get('metrics', {})
        avg_price = metrics.get('avg_price', 0)
        avg_match_score = metrics.get('avg_match_score', 0)
        price_range = ''
        if avg_price > 0:
            min_price = min([r['price'] for r in in_stock_recommendations]) if in_stock_recommendations else 0
            max_price = max([r['price'] for r in in_stock_recommendations]) if in_stock_recommendations else 0
            price_range = f"${min_price:.0f} - ${max_price:.0f}"
        
        # Format results to match rule-based structure
        formatted_results = {
            'recommendations': in_stock_recommendations,
            'out_of_stock_recommendations': out_of_stock_recommendations,
            'in_stock_count': len(in_stock_recommendations),
            'out_of_stock_count': len(out_of_stock_recommendations),
            'customer_id': config.customer_id,
            'persona': results.get('persona'),
            'model_performance': results.get('model_performance', {}),
            # ADD METRICS FOR UI
            'metrics': {
                'avg_match_score': avg_match_score,
                'avg_price': avg_price,
                'price_range': price_range,
                'total_recommendations': len(in_stock_recommendations) + len(out_of_stock_recommendations)
            },
            'insights': {
                'total_recommendations': len(in_stock_recommendations) + len(out_of_stock_recommendations),
                'scoring_method': 'Hybrid ML (70% ML + 30% Rules)',
                'ml_weight': 0.7,
                'rule_weight': 0.3
            }
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Hybrid Agent B completed in {execution_time:.2f}s")
        logger.info(f"   Avg Match Score: {avg_match_score:.1%}")
        logger.info(f"   Avg Price: ${avg_price:.2f}")
        logger.info(f"   In-stock: {len(in_stock_recommendations)} | Out-of-stock: {len(out_of_stock_recommendations)}")
        
        return {
            "success": True,
            "results": numpy_to_python_types(formatted_results),
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Hybrid Agent B failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/academy/agent_b/nested_logit")
async def execute_academy_agent_b_nested_logit(config: AgentBLogitConfig):
    """
    Execute Academy Sports Agent B with Nested Logit Model
    
    Addresses IIA assumption and captures product substitution patterns
    Hierarchical structure: Category → Brand → Product
    """
    try:
        logger.info("="*80)
        logger.info(f"🌳 ACADEMY SPORTS AGENT B - NESTED LOGIT MODEL")
        if config.customer_id:
            logger.info(f"   Customer: {config.customer_id}")
        else:
            logger.info(f"   Persona: {config.persona}")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Load data
        import pandas as pd
        customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Get personas from Agent A results
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        # Initialize Nested Logit Agent B
        agent_b_nested = AgentB_NestedLogit(
            products_df=products_df,
            customers_df=customers_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Get recommendations
        results = agent_b_nested.recommend(
            persona_name=config.persona,
            top_k=config.top_n
        )
        
        if not results.get('success'):
            raise HTTPException(status_code=400, detail=results.get('error', 'Unknown error'))
        
        # Separate in-stock and out-of-stock
        in_stock_lookup = dict(zip(products_df['product_id'], products_df.get('in_stock', True)))
        
        in_stock_recommendations = []
        out_of_stock_recommendations = []
        
        for rec in results.get('recommendations', []):
            product_id = rec.get('product_id')
            is_in_stock = in_stock_lookup.get(product_id, True)
            rec['in_stock'] = bool(is_in_stock)
            
            # Add scoring details for UI (use overall_probability as score)
            rec['score'] = rec.get('overall_probability', 0) / 100.0  # Convert from percentage to 0-1
            rec['match_level'] = rec.get('match_quality', 'Good Match')
            
            if is_in_stock:
                in_stock_recommendations.append(rec)
            else:
                out_of_stock_recommendations.append(rec)
        
        # Calculate metrics from recommendations
        metrics = results.get('metrics', {})
        avg_probability = metrics.get('avg_probability', 0)
        avg_price = metrics.get('avg_price', 0)
        price_range = metrics.get('price_range', '$0 - $0')
        
        # Format results to match standard structure
        formatted_results = {
            'recommendations': in_stock_recommendations,
            'out_of_stock_recommendations': out_of_stock_recommendations,
            'in_stock_count': len(in_stock_recommendations),
            'out_of_stock_count': len(out_of_stock_recommendations),
            'total_recommendations': len(in_stock_recommendations) + len(out_of_stock_recommendations),
            'persona': config.persona,
            'metrics': {
                'avg_match_score': float(avg_probability) / 100.0,  # Convert to 0-1 scale
                'avg_price': float(avg_price),
                'price_range': price_range,
                'products_considered': metrics.get('products_considered', 0),
                'unique_categories': metrics.get('unique_categories', 0),
                'unique_brands': metrics.get('unique_brands', 0)
            },
            'model_info': results.get('model_info', {})
        }
        
        # Store results in state
        system_state['academy']['agent_b_nested_logit_results'] = formatted_results
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Nested Logit Agent B completed in {execution_time:.2f}s")
        logger.info(f"   Avg Probability: {avg_probability:.1f}%")
        logger.info(f"   Avg Price: ${avg_price:.2f}")
        logger.info(f"   In-stock: {len(in_stock_recommendations)} | Out-of-stock: {len(out_of_stock_recommendations)}")
        
        return {
            "success": True,
            "results": numpy_to_python_types(formatted_results),
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Nested Logit Agent B failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/products")
async def list_academy_products():
    """List all Academy Sports camping products"""
    try:
        import pandas as pd
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        
        products = products_df.to_dict('records')
        products = [numpy_to_python_types(product) for product in products]
        
        # Get category counts
        category_counts = products_df['main_category'].value_counts().to_dict()
        
        return {
            "success": True,
            "total_products": len(products),
            "categories": category_counts,
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error listing products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# MICRO SEGMENTATION ENDPOINTS
# ============================================================================

@app.post("/api/academy/micro-segments/{macro_segment_id}")
async def create_micro_segments(macro_segment_id: int, n_micro_segments: int = 4):
    """
    Create micro segments for a specific macro segment
    
    Args:
        macro_segment_id: ID of the macro segment
        n_micro_segments: Number of micro segments to create (default 4)
    """
    try:
        logger.info(f"🚀 Creating micro segments for macro segment {macro_segment_id}")
        
        # Check if Agent A has been executed
        if not system_state['academy']['agent_a_results']:
            logger.error("❌ No Agent A results available")
            raise HTTPException(status_code=404, detail="No macro segments available. Please execute Agent A first.")
        
        results = system_state['academy']['agent_a_results']
        personas = results.get('personas', {})
        customers_df = results.get('customers_with_clusters', None)
        
        logger.info(f"  Personas available: {len(personas)}")
        logger.info(f"  Customers data type: {type(customers_df)}")
        logger.info(f"  Customers data is None: {customers_df is None}")
        
        if customers_df is None:
            logger.error("❌ Customer data not available in Agent A results")
            logger.error(f"  Available keys: {list(results.keys())}")
            raise HTTPException(status_code=500, detail="Customer data not available")
        
        # Convert to DataFrame if needed
        if isinstance(customers_df, list):
            import pandas as pd
            customers_df = pd.DataFrame(customers_df)
        
        # Check if macro segment exists
        if macro_segment_id not in personas:
            raise HTTPException(status_code=404, detail=f"Macro segment {macro_segment_id} not found")
        
        # Initialize micro segmentation agent
        from agents.agent_a_academy_micro import AgentA_Academy_Micro
        micro_agent = AgentA_Academy_Micro(customers_df, personas)
        
        # Execute micro segmentation
        logger.info(f"  Executing micro segmentation agent...")
        result = micro_agent.execute(macro_segment_id, n_micro_segments)
        
        # Store results
        if 'academy_micro_segments' not in system_state['academy']:
            system_state['academy']['academy_micro_segments'] = {}
        
        system_state['academy']['academy_micro_segments'][macro_segment_id] = result
        
        micro_count = len(result.get('micro_segments', []))
        logger.info(f"✅ Successfully created {micro_count} micro segments for macro segment {macro_segment_id}")
        
        return {
            "success": True,
            "result": numpy_to_python_types(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating micro segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/micro-segments/{macro_segment_id}")
async def get_micro_segments(macro_segment_id: int):
    """
    Get micro segments for a specific macro segment
    
    Args:
        macro_segment_id: ID of the macro segment
    """
    try:
        # Check if micro segments exist
        if 'academy_micro_segments' not in system_state['academy']:
            system_state['academy']['academy_micro_segments'] = {}
        
        if macro_segment_id not in system_state['academy']['academy_micro_segments']:
            # Auto-create micro segments if Agent A results exist
            if system_state['academy']['agent_a_results']:
                await create_micro_segments(macro_segment_id)
            else:
                raise HTTPException(status_code=404, detail=f"No micro segments found for macro segment {macro_segment_id}")
        
        result = system_state['academy']['academy_micro_segments'][macro_segment_id]
        
        return {
            "success": True,
            "result": numpy_to_python_types(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting micro segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PRODUCT RECOMMENDATION ENDPOINTS
# ============================================================================

@app.get("/api/academy/recommendations/{customer_id}/similar")
async def get_similar_product_recommendations(customer_id: str):
    """
    Get similar product recommendations based on purchase history
    
    Args:
        customer_id: Customer ID
    """
    try:
        # Load data
        import pandas as pd
        customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Initialize recommendation agent with personas
        from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        rec_agent = AgentB_Academy_Enhanced(
            customers_df=customers_df,
            products_df=products_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Get recommendations
        result = rec_agent.get_similar_products(customer_id)
        
        return {
            "success": True,
            "result": numpy_to_python_types(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting similar product recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/recommendations/{customer_id}/you-might-like")
async def get_segment_based_recommendations(customer_id: str, micro_segment_id: int = None):
    """
    Get segment-based recommendations (You Might Like)
    
    Args:
        customer_id: Customer ID
        micro_segment_id: Optional micro segment ID
    """
    try:
        # Load data
        import pandas as pd
        customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Add cluster assignments if Agent A has been executed
        if system_state['academy']['agent_a_results']:
            customers_with_clusters = system_state['academy']['agent_a_results'].get('customers_with_clusters')
            if customers_with_clusters is not None:
                if isinstance(customers_with_clusters, pd.DataFrame):
                    customers_df = customers_with_clusters
                else:
                    cluster_df = pd.DataFrame(customers_with_clusters)
                    customers_df = customers_df.merge(
                        cluster_df[['customer_id', 'cluster']],
                        on='customer_id',
                        how='left',
                        suffixes=('', '_new')
                    )
                    if 'cluster_new' in customers_df.columns:
                        customers_df['cluster'] = customers_df['cluster_new']
                        customers_df.drop('cluster_new', axis=1, inplace=True)
        
        # Initialize recommendation agent with personas
        from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        rec_agent = AgentB_Academy_Enhanced(
            customers_df=customers_df,
            products_df=products_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Get recommendations
        result = rec_agent.get_segment_recommendations(customer_id, micro_segment_id)
        
        return {
            "success": True,
            "result": numpy_to_python_types(result)
        }
        
    except Exception as e:
        logger.error(f"Error getting segment-based recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/academy/recommendations/{customer_id}/search")
async def get_search_based_recommendations(customer_id: str, search_data: dict):
    """
    Get search-based recommendations using semantic search
    
    Args:
        customer_id: Customer ID
        search_data: Dictionary with 'search_term' key
    """
    try:
        search_term = search_data.get('search_term', '')
        
        if not search_term:
            raise HTTPException(status_code=400, detail="search_term is required")
        
        # Load data
        import pandas as pd
        customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # ChromaDB not available with current wrapper, use keyword search
        chromadb_collection = None
        
        # Initialize recommendation agent with personas
        from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced
        personas = {}
        if system_state['academy']['agent_a_results']:
            personas = system_state['academy']['agent_a_results'].get('personas', {})
        
        rec_agent = AgentB_Academy_Enhanced(
            customers_df=customers_df,
            products_df=products_df,
            purchases_df=purchases_df,
            personas=personas
        )
        
        # Get recommendations
        result = rec_agent.get_search_recommendations(
            customer_id,
            search_term,
            chromadb_collection
        )
        
        return {
            "success": True,
            "result": numpy_to_python_types(result)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search-based recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/recommendations/{customer_id}/all")
async def get_all_recommendations(customer_id: str, search_term: str = None):
    """
    Get all three types of recommendations for a customer
    
    Args:
        customer_id: Customer ID
        search_term: Optional search term for dynamic recommendations
    """
    try:
        global academy_cached_data, academy_dataset_version
        
        # ENSURE data is preloaded
        if not academy_cached_data['loaded'] or academy_cached_data['version'] != academy_dataset_version:
            logger.info(f"⏳ Data not cached, preloading {academy_dataset_version} for recommendations...")
            preload_result = preload_academy_data(academy_dataset_version, max_retries=3)
            
            if not preload_result['success']:
                error_msg = f"Failed to preload data: {preload_result.get('error', 'Unknown error')}"
                logger.error(f"❌ {error_msg}")
                raise HTTPException(status_code=500, detail=error_msg)
        
        # Use cached data if available, otherwise load from files
        import pandas as pd
        
        if academy_cached_data['loaded'] and academy_cached_data['customers_df'] is not None:
            logger.info(f"✅ Using cached data for all recommendations")
            customers_df = academy_cached_data['customers_df'].copy()
            products_df = academy_cached_data['products_df'].copy()
            purchases_df = academy_cached_data['purchases_df'].copy()
        else:
            logger.info(f"⚠️ Loading data from files (cache not available)")
            customers_df = pd.read_csv(get_dataset_file_path('customers.csv'))
            products_df = pd.read_csv(get_dataset_file_path('products.csv'))
            purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Convert in_stock column to boolean (from string "True"/"False")
        if 'in_stock' in products_df.columns:
            products_df['in_stock'] = products_df['in_stock'].astype(str).str.lower().isin(['true', '1', 'yes'])
        
        # Add cluster assignments if available
        if system_state['academy']['agent_a_results']:
            customers_with_clusters = system_state['academy']['agent_a_results'].get('customers_with_clusters')
            if customers_with_clusters is not None:
                if isinstance(customers_with_clusters, pd.DataFrame):
                    customers_df = customers_with_clusters
                    logger.info(f"✅ Using clustered customer data with {len(customers_df)} customers")
                    
                    # Log customer info for debugging
                    if customer_id in customers_df['customer_id'].values:
                        customer_row = customers_df[customers_df['customer_id'] == customer_id].iloc[0]
                        logger.info(f"👤 Customer {customer_id} info:")
                        logger.info(f"   LTV: ${customer_row.get('total_spend_12mo', 'N/A')}")
                        logger.info(f"   Dominant Category: {customer_row.get('dominant_category', 'N/A')}")
                        logger.info(f"   Cluster: {customer_row.get('cluster', 'N/A')}")
        
        # Verify customer exists
        if customer_id not in customers_df['customer_id'].values:
            logger.error(f"❌ Customer {customer_id} not found in dataset")
            raise HTTPException(status_code=404, detail=f"Customer {customer_id} not found")
        
        logger.info(f"🔍 Getting all recommendations for customer: {customer_id}")
        logger.info(f"   Data loaded: Customers={len(customers_df)}, Products={len(products_df)}, Purchases={len(purchases_df)}")
        
        # Get ChromaDB collection
        chromadb_collection = None
        try:
            if chroma_client:
                chromadb_collection = chroma_client.get_collection('academy_products')
                logger.info(f"   ChromaDB collection available")
        except Exception as ce:
            logger.warning(f"   ChromaDB not available: {ce}")
        
        # Initialize recommendation agent with personas
        from agents.agent_b_academy_enhanced import AgentB_Academy_Enhanced
        
        try:
            personas = {}
            if system_state['academy']['agent_a_results']:
                personas = system_state['academy']['agent_a_results'].get('personas', {})
            
            rec_agent = AgentB_Academy_Enhanced(
                customers_df=customers_df,
                products_df=products_df,
                purchases_df=purchases_df,
                personas=personas
            )
            logger.info(f"✅ Agent B Enhanced initialized successfully with {len(personas)} personas")
        except Exception as init_error:
            logger.error(f"❌ Failed to initialize Agent B Enhanced: {init_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to initialize recommendation agent: {str(init_error)}")
        
        # Get all recommendations
        try:
            result = rec_agent.get_all_recommendations(
                customer_id,
                search_term,
                chromadb_collection
            )
            logger.info(f"✅ Recommendations generated successfully")
        except Exception as rec_error:
            logger.error(f"❌ Failed to generate recommendations: {rec_error}")
            logger.error(traceback.format_exc())
            raise HTTPException(status_code=500, detail=f"Failed to generate recommendations: {str(rec_error)}")
        
        # Check if result is valid
        if not isinstance(result, dict):
            logger.error(f"Invalid result type from agent: {type(result)}, value: {result}")
            raise ValueError(f"Agent returned invalid result type: {type(result)}")
        
        logger.info(f"📊 Raw recommendations received:")
        logger.info(f"   Tailored: {len(result.get('tailored_recommendations', []))} products")
        logger.info(f"   Similar: {len(result.get('similar_products', []))} products")
        logger.info(f"   Segment: {len(result.get('segment_recommendations', []))} products")
        
        # Separate in-stock and out-of-stock products
        def separate_by_stock(products):
            """Separate products into in-stock and out-of-stock lists"""
            in_stock = []
            out_of_stock = []
            
            for product in products:
                # Check in_stock field (handles both boolean and string values)
                is_in_stock = product.get('in_stock', True)
                if isinstance(is_in_stock, str):
                    is_in_stock = is_in_stock.lower() in ['true', '1', 'yes']
                
                if is_in_stock:
                    in_stock.append(product)
                else:
                    out_of_stock.append(product)
            
            return in_stock, out_of_stock
        
        # Process each recommendation type
        tailored_in_stock, tailored_out_of_stock = separate_by_stock(
            result.get('tailored_recommendations', [])
        )
        similar_in_stock, similar_out_of_stock = separate_by_stock(
            result.get('similar_products', [])
        )
        segment_in_stock, segment_out_of_stock = separate_by_stock(
            result.get('segment_recommendations', [])
        )
        
        return {
            "success": True,
            "result": {
                # In-stock products (main recommendations)
                "tailored_recommendations": numpy_to_python_types(tailored_in_stock),
                "similar_products": numpy_to_python_types(similar_in_stock),
                "segment_recommendations": numpy_to_python_types(segment_in_stock),
                # Out-of-stock products (separate section)
                "out_of_stock_tailored": numpy_to_python_types(tailored_out_of_stock),
                "out_of_stock_similar": numpy_to_python_types(similar_out_of_stock),
                "out_of_stock_segment": numpy_to_python_types(segment_out_of_stock),
                # Metadata
                "customer_info": result.get('customer_info', {}),
                "recommendation_metadata": result.get('recommendation_metadata', {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting all recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# NEW VISITOR RECOMMENDATIONS
# ============================================================================

@app.get("/api/academy/recommendations/new-visitor")
async def get_new_visitor_recommendations():
    """
    Get generic recommendations for new visitors without purchase history
    
    Returns:
    - Top 3 best-selling products
    - Top 3 highest-rated products
    - Top 3 trending products
    """
    try:
        import pandas as pd
        products_df = pd.read_csv(get_dataset_file_path('products.csv'))
        purchases_df = pd.read_csv(get_dataset_file_path('purchases.csv'))
        
        # Calculate product popularity
        product_sales = purchases_df['product_id'].value_counts()
        
        # Best-selling products
        best_selling_ids = product_sales.head(3).index.tolist()
        best_selling = products_df[
            (products_df['product_id'].isin(best_selling_ids)) &
            (products_df['in_stock'] == True)
        ].copy()
        
        best_selling_list = []
        for _, product in best_selling.iterrows():
            best_selling_list.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'brand': product['brand'],
                'category': product['main_category'],
                'price': round(product['price'], 2),
                'rating': round(product.get('avg_rating', 4.0), 1),
                'num_reviews': int(product.get('num_reviews', 0)),
                'reason': 'Best-selling product'
            })
        
        # Highest-rated products (with minimum reviews)
        if 'avg_rating' in products_df.columns and 'num_reviews' in products_df.columns:
            top_rated = products_df[
                (products_df['num_reviews'] >= 20) &
                (products_df['in_stock'] == True)
            ].nlargest(3, 'avg_rating')
        else:
            top_rated = products_df[products_df['in_stock'] == True].head(3)
        
        top_rated_list = []
        for _, product in top_rated.iterrows():
            top_rated_list.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'brand': product['brand'],
                'category': product['main_category'],
                'price': round(product['price'], 2),
                'rating': round(product.get('avg_rating', 4.0), 1),
                'num_reviews': int(product.get('num_reviews', 0)),
                'reason': 'Highly rated by customers'
            })
        
        # Trending products (recent purchases)
        if 'purchase_date' in purchases_df.columns:
            purchases_df['purchase_date'] = pd.to_datetime(purchases_df['purchase_date'])
            recent_date = purchases_df['purchase_date'].max() - pd.Timedelta(days=30)
            recent_purchases = purchases_df[purchases_df['purchase_date'] >= recent_date]
            trending_ids = recent_purchases['product_id'].value_counts().head(3).index.tolist()
            
            trending = products_df[
                (products_df['product_id'].isin(trending_ids)) &
                (products_df['in_stock'] == True)
            ]
        else:
            # Fallback: use mid-price range products
            median_price = products_df['price'].median()
            trending = products_df[
                (products_df['price'] >= median_price * 0.8) &
                (products_df['price'] <= median_price * 1.2) &
                (products_df['in_stock'] == True)
            ].head(3)
        
        trending_list = []
        for _, product in trending.iterrows():
            trending_list.append({
                'product_id': product['product_id'],
                'product_name': product['product_name'],
                'brand': product['brand'],
                'category': product['main_category'],
                'price': round(product['price'], 2),
                'rating': round(product.get('avg_rating', 4.0), 1),
                'num_reviews': int(product.get('num_reviews', 0)),
                'reason': 'Trending this month'
            })
        
        return {
            "success": True,
            "segment_type": "new_visitor",
            "recommendations": {
                "best_selling": best_selling_list,
                "top_rated": top_rated_list,
                "trending": trending_list
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting new visitor recommendations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BANKING PLATFORM ENDPOINTS
# ============================================================================

@app.get("/api/banking/datasets")
async def list_banking_datasets():
    """List available Banking datasets"""
    import pandas as pd
    from pathlib import Path
    
    try:
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "preloaded" / "fmb_bank"
        
        logger.info(f"📂 Checking for F&M Bank datasets in: {data_path}")
        
        data_path.mkdir(parents=True, exist_ok=True)
        
        datasets = []
        
        # Check what files exist
        customers_file = data_path / "customers.csv"
        products_file = data_path / "products.csv"
        transactions_file = data_path / "transactions.csv"
        
        if customers_file.exists():
            try:
                customers_df = pd.read_csv(customers_file)
                customer_count = len(customers_df)
                
                product_count = 0
                if products_file.exists():
                    products_df = pd.read_csv(products_file)
                    product_count = len(products_df)
                
                transaction_count = 0
                if transactions_file.exists():
                    transactions_df = pd.read_csv(transactions_file)
                    transaction_count = len(transactions_df)
                
                datasets.append({
                    "name": "banking_v1",
                    "display_name": "Banking Platform V1",
                    "version": "v1",
                    "description": f"Banking dataset with {customer_count} customers and financial products",
                    "tables": [
                        {
                            "name": "customers",
                            "display_name": "Customers",
                            "row_count": customer_count,
                            "loaded": True
                        },
                        {
                            "name": "products",
                            "display_name": "Products",
                            "row_count": product_count,
                            "loaded": True
                        },
                        {
                            "name": "transactions",
                            "display_name": "Transactions",
                            "row_count": transaction_count,
                            "loaded": True
                        }
                    ],
                    "loaded": True,
                    "status": "ready",
                    "customer_count": customer_count,
                    "product_count": product_count,
                    "transaction_count": transaction_count,
                    "path": str(data_path)
                })
                logger.info(f"✅ Banking dataset: {customer_count} customers, {product_count} products, {transaction_count} transactions")
            except Exception as e:
                logger.error(f"❌ Error reading banking dataset: {e}")
        else:
            datasets.append({
                "name": "banking_v1",
                "display_name": "Banking Platform V1",
                "version": "v1",
                "description": "Banking dataset - Generate by running: generate_banking_data_5000.bat",
                "tables": [
                    {
                        "name": "customers",
                        "display_name": "Customers",
                        "row_count": 5000,
                        "loaded": False
                    },
                    {
                        "name": "products",
                        "display_name": "Products",
                        "row_count": 20,
                        "loaded": False
                    },
                    {
                        "name": "transactions",
                        "display_name": "Transactions",
                        "row_count": 25000,
                        "loaded": False
                    }
                ],
                "loaded": False,
                "status": "not_generated",
                "customer_count": 5000,
                "product_count": 20,
                "path": str(data_path)
            })
            logger.warning(f"⚠️ Banking dataset not found at {customers_file}")
        
        logger.info(f"📊 Returning {len(datasets)} banking datasets")
        return {"datasets": datasets}
        
    except Exception as e:
        logger.error(f"❌ Error listing banking datasets: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return {"datasets": [], "error": str(e)}


@app.get("/api/banking/datasets/view/{dataset_name}/{table_name}")
async def view_banking_dataset_table(dataset_name: str, table_name: str):
    """View a specific table from the banking dataset"""
    import pandas as pd
    import numpy as np
    from pathlib import Path
    
    try:
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "preloaded" / "fmb_bank"
        
        # Map table names to file names
        table_files = {
            "customers": "customers.csv",
            "products": "products.csv",
            "transactions": "transactions.csv"
        }
        
        if table_name not in table_files:
            raise HTTPException(status_code=404, detail=f"Table {table_name} not found")
        
        file_path = data_path / table_files[table_name]
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File {file_path} not found")
        
        # Read the CSV
        df = pd.read_csv(file_path)
        
        # Get first 100 rows for preview
        preview_df = df.head(100)
        
        # Replace NaN/Inf values with None for JSON compatibility
        preview_df = preview_df.replace([np.inf, -np.inf], np.nan)
        preview_df = preview_df.where(pd.notnull(preview_df), None)
        
        return {
            "columns": df.columns.tolist(),
            "data": preview_df.to_dict(orient='records'),
            "total_rows": len(df),
            "preview_rows": len(preview_df)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error viewing table {table_name}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/banking/datasets/load")
async def load_banking_dataset(request: dict):
    """Load Banking dataset"""
    dataset_name = request.get("dataset_name", "banking_v1")
    
    logger.info(f"📊 Loading Banking dataset: {dataset_name}")
    
    try:
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "preloaded" / "fmb_bank"
        
        customers_file = data_path / "customers.csv"
        products_file = data_path / "products.csv"
        transactions_file = data_path / "transactions.csv"
        
        if not customers_file.exists():
            raise HTTPException(status_code=404, detail="Banking dataset not found. Run generate_banking_data.bat first.")
        
        import pandas as pd
        customers_df = pd.read_csv(customers_file)
        products_df = pd.read_csv(products_file)
        transactions_df = pd.read_csv(transactions_file)
        
        # Store in system_state for Agent B
        system_state['banking']['products'] = products_df
        system_state['banking']['transactions'] = transactions_df
        system_state['banking']['customers'] = customers_df
        
        logger.info(f"✅ Banking dataset loaded successfully")
        
        return {
            "status": "success",
            "message": "Banking dataset loaded",
            "dataset": dataset_name,
            "customer_count": len(customers_df),
            "product_count": len(products_df),
            "transaction_count": len(transactions_df)
        }
        
    except Exception as e:
        logger.error(f"❌ Error loading banking dataset: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/status")
async def get_banking_status():
    """Get Banking system status"""
    try:
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        data_path = project_root / "data" / "preloaded" / "fmb_bank"
        
        customers_path = data_path / "customers.csv"
        data_loaded = customers_path.exists()
        
        customer_count = 0
        if data_loaded:
            import pandas as pd
            df = pd.read_csv(customers_path)
            customer_count = len(df)
        
        return {
            "data_loaded": data_loaded,
            "current_dataset": "banking_v1",
            "agent_a_complete": system_state['banking']['agent_a_results'] is not None,
            "agent_b_complete": system_state['banking']['agent_b_results'] is not None,
            "customers_count": customer_count,
            "backend": "CSV Files (On-Demand Processing)"
        }
    except Exception as e:
        logger.error(f"Error getting Banking status: {e}")
        return {
            "data_loaded": False,
            "current_dataset": None,
            "agent_a_complete": False,
            "agent_b_complete": False,
            "customers_count": 0,
            "backend": "CSV Files"
        }


@app.post("/api/banking/agent_a/execute")
async def execute_banking_agent_a(config: AgentAConfigAcademy):
    """Execute Banking Agent A - Customer Segmentation"""
    try:
        logger.info("="*80)
        logger.info(f"🏦 BANKING AGENT A - CUSTOMER SEGMENTATION")
        logger.info(f"   Requested clusters: {config.n_clusters}")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Execute Banking Agent A with user's gamma selection
        results = banking_agent_a.execute({
            'dataset_version': 'v1',
            'n_clusters': config.n_clusters,
            'gamma': config.gamma  # USE USER INPUT, NOT HARDCODED
        })
        
        execution_time = (datetime.now() - start_time).total_seconds()
        logger.info(f"✅ Banking Agent A completed in {execution_time:.2f}s")
        logger.info(f"   Generated {results.get('n_clusters', 0)} personas")
        
        # Convert numpy types BEFORE storing (converts DataFrames to dicts)
        results = numpy_to_python_types(results)
        
        # Store converted results
        system_state['banking']['agent_a_results'] = results
        
        return {
            "success": True,
            "result": results,
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Banking Agent A failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/agent_a/results")
async def get_banking_agent_a_results():
    """Get Banking Agent A results"""
    if not system_state['banking']['agent_a_results']:
        raise HTTPException(status_code=404, detail="No Agent A results available. Please execute Agent A first.")
    
    results = system_state['banking']['agent_a_results']
    results = numpy_to_python_types(results)
    return {"success": True, "results": results}


@app.get("/api/banking/macro-segments")
async def get_banking_macro_segments():
    """Get Banking macro segments"""
    try:
        if not system_state['banking']['agent_a_results']:
            raise HTTPException(status_code=404, detail="No segments available. Please execute Agent A first.")
        
        results = system_state['banking']['agent_a_results']
        personas = results.get('personas', {})
        
        segments = []
        for cluster_id, persona in personas.items():
            segment = {
                'cluster_id': cluster_id,
                'segment_name': persona['persona_name'],
                'short_name': persona['short_name'],
                'description': persona['description'],
                'size': persona['size'],
                'percentage': persona['percentage'],
                'characteristics': persona['characteristics'],
                'revenue_metrics': persona['revenue_metrics'],
                'special_flags': persona.get('special_flags', [])
            }
            segments.append(segment)
        
        return {
            "success": True,
            "segments": segments,
            "total_customers": results.get('total_customers', 0),
            "total_deposits": results.get('total_deposits', 0)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting banking macro segments: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BANKING MICRO SEGMENTATION ENDPOINTS (NEW - Matching Academy Sports)
# ============================================================================

@app.post("/api/banking/micro-segments/{macro_segment_id}")
async def create_banking_micro_segments(macro_segment_id: int, n_micro_segments: int = 4):
    """
    Create micro segments for a specific banking macro segment
    
    Args:
        macro_segment_id: ID of macro segment to sub-segment
        n_micro_segments: Number of micro segments to create (default 4)
    """
    try:
        logger.info(f"🚀 Creating banking micro segments for macro segment {macro_segment_id}")
        
        # Check if Agent A has been executed
        if not system_state['banking']['agent_a_results']:
            raise HTTPException(
                status_code=400,
                detail="Agent A must be executed first. Please run macro segmentation."
            )
        
        # Get Agent A results
        agent_a_results = system_state['banking']['agent_a_results']
        customers_df = pd.DataFrame(agent_a_results['customers_with_clusters'])
        personas = agent_a_results['personas']
        
        # Validate macro segment exists (check both int and str versions)
        if macro_segment_id not in personas and str(macro_segment_id) not in personas:
            # Try converting personas keys to int
            int_personas = {int(k) if isinstance(k, str) and k.isdigit() else k: v for k, v in personas.items()}
            if macro_segment_id not in int_personas:
                available_segments = list(personas.keys())
                raise HTTPException(
                    status_code=404,
                    detail=f"Macro segment {macro_segment_id} not found. Available segments: {available_segments}"
                )
        
        # Initialize micro segmentation agent
        from agents.agent_a_banking_micro import AgentA_Banking_Micro
        micro_agent = AgentA_Banking_Micro(customers_df, personas)
        
        # Execute micro segmentation
        logger.info(f"  Executing banking micro segmentation agent...")
        result = micro_agent.execute(macro_segment_id, n_micro_segments)
        
        # Store in system state
        if 'banking_micro_segments' not in system_state['banking']:
            system_state['banking']['banking_micro_segments'] = {}
        
        system_state['banking']['banking_micro_segments'][macro_segment_id] = result
        
        micro_count = len(result.get('micro_segments', []))
        logger.info(f"✅ Successfully created {micro_count} banking micro segments for macro segment {macro_segment_id}")
        
        # Convert numpy types
        result = numpy_to_python_types(result)
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating banking micro segments: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/micro-segments/{macro_segment_id}")
async def get_banking_micro_segments(macro_segment_id: int):
    """
    Get micro segments for a specific banking macro segment
    """
    try:
        logger.info(f"📊 Getting banking micro segments for macro segment {macro_segment_id}")
        
        # Check if micro segments exist
        if 'banking_micro_segments' not in system_state['banking']:
            system_state['banking']['banking_micro_segments'] = {}
        
        if macro_segment_id not in system_state['banking']['banking_micro_segments']:
            # Auto-create micro segments if Agent A results exist
            if system_state['banking']['agent_a_results']:
                await create_banking_micro_segments(macro_segment_id)
            else:
                raise HTTPException(status_code=404, detail=f"No micro segments found for macro segment {macro_segment_id}")
        
        result = system_state['banking']['banking_micro_segments'][macro_segment_id]
        
        # Convert numpy types
        result = numpy_to_python_types(result)
        
        return {
            "success": True,
            "result": result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting banking micro segments: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/agent_a/customers")
async def get_banking_customers(
    skip: int = 0,
    limit: int = 50,
    persona_filter: str = None,
    search: str = None
):
    """Get paginated list of banking customers"""
    try:
        customers_data = banking_agent_a.get_all_customers(
            skip=skip,
            limit=limit,
            persona_filter=persona_filter,
            search_query=search
        )
        
        customers_data = numpy_to_python_types(customers_data)
        
        return {
            "success": True,
            "data": customers_data
        }
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting banking customers: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/agent_a/customer/{customer_id}")
async def get_banking_customer_details(customer_id: str):
    """Get detailed information for a specific banking customer"""
    try:
        customer_details = banking_agent_a.get_customer_details(customer_id)
        customer_details = numpy_to_python_types(customer_details)
        
        return {
            "success": True,
            "data": customer_details
        }
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting banking customer details: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/personas")
async def get_banking_personas():
    """Get available banking personas for Agent B dropdown"""
    try:
        if not system_state['banking']['agent_a_results']:
            return {'personas': []}
        
        # Access personas directly (not nested under 'results')
        personas_dict = system_state['banking']['agent_a_results'].get('personas', {})
        personas_list = []
        
        # Calculate total customers for percentage
        total_customers = sum(p['size'] for p in personas_dict.values())
        
        for cluster_id, persona_data in personas_dict.items():
            size = persona_data['size']
            percentage = (size / total_customers * 100) if total_customers > 0 else 0
            personas_list.append({
                'id': str(cluster_id),
                'name': persona_data['persona_name'],
                'size': size,
                'percentage': percentage,
                'emoji': persona_data.get('emoji', '🏦')
            })
        
        logger.info(f"✅ Returning {len(personas_list)} personas for Agent B")
        return {'personas': personas_list}
    except Exception as e:
        logger.error(f"Error getting banking personas: {e}")
        logger.error(traceback.format_exc())
        return {'personas': []}


@app.get("/api/banking/customers")
async def get_banking_customers():
    """Get list of all banking customers (alias for agent_a/customers for Agent B compatibility)"""
    try:
        if not system_state['banking']['agent_a_results']:
            raise HTTPException(status_code=404, detail="No Agent A results available. Please execute Agent A first.")
        
        customers_with_clusters = system_state['banking']['agent_a_results'].get('customers_with_clusters', [])
        
        # Convert DataFrame to list of dictionaries if needed
        if hasattr(customers_with_clusters, 'to_dict'):
            # It's a DataFrame - convert to records
            customers = customers_with_clusters.to_dict('records')
        else:
            # Already a list
            customers = customers_with_clusters
        
        customers = [numpy_to_python_types(c) for c in customers]
        
        return {
            "success": True,
            "total_customers": len(customers),
            "customers": customers
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting banking customers: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/banking/agent_b/execute")
async def execute_banking_agent_b(request: dict = Body(...)):
    """Execute Banking Agent B - Product Recommendations (MATCHES Academy Sports)"""
    try:
        customer_id = request.get('customer_id')
        persona = request.get('persona')  # NEW: Accept persona parameter
        top_n = request.get('top_n', 5)  # NEW: Number of recommendations
        explain = request.get('explain', True)  # NEW: Generate explanations
        
        # MATCHES ACADEMY SPORTS: Accept either customer_id OR persona
        if not customer_id and not persona:
            raise HTTPException(status_code=400, detail="Either customer_id or persona is required")
        
        # Check if Agent A has been executed
        if not system_state['banking']['agent_a_results']:
            raise HTTPException(
                status_code=400, 
                detail="Agent A must be executed first to create personas"
            )
        
        # If persona provided, get a random customer from that persona
        if persona and not customer_id:
            customers_with_clusters = system_state['banking']['agent_a_results'].get('customers_with_clusters', [])
            if hasattr(customers_with_clusters, 'to_dict'):
                customers_list = customers_with_clusters.to_dict('records')
            else:
                customers_list = customers_with_clusters
            
            # Find customers in this persona (use 'cluster' column)
            persona_customers = [c for c in customers_list if c.get('cluster', c.get('macro_segment_id')) == int(persona)]
            
            if not persona_customers:
                raise HTTPException(status_code=404, detail=f"No customers found for persona {persona}")
            
            # Pick first customer from persona
            customer_id = persona_customers[0]['customer_id']
            logger.info(f"📊 Persona mode: Selected customer {customer_id} from persona {persona}")
        
        logger.info("="*80)
        logger.info(f"🏦 BANKING AGENT B - RULE-BASED RECOMMENDATIONS")
        logger.info(f"   Customer ID: {customer_id}")
        logger.info(f"   Persona: {persona}")
        logger.info(f"   Top N: {top_n}")
        logger.info(f"   Explain: {explain}")
        logger.info("="*80)
        
        # Initialize Agent B if needed
        init_banking_agent_b()
        
        if banking_agent_b_chromadb is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize Banking Agent B (Rule-Based)"
            )
        
        # Use the RULE-BASED chromadb agent with execute()
        result = banking_agent_b_chromadb.execute({
            'customer_id': customer_id,
            'persona': persona,
            'search_query': request.get('search_query', ''),
            'category': request.get('category'),
            'top_n': top_n,
            'explain': explain
        })
        
        if not isinstance(result, dict):
            raise ValueError(f"Agent returned invalid result type: {type(result)}")
        
        # Check if agent returned error
        if 'error' in result:
            logger.error(f"❌ Agent B returned error: {result['error']}")
            raise HTTPException(status_code=500, detail=result['error'])
        
        # Store in system state
        if system_state['banking']['agent_b_results'] is None:
            system_state['banking']['agent_b_results'] = {}
        system_state['banking']['agent_b_results'][customer_id] = result
        
        recommendations = result.get('recommendations', [])
        logger.info(f"✅ Banking Agent B (Rule-Based): {len(recommendations)} recommendations")
        
        # Convert numpy types to Python types for JSON serialization
        result = numpy_to_python_types(result)
        
        # Return in frontend-compatible format
        return {
            'success': True,
            'customer_id': customer_id,
            'results': result  # Wrap in 'results' key for frontend
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in Banking Agent B: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/banking/agent_b/logit")
async def execute_banking_agent_b_logit(config: AgentBLogitConfig):
    """
    Execute Banking Agent B with Hybrid ML Model
    
    Uses 50% ML (Logistic Regression) + 50% Banking 12-Factor Rules
    """
    try:
        logger.info("="*80)
        logger.info(f"🤖 BANKING AGENT B - HYBRID ML MODEL")
        if config.customer_id:
            logger.info(f"   Customer: {config.customer_id}")
        else:
            logger.info(f"   Persona: {config.persona}")
        logger.info("="*80)
        
        start_time = datetime.now()
        
        # Check if Agent A has been executed
        if not system_state['banking']['agent_a_results']:
            raise HTTPException(
                status_code=400,
                detail="Agent A must be executed first to create personas"
            )
        
        # Get personas from Agent A results
        personas = system_state['banking']['agent_a_results'].get('personas', {})
        
        # Initialize Banking Agent B if needed
        init_banking_agent_b()
        
        if banking_agent_b_logit is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to initialize Banking Hybrid ML Agent"
            )
        
        # Get recommendations
        try:
            results = banking_agent_b_logit.recommend(
                customer_id=config.customer_id,
                persona_name=config.persona,
                search_query=config.search_query or '',
                category=config.category or '',
                top_n=config.top_n
            )
        except (FileNotFoundError, ValueError) as e:
            # Model not trained yet - train it now
            logger.warning("⚠️ Banking ML model not found or untrained. Training now (first time only)...")
            banking_agent_b_logit.train_logit_model()
            logger.info("✅ Banking model trained successfully. Generating recommendations...")
            
            # Try again
            results = banking_agent_b_logit.recommend(
                customer_id=config.customer_id,
                persona_name=config.persona,
                search_query=config.search_query or '',
                category=config.category or '',
                top_n=config.top_n
            )
        
        # Extract recommendations and metrics (agent returns full banking metrics)
        recommendations = results.get('recommendations', [])
        metrics = results.get('metrics', {}) or {}
        
        # Fee range from recommendations if not in metrics
        fee_range = metrics.get('fee_range', '')
        if not fee_range and recommendations:
            min_fee = min([r.get('annual_fee', 0) for r in recommendations])
            max_fee = max([r.get('annual_fee', 0) for r in recommendations])
            fee_range = f"${min_fee:.0f} - ${max_fee:.0f}"
        
        # Pass through ALL agent metrics so UI shows Match Quality, Annual Cost, Earning Potential, Easy Access
        metrics_for_ui = dict(metrics)
        metrics_for_ui['fee_range'] = fee_range
        metrics_for_ui['total_recommendations'] = len(recommendations)
        if 'avg_fee' not in metrics_for_ui and 'avg_annual_fee' in metrics_for_ui:
            metrics_for_ui['avg_fee'] = metrics_for_ui['avg_annual_fee']
        
        # Algorithm explanation from agent (how ML probability + 50/50 hybrid work)
        scoring_methodology = results.get('scoring_methodology') or results.get('algorithm_explanation') or {}
        
        # Format results to match rule-based structure (include full insights for value_proposition etc.)
        formatted_results = {
            'recommendations': recommendations,
            'customer_id': config.customer_id,
            'persona': results.get('persona'),
            'model_performance': results.get('model_performance', {}),
            'metrics': metrics_for_ui,
            'scoring_methodology': scoring_methodology,
            'algorithm_explanation': scoring_methodology,
            'insights': {
                'total_recommendations': len(recommendations),
                'scoring_method': 'Banking Hybrid ML (50% ML + 50% Rules)',
                'ml_weight': 0.5,
                'rule_weight': 0.5,
                'persona_summary': 'Tailored to your financial profile',
                'avg_match_score': metrics.get('avg_match_score'),
                'free_products': metrics.get('free_products'),
                'total_annual_cost': metrics.get('total_annual_cost'),
                'estimated_annual_earnings': metrics.get('estimated_annual_earnings'),
                'earning_products': metrics.get('earning_products'),
                'avg_apy': metrics.get('avg_apy'),
                'no_minimum_products': metrics.get('no_minimum_products'),
                'total_products': metrics.get('total_products'),
                'how_ml_works': scoring_methodology.get('how_ml_probability_works', ''),
                'how_rules_work': scoring_methodology.get('how_rules_work', ''),
                'formula': scoring_methodology.get('formula', 'Final Score = 0.5 × ML + 0.5 × Rules'),
            }
        }
        
        execution_time = (datetime.now() - start_time).total_seconds()
        avg_match = metrics.get('avg_match_score', 0)
        avg_fee = metrics.get('avg_annual_fee', metrics.get('avg_fee', 0))
        logger.info(f"✅ Banking Hybrid Agent B completed in {execution_time:.2f}s")
        logger.info(f"   Avg Match Score: {avg_match}%")
        logger.info(f"   Avg Fee: ${avg_fee:.2f}")
        logger.info(f"   Recommendations: {len(recommendations)}")
        
        return {
            "success": True,
            "results": numpy_to_python_types(formatted_results),
            "execution_time_seconds": execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Banking Hybrid Agent B failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/banking/agent_b/explain")
async def explain_banking_recommendation(request: dict = Body(...)):
    """Generate AI explanation for a specific product recommendation (on-demand)"""
    try:
        customer_id = request.get('customer_id')
        product_id = request.get('product_id')
        
        if not customer_id or not product_id:
            raise HTTPException(
                status_code=400,
                detail="Both customer_id and product_id are required"
            )
        
        logger.info(f"💡 Generating AI explanation: {customer_id} + {product_id}")
        
        # Check if Agent A has been executed
        if not system_state['banking']['agent_a_results']:
            raise HTTPException(
                status_code=400,
                detail="Agent A must be executed first"
            )
        
        # Initialize Agent B if needed
        init_banking_agent_b()
        
        if banking_agent_b is None:
            raise HTTPException(
                status_code=500,
                detail="Banking Agent B not initialized"
            )
        
        # Get customer data
        customer = banking_agent_b.customers_df[
            banking_agent_b.customers_df['customer_id'] == customer_id
        ]
        
        if len(customer) == 0:
            raise HTTPException(status_code=404, detail="Customer not found")
        
        customer = customer.iloc[0]
        
        # Get product data
        product = banking_agent_b.products_df[
            banking_agent_b.products_df['product_id'] == product_id
        ]
        
        if len(product) == 0:
            raise HTTPException(status_code=404, detail="Product not found")
        
        product = product.iloc[0]
        
        # Get persona (use 'cluster' column)
        persona_id = customer.get('cluster', customer.get('macro_segment_id', 0))
        persona = banking_agent_b.personas.get(persona_id, {})
        
        if not persona:
            raise HTTPException(status_code=404, detail="Persona not found")
        
        # Get score breakdown using banking 12-factor scorer
        score_breakdown = banking_agent_b.scorer.score_product(
            customer=customer.to_dict(),
            product=product.to_dict(),
            persona=persona
        )
        
        # Generate AI explanation using Together AI
        from utils.together_ai import together_ai
        
        explanation = together_ai.generate_banking_product_explanation(
            customer_profile=customer.to_dict(),
            product=product.to_dict(),
            persona_name=persona['persona_name'],
            score_breakdown=score_breakdown
        )
        
        logger.info(f"✅ Generated AI explanation ({len(explanation)} chars)")
        
        return {
            'success': True,
            'customer_id': customer_id,
            'product_id': product_id,
            'explanation': explanation,
            'score_breakdown': score_breakdown
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error explaining recommendation: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/recommendations/{customer_id}/all")
async def get_all_banking_recommendations(customer_id: str, search_term: str = None):
    """Get all types of recommendations for a banking customer"""
    try:
        result = banking_agent_b.get_all_recommendations(
            customer_id,
            search_term,
            None  # No ChromaDB for now
        )
        
        if not isinstance(result, dict):
            raise ValueError(f"Agent returned invalid result type: {type(result)}")
        
        logger.info(f"📊 Recommendations generated for customer {customer_id}")
        
        # Separate in-stock and out-of-stock products
        def separate_by_stock(products):
            in_stock = []
            out_of_stock = []
            
            for product in products:
                is_in_stock = product.get('in_stock', True)
                if isinstance(is_in_stock, str):
                    is_in_stock = is_in_stock.lower() in ['true', '1', 'yes']
                
                if is_in_stock:
                    in_stock.append(product)
                else:
                    out_of_stock.append(product)
            
            return in_stock, out_of_stock
        
        tailored_in_stock, tailored_out_of_stock = separate_by_stock(
            result.get('tailored_recommendations', [])
        )
        similar_in_stock, similar_out_of_stock = separate_by_stock(
            result.get('similar_products', [])
        )
        segment_in_stock, segment_out_of_stock = separate_by_stock(
            result.get('segment_recommendations', [])
        )
        
        return {
            "success": True,
            "result": {
                "tailored_recommendations": numpy_to_python_types(tailored_in_stock),
                "similar_products": numpy_to_python_types(similar_in_stock),
                "segment_recommendations": numpy_to_python_types(segment_in_stock),
                "out_of_stock_tailored": numpy_to_python_types(tailored_out_of_stock),
                "out_of_stock_similar": numpy_to_python_types(similar_out_of_stock),
                "out_of_stock_segment": numpy_to_python_types(segment_out_of_stock),
                "customer_info": result.get('customer_info', {}),
                "recommendation_metadata": result.get('recommendation_metadata', {})
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting banking recommendations: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/banking/products")
async def list_banking_products():
    """List all banking products"""
    try:
        import pandas as pd
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent
        products_path = project_root / "data" / "preloaded" / "banking" / "products.csv"
        
        if not products_path.exists():
            raise HTTPException(status_code=404, detail="Products catalog not found. Generate data first.")
        
        products_df = pd.read_csv(products_path)
        products = products_df.to_dict('records')
        products = [numpy_to_python_types(product) for product in products]
        
        category_counts = products_df['category'].value_counts().to_dict()
        
        return {
            "success": True,
            "total_products": len(products),
            "categories": category_counts,
            "products": products
        }
        
    except Exception as e:
        logger.error(f"Error listing banking products: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STATIC FILES - Serve Frontend
# ============================================================================
frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.exists(frontend_dist):
    # Mount static assets
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")
    
    # Serve index.html for root and SPA routes
    @app.get("/")
    async def serve_root():
        """Serve frontend root"""
        return FileResponse(os.path.join(frontend_dist, "index.html"))


# ============================================================================
# CHROMADB INITIALIZATION FOR ACADEMY SPORTS
# ============================================================================

@app.post("/api/academy/chromadb/initialize")
async def initialize_academy_chromadb_endpoint(force_recreate: bool = False):
    """
    Initialize ChromaDB collections for Academy Sports products
    
    Args:
        force_recreate: If True, recreate collections even if they exist
        
    Returns:
        Initialization status and metrics
    """
    try:
        from utils.chromadb_academy_init import initialize_academy_chromadb as init_chromadb
        
        logger.info(f"Starting ChromaDB initialization (force_recreate={force_recreate})...")
        
        result = init_chromadb(force_recreate=force_recreate)
        
        return {
            "success": True,
            "result": numpy_to_python_types(result)
        }
        
    except Exception as e:
        logger.error(f"Error initializing ChromaDB: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/academy/chromadb/status")
async def get_chromadb_status():
    """
    Check status of ChromaDB collections for Academy Sports
    
    Returns:
        Status of collections and item counts
    """
    try:
        status = {
            'product_collection': {
                'name': 'academy_products_semantic',
                'exists': False,
                'count': 0
            }
        }
        
        try:
            collection = chroma_client.client.get_collection('academy_products_semantic')
            status['product_collection']['exists'] = True
            status['product_collection']['count'] = collection.count()
        except:
            pass
        
        return {
            "success": True,
            "status": status
        }
        
    except Exception as e:
        logger.error(f"Error checking ChromaDB status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# STARTUP
# ============================================================================
@app.on_event("startup")
async def startup_event():
    """Initialize ChromaDB and print startup banner"""
    logger.info("\n" + "="*80)
    logger.info("🏦 MULTI-INDUSTRY NBA PLATFORM API (Academy Sports + Banking)")
    logger.info("="*80)
    
    # Check for data files
    try:
        from pathlib import Path
        project_root = Path(__file__).parent.parent
        
        # Check Academy Sports data
        academy_path = project_root / "data" / "preloaded" / "academy_sports"
        if (academy_path / "customers.csv").exists():
            logger.info(f"✓ Academy Sports data: {academy_path}")
        else:
            logger.warning(f"⚠️  Academy Sports data not found")
        
        # Check Banking data
        banking_path = project_root / "data" / "preloaded" / "banking"
        if (banking_path / "customers.csv").exists():
            logger.info(f"✓ Banking data: {banking_path}")
        else:
            logger.warning(f"⚠️  Banking data not found. Run: generate_banking_data_5000.bat")
    except Exception as e:
        logger.warning(f"⚠️  Could not check data files: {e}")
    
    logger.info(f"\n📍 Academy Sports API: http://localhost:8002/api/academy/*")
    logger.info(f"📍 Banking API: http://localhost:8002/api/banking/*")
    logger.info(f"📍 ChromaDB stats: http://localhost:8002/api/chromadb/stats")
    logger.info(f"📍 API Docs: http://localhost:8002/docs")
    logger.info(f"\n📍 Frontend UI: http://localhost:5173/")
    logger.info(f"   - Academy: http://localhost:5173/academy/agent-a")
    logger.info(f"   - Banking: http://localhost:5173/banking/agent-a")
    logger.info("="*80 + "\n")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)

  
  
  
  
  
  
