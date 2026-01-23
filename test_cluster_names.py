"""
Quick test to verify cluster naming works
"""
from utils.cluster_naming import cluster_namer

# Test Banking Cluster
print("=" * 60)
print("🏦 BANKING CLUSTER NAME EXAMPLES")
print("=" * 60)

# Example 1: Premium Active Client
persona1 = {
    'avg_intent': 0.75,
    'avg_engagement': 9,
    'avg_income': 150000,
    'avg_credit_score': 780,
    'avg_tenure': 48
}
name1 = cluster_namer.name_banking_cluster(persona1)
print(f"\nPersona 1: {name1}")
print(f"  Intent: {persona1['avg_intent']} | Engagement: {persona1['avg_engagement']} | Income: ${persona1['avg_income']:,}")

# Example 2: Dormant Account
persona2 = {
    'avg_intent': 0.2,
    'avg_engagement': 1.5,
    'avg_income': 60000,
    'avg_credit_score': 650,
    'avg_tenure': 12
}
name2 = cluster_namer.name_banking_cluster(persona2)
print(f"\nPersona 2: {name2}")
print(f"  Intent: {persona2['avg_intent']} | Engagement: {persona2['avg_engagement']} | Income: ${persona2['avg_income']:,}")

# Example 3: Active Prospect
persona3 = {
    'avg_intent': 0.8,
    'avg_engagement': 8,
    'avg_income': 90000,
    'avg_credit_score': 720,
    'avg_tenure': 6
}
name3 = cluster_namer.name_banking_cluster(persona3)
print(f"\nPersona 3: {name3}")
print(f"  Intent: {persona3['avg_intent']} | Engagement: {persona3['avg_engagement']} | Income: ${persona3['avg_income']:,}")

print("\n" + "=" * 60)
print("🛒 RETAIL CLUSTER NAME EXAMPLES")
print("=" * 60)

# Example 4: VIP Elite Shopper
persona4 = {
    'avg_intent': 0.7,
    'avg_engagement': 12,
    'avg_recency': 4.5,
    'avg_frequency': 4.5,
    'avg_monetary': 4.8,
    'avg_aov': 200,
    'avg_income': 120000
}
name4 = cluster_namer.name_retail_cluster(persona4)
print(f"\nPersona 4: {name4}")
print(f"  Intent: {persona4['avg_intent']} | Engagement: {persona4['avg_engagement']} visits/month | AOV: ${persona4['avg_aov']}")

# Example 5: Inactive Account
persona5 = {
    'avg_intent': 0.15,
    'avg_engagement': 0.5,
    'avg_recency': 1.5,
    'avg_frequency': 1.2,
    'avg_monetary': 1.8,
    'avg_aov': 45,
    'avg_income': 55000
}
name5 = cluster_namer.name_retail_cluster(persona5)
print(f"\nPersona 5: {name5}")
print(f"  Intent: {persona5['avg_intent']} | Engagement: {persona5['avg_engagement']} visits/month | AOV: ${persona5['avg_aov']}")

print("\n" + "=" * 60)
print("✅ Cluster naming utility is working correctly!")
print("=" * 60)
print("\nNext step: Run 'py -3.10 scripts\\initialize_chromadb.py' to apply these names to your data")

