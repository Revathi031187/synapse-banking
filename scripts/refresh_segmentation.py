"""
Weekly Refresh Script for Academy Sports Segmentation

Runs automatically every Sunday at 2 AM to refresh:
- Macro segmentation (K-Prototypes clustering)
- Micro segmentation for each macro segment
- Update ChromaDB with new assignments

Usage:
    python scripts/refresh_segmentation.py [--dataset-version v1|v2]

Cron setup:
    0 2 * * 0 /path/to/venv/bin/python /path/to/scripts/refresh_segmentation.py
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import logging
import json

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Setup logging
log_dir = project_root / "logs"
log_dir.mkdir(exist_ok=True)
log_file = log_dir / f"refresh_segmentation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def main():
    """Main refresh function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Refresh Academy Sports segmentation')
    parser.add_argument('--dataset-version', type=str, default='v1', choices=['v1', 'v2'],
                        help='Dataset version to use (default: v1)')
    parser.add_argument('--n-clusters', type=int, default=4,
                        help='Number of macro clusters (default: 4)')
    parser.add_argument('--n-micro', type=int, default=4,
                        help='Number of micro segments per macro (default: 4)')
    
    args = parser.parse_args()
    
    logger.info("="*70)
    logger.info("WEEKLY SEGMENTATION REFRESH - Academy Sports")
    logger.info("="*70)
    logger.info(f"Started at: {datetime.now().isoformat()}")
    logger.info(f"Dataset version: {args.dataset_version}")
    logger.info(f"Macro clusters: {args.n_clusters}")
    logger.info(f"Micro segments per macro: {args.n_micro}")
    logger.info("="*70)
    
    try:
        # Step 1: Run Macro Segmentation
        logger.info("\n📊 Step 1: Running Macro Segmentation (K-Prototypes)...")
        from agents.agent_a_academy_chromadb import AgentA_Academy
        
        agent_a = AgentA_Academy()
        macro_result = agent_a.execute({
            'n_clusters': args.n_clusters,
            'gamma': 0.5,
            'dataset_version': args.dataset_version
        })
        
        if 'error' in macro_result:
            logger.error(f"❌ Macro segmentation failed: {macro_result['error']}")
            return 1
        
        logger.info(f"✅ Macro segmentation complete")
        logger.info(f"   - Total customers: {macro_result['total_customers']}")
        logger.info(f"   - Total revenue: ${macro_result['total_revenue']:,.2f}")
        logger.info(f"   - Personas: {len(macro_result['personas'])}")
        
        # Log persona summary
        for cluster_id, persona in macro_result['personas'].items():
            logger.info(f"   • {persona['persona_name']}: {persona['size']} customers, ${persona['revenue_metrics']['total_revenue_12mo']:,.0f} revenue")
        
        # Check constraints
        constraints = macro_result.get('constraints_validation', {})
        if constraints.get('all_constraints_met', True):
            logger.info("✅ All business constraints met")
        else:
            logger.warning(f"⚠️  Some constraints not met: {constraints.get('recommendation', 'N/A')}")
            for failure in constraints.get('constraints_failed', []):
                logger.warning(f"   - {failure['message']}")
        
        # Step 2: Run Micro Segmentation for each macro segment
        logger.info("\n🎯 Step 2: Running Micro Segmentation...")
        from agents.agent_a_academy_micro import AgentA_Academy_Micro
        
        customers_df = macro_result['customers_with_clusters']
        personas = macro_result['personas']
        
        micro_agent = AgentA_Academy_Micro(customers_df, personas)
        micro_results = micro_agent.execute_all_macro_segments(args.n_micro)
        
        if micro_results['status'] == 'success':
            logger.info(f"✅ Micro segmentation complete")
            logger.info(f"   - Total macro segments: {micro_results['total_macro_segments']}")
            logger.info(f"   - Total micro segments: {micro_results['total_micro_segments']}")
            
            # Log micro segment summary
            for macro_id, micro_result in micro_results['micro_segments_by_macro'].items():
                persona_name = personas[macro_id]['persona_name']
                logger.info(f"   • {persona_name}: {micro_result['n_micro_segments']} micro segments")
        else:
            logger.error("❌ Micro segmentation failed")
            return 1
        
        # Step 3: Save results
        logger.info("\n💾 Step 3: Saving results...")
        
        results_dir = project_root / "data" / "results"
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save macro results
        macro_file = results_dir / f"macro_segmentation_{timestamp}.json"
        with open(macro_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'dataset_version': args.dataset_version,
                'n_clusters': args.n_clusters,
                'result': {
                    'status': macro_result['status'],
                    'total_customers': macro_result['total_customers'],
                    'total_revenue': macro_result['total_revenue'],
                    'personas': {
                        str(k): {
                            'persona_name': v['persona_name'],
                            'short_name': v['short_name'],
                            'size': v['size'],
                            'percentage': v['percentage'],
                            'total_revenue': v['revenue_metrics']['total_revenue_12mo'],
                            'avg_customer_value': v['revenue_metrics']['avg_customer_value'],
                            'special_flags': v.get('special_flags', [])
                        }
                        for k, v in macro_result['personas'].items()
                    },
                    'constraints_met': constraints.get('all_constraints_met', True)
                }
            }, f, indent=2)
        
        logger.info(f"   ✓ Macro results saved: {macro_file}")
        
        # Save micro results
        micro_file = results_dir / f"micro_segmentation_{timestamp}.json"
        with open(micro_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'n_micro_per_macro': args.n_micro,
                'result': {
                    'total_macro_segments': micro_results['total_macro_segments'],
                    'total_micro_segments': micro_results['total_micro_segments'],
                    'micro_segments_by_macro': {
                        str(k): {
                            'macro_segment_name': v['macro_segment_name'],
                            'n_micro_segments': v['n_micro_segments'],
                            'micro_segments': {
                                str(mk): {
                                    'segment_name': mv['segment_name'],
                                    'ltv_tier': mv['ltv_tier'],
                                    'size': mv['size'],
                                    'percentage': mv['percentage'],
                                    'total_revenue': mv['revenue_metrics']['total_revenue']
                                }
                                for mk, mv in v['micro_segments'].items()
                            }
                        }
                        for k, v in micro_results['micro_segments_by_macro'].items()
                    }
                }
            }, f, indent=2)
        
        logger.info(f"   ✓ Micro results saved: {micro_file}")
        
        # Save latest results (for API to use)
        latest_macro = results_dir / "macro_segmentation_latest.json"
        latest_micro = results_dir / "micro_segmentation_latest.json"
        
        with open(latest_macro, 'w') as f:
            json.dump(json.load(open(macro_file)), f, indent=2)
        
        with open(latest_micro, 'w') as f:
            json.dump(json.load(open(micro_file)), f, indent=2)
        
        logger.info("   ✓ Latest results updated")
        
        # Step 4: Export for marketing
        logger.info("\n📤 Step 4: Exporting for marketing...")
        
        export_file = results_dir / f"persona_assignments_{timestamp}.csv"
        export_path = agent_a.export_persona_assignments(str(export_file))
        logger.info(f"   ✓ Marketing export saved: {export_path}")
        
        # Summary
        logger.info("\n" + "="*70)
        logger.info("✅ REFRESH COMPLETE")
        logger.info("="*70)
        logger.info(f"Completed at: {datetime.now().isoformat()}")
        logger.info(f"Duration: {(datetime.now() - datetime.fromisoformat(macro_result.get('last_refreshed', datetime.now().isoformat()))).total_seconds():.0f} seconds")
        logger.info(f"Log file: {log_file}")
        logger.info("="*70)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ ERROR: {str(e)}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

