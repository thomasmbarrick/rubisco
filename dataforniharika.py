"""
just run this in the same directory as the CSV i added already. Thank you :)
"""

import pandas as pd
import requests
import os
import time
from pathlib import Path
from urllib.parse import urljoin
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PDBDownloader:
    def __init__(self, output_dir="pdb_files"):
        """
        Initialize PDB downloader
        
        Args:
            output_dir (str): Directory to save PDB files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.base_url = "https://files.rcsb.org/download/"
        self.session = requests.Session()
        
    def download_pdb(self, pdb_id, max_retries=3):
        """
        Download a single PDB file
        
        Args:
            pdb_id (str): PDB identifier (e.g., "1E1G")
            max_retries (int): Maximum number of retry attempts
            
        Returns:
            bool: True if successful, False otherwise
        """
        if not pdb_id or pdb_id == '-' or pd.isna(pdb_id):
            return False
            
        pdb_id = pdb_id.upper().strip()
        filename = f"{pdb_id}.pdb"
        filepath = self.output_dir / filename
        
        # Skip if already exists
        if filepath.exists():
            logger.info(f"PDB {pdb_id} already exists, skipping")
            return True
            
        url = urljoin(self.base_url, filename)
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Downloading PDB {pdb_id} (attempt {attempt + 1}/{max_retries})")
                
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Check if response contains actual PDB data
                if len(response.content) < 100:
                    logger.warning(f"PDB {pdb_id} appears to be empty or invalid")
                    return False
                    
                # Save file
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                    
                logger.info(f"Successfully downloaded PDB {pdb_id}")
                return True
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Attempt {attempt + 1} failed for PDB {pdb_id}: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    
        logger.error(f"Failed to download PDB {pdb_id} after {max_retries} attempts")
        return False
        
    def process_csv(self, csv_file, pdb_column="PDB_wild"):
        """
        Process CSV file and download all PDB files
        
        Args:
            csv_file (str): Path to CSV file
            pdb_column (str): Column name containing PDB IDs
        """
        try:
            # Read CSV
            df = pd.read_csv(csv_file)
            logger.info(f"Loaded CSV with {len(df)} rows")
            
            # Check if column exists
            if pdb_column not in df.columns:
                logger.error(f"Column '{pdb_column}' not found in CSV")
                logger.info(f"Available columns: {list(df.columns)}")
                return
                
            # Get unique PDB IDs
            pdb_ids = df[pdb_column].dropna().unique()
            pdb_ids = [pdb for pdb in pdb_ids if pdb != '-' and str(pdb).strip()]
            
            logger.info(f"Found {len(pdb_ids)} unique PDB IDs to download")
            
            # Download each PDB
            successful = 0
            failed = 0
            
            for i, pdb_id in enumerate(pdb_ids, 1):
                logger.info(f"Processing {i}/{len(pdb_ids)}: {pdb_id}")
                
                if self.download_pdb(pdb_id):
                    successful += 1
                else:
                    failed += 1
                    
                # Add delay between downloads to be respectful
                time.sleep(0.5)
                
            logger.info(f"Download complete. Successful: {successful}, Failed: {failed}")
            
        except Exception as e:
            logger.error(f"Error processing CSV: {e}")
            
    def get_download_stats(self):
        """Get statistics about downloaded files"""
        pdb_files = list(self.output_dir.glob("*.pdb"))
        total_size = sum(f.stat().st_size for f in pdb_files)
        
        return {
            "total_files": len(pdb_files),
            "total_size_mb": total_size / (1024 * 1024),
            "files": [f.name for f in pdb_files]
        }

def main():
    """Main function to run the PDB downloader"""
    # Hardcoded file path
    csv_file = "/Users/thomasbarrick/Desktop/testing shit/dataForNiharika.csv"
    output_dir = "/Users/thomasbarrick/Desktop/testing shit/pdb_files"
    pdb_column = "PDB_wild"
    
    print(f"Processing CSV file: {csv_file}")
    print(f"Output directory: {output_dir}")
    print(f"PDB column: {pdb_column}")
    print("-" * 50)
    
    # Create downloader and process CSV
    downloader = PDBDownloader(output_dir)
    downloader.process_csv(csv_file, pdb_column)
    
    # Show statistics
    stats = downloader.get_download_stats()
    print(f"\nDownload Statistics:")
    print(f"Total files downloaded: {stats['total_files']}")
    print(f"Total size: {stats['total_size_mb']:.2f} MB")
    print(f"Files saved to: {downloader.output_dir}")

if __name__ == "__main__":
    main()

