"""
Download EIA weekly petroleum data
Requires: EIA API key (get free at https://www.eia.gov/opendata/register.php)
"""

import pandas as pd
import requests
import os

# TODO: Set your EIA API key
# Get from: https://www.eia.gov/opendata/register.php
API_KEY = os.getenv("EIA_API_KEY", "YOUR_API_KEY_HERE")

def download_eia_inventory():
    """Download weekly gasoline inventory data"""
    print("Downloading EIA inventory data...")
    
    # Series ID for Total Motor Gasoline Stocks (Thousand Barrels)
    series_id = "PET.WGTSTUS1.W"
    
    url = f"https://api.eia.gov/v2/petroleum/stoc/wstk/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=weekly&start=2020-10-01"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Parse into dataframe
        df = pd.DataFrame(data['response']['data'])
        df['date'] = pd.to_datetime(df['period'])
        df['inventory_mbbl'] = df['value'].astype(float) / 1000  # Convert to millions
        df = df[['date', 'inventory_mbbl']].sort_values('date')
        
        # Sanity check
        assert df['inventory_mbbl'].min() > 180, "Inventory too low (data error?)"
        assert df['inventory_mbbl'].max() < 350, "Inventory too high (data error?)"
        
        # Save to silver
        os.makedirs('../data/silver', exist_ok=True)
        df.to_parquet('../data/silver/eia_inventory_weekly.parquet', index=False)
        print(f"✓ Downloaded {len(df)} weeks of inventory data")
        return df
        
    except Exception as e:
        print(f"✗ Error downloading inventory: {e}")
        return None


def download_eia_utilization():
    """Download weekly refinery utilization rate"""
    print("Downloading EIA utilization data...")
    
    series_id = "PET.WPULEUS3.W"  # Percent Utilization of Refinery Operable Capacity
    
    url = f"https://api.eia.gov/v2/petroleum/pnp/wiup/data/?api_key={API_KEY}&data[0]=value&facets[series][]={series_id}&frequency=weekly&start=2020-10-01"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        df = pd.DataFrame(data['response']['data'])
        df['date'] = pd.to_datetime(df['period'])
        df['utilization_pct'] = df['value'].astype(float)
        df = df[['date', 'utilization_pct']].sort_values('date')
        
        # Sanity check
        assert df['utilization_pct'].min() > 50, "Utilization too low"
        assert df['utilization_pct'].max() < 100, "Utilization over 100%"
        
        df.to_parquet('../data/silver/eia_utilization_weekly.parquet', index=False)
        print(f"✓ Downloaded {len(df)} weeks of utilization data")
        return df
        
    except Exception as e:
        print(f"✗ Error downloading utilization: {e}")
        return None


def download_eia_imports():
    """Download weekly imports minus exports"""
    print("Downloading EIA imports/exports data...")
    
    # Net imports = Imports - Exports
    imports_series = "PET.WGTIMUS2.W"
    exports_series = "PET.WGTEXUS2.W"
    
    try:
        # Download imports
        url_imports = f"https://api.eia.gov/v2/petroleum/move/wkly/data/?api_key={API_KEY}&data[0]=value&facets[series][]={imports_series}&frequency=weekly&start=2020-10-01"
        imports_data = requests.get(url_imports).json()
        df_imports = pd.DataFrame(imports_data['response']['data'])
        
        # Download exports
        url_exports = f"https://api.eia.gov/v2/petroleum/move/wkly/data/?api_key={API_KEY}&data[0]=value&facets[series][]={exports_series}&frequency=weekly&start=2020-10-01"
        exports_data = requests.get(url_exports).json()
        df_exports = pd.DataFrame(exports_data['response']['data'])
        
        # Merge and calculate net imports
        df_imports['date'] = pd.to_datetime(df_imports['period'])
        df_imports['imports'] = df_imports['value'].astype(float)
        df_exports['date'] = pd.to_datetime(df_exports['period'])
        df_exports['exports'] = df_exports['value'].astype(float)
        
        df = df_imports[['date', 'imports']].merge(df_exports[['date', 'exports']], on='date')
        df['net_imports_kbd'] = df['imports'] - df['exports']  # Thousand barrels per day
        df = df[['date', 'net_imports_kbd']].sort_values('date')
        
        df.to_parquet('../data/silver/eia_imports_weekly.parquet', index=False)
        print(f"✓ Downloaded {len(df)} weeks of import/export data")
        return df
        
    except Exception as e:
        print(f"✗ Error downloading imports: {e}")
        return None


if __name__ == "__main__":
    print("=" * 60)
    print("EIA DATA DOWNLOAD")
    print("=" * 60)
    
    if API_KEY == "YOUR_API_KEY_HERE":
        print("\n⚠️  WARNING: EIA_API_KEY not set!")
        print("Get a free API key at: https://www.eia.gov/opendata/register.php")
        print("Then set it: export EIA_API_KEY='your_key_here'")
        exit(1)
    
    download_eia_inventory()
    download_eia_utilization()
    download_eia_imports()
    
    print("\n✅ EIA data download complete!")
    print("Files saved to: ../data/silver/")
