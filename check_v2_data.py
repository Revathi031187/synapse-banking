"""Check V2 data quality - should have overlap!"""
import pandas as pd

df = pd.read_csv('data/preloaded/academy_sports/customers_v2.csv')

print("="*80)
print("V2 DATA QUALITY CHECK")
print("="*80)

print(f"\nTotal Customers: {len(df)}")
print(f"\nPersona Distribution:")
print(df['true_persona'].value_counts())

print("\n" + "="*80)
print("OVERLAP CHECK - Search Specificity by Persona")
print("="*80)
print(df.groupby('true_persona')['search_specificity'].agg(['mean', 'std', 'min', 'max']))

print("\n" + "="*80)
print("OVERLAP CHECK - Bundle Affinity by Persona")
print("="*80)
print(df.groupby('true_persona')['bundle_affinity'].agg(['mean', 'std', 'min', 'max']))

print("\n" + "="*80)
print("KEY QUESTION: Do ranges overlap?")
print("="*80)

# Check for overlap
novice = df[df['true_persona'] == 'Novice']
family = df[df['true_persona'] == 'Family_Socializer']
pro = df[df['true_persona'] == 'Seasoned_Pro']

print("\nSearch Specificity Ranges:")
print(f"  Novice: {novice['search_specificity'].min():.2f} - {novice['search_specificity'].max():.2f}")
print(f"  Family: {family['search_specificity'].min():.2f} - {family['search_specificity'].max():.2f}")
print(f"  Pro: {pro['search_specificity'].min():.2f} - {pro['search_specificity'].max():.2f}")

# Check if ranges overlap
novice_max = novice['search_specificity'].max()
family_min = family['search_specificity'].min()
family_max = family['search_specificity'].max()
pro_min = pro['search_specificity'].min()

print(f"\n✓ Novice-Family overlap: {novice_max >= family_min} (Novice max: {novice_max:.2f}, Family min: {family_min:.2f})")
print(f"✓ Family-Pro overlap: {family_max >= pro_min} (Family max: {family_max:.2f}, Pro min: {pro_min:.2f})")

if novice_max < family_min and family_max < pro_min:
    print("\n❌ NO OVERLAP! Data is too clean - this will cause overfitting!")
    print("   V2 should have 10-20% overlap in feature ranges.")
else:
    print("\n✅ Data has overlap - good for realistic testing!")

