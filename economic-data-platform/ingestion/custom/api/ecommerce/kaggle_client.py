"""Kaggle API client for downloading the Olist Brazilian E-Commerce dataset.

Downloads the dataset from Kaggle, extracts CSVs, and provides metadata.
Requires KAGGLE_USERNAME and KAGGLE_KEY environment variables (or ~/.kaggle/kaggle.json).

Usage:
    client = KaggleClient()
    client.download_dataset()            # → data/raw/olist/
    tables = client.extract_csvs()       # → list of CSV paths
    meta = client.get_dataset_metadata() # → dict with dataset info
"""

from __future__ import annotations

import json
import logging
import os
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

DATASET_SLUG = "olistbr/brazilian-ecommerce"
DEFAULT_DATA_DIR = "data/raw/olist"

# Expected CSV files in the Olist dataset
EXPECTED_FILES = [
    "olist_orders_dataset.csv",
    "olist_order_items_dataset.csv",
    "olist_customers_dataset.csv",
    "olist_products_dataset.csv",
    "olist_sellers_dataset.csv",
    "olist_order_payments_dataset.csv",
    "olist_order_reviews_dataset.csv",
    "olist_geolocation_dataset.csv",
    "product_category_name_translation.csv",
]


class KaggleClient:
    """Client for downloading and managing the Olist dataset from Kaggle."""

    def __init__(
        self,
        data_dir: str = DEFAULT_DATA_DIR,
        dataset_slug: str = DATASET_SLUG,
    ) -> None:
        self.data_dir = Path(data_dir)
        self.dataset_slug = dataset_slug
        self._api = None

    # ------------------------------------------------------------------
    # Lazy Kaggle API initialization
    # ------------------------------------------------------------------

    def _get_api(self):
        """Lazy-load the Kaggle API client."""
        if self._api is not None:
            return self._api
        try:
            from kaggle.api.kaggle_api_extended import KaggleApi

            api = KaggleApi()
            api.authenticate()
            self._api = api
            logger.info("Kaggle API authenticated successfully")
            return api
        except ImportError:
            raise RuntimeError(
                "kaggle package not installed. Run: pip install kaggle"
            )
        except Exception as exc:
            raise RuntimeError(
                f"Kaggle authentication failed: {exc}. "
                "Set KAGGLE_USERNAME and KAGGLE_KEY env vars or create ~/.kaggle/kaggle.json"
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def download_dataset(self, force: bool = False) -> Path:
        """Download the Olist dataset from Kaggle to data_dir.

        Args:
            force: Re-download even if files already exist.

        Returns:
            Path to the data directory containing extracted CSVs.
        """
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Skip if already downloaded (check for at least one expected file)
        if not force and self._is_already_downloaded():
            logger.info(
                "Olist dataset already exists at %s (use force=True to re-download)",
                self.data_dir,
            )
            return self.data_dir

        logger.info("Downloading %s from Kaggle...", self.dataset_slug)
        api = self._get_api()
        api.dataset_download_files(
            self.dataset_slug,
            path=str(self.data_dir),
            unzip=True,
        )
        logger.info("Dataset downloaded and extracted to %s", self.data_dir)
        return self.data_dir

    def extract_csvs(self, zip_path: Optional[str] = None) -> List[Path]:
        """Extract CSVs from a zip file (if download was not auto-unzipped).

        Args:
            zip_path: Path to the zip file. Auto-detected if None.

        Returns:
            List of extracted CSV file paths.
        """
        if zip_path is None:
            # Look for zip in data_dir or project root
            candidates = [
                self.data_dir / "brazilian-ecommerce.zip",
                Path("olist_dataset.zip"),
            ]
            zip_path_resolved = None
            for c in candidates:
                if c.exists():
                    zip_path_resolved = c
                    break
            if zip_path_resolved is None:
                # CSVs may already be extracted
                existing = self._find_existing_csvs()
                if existing:
                    logger.info("CSVs already extracted: %d files found", len(existing))
                    return existing
                raise FileNotFoundError(
                    "No zip file or extracted CSVs found. Run download_dataset() first."
                )
        else:
            zip_path_resolved = Path(zip_path)

        logger.info("Extracting CSVs from %s...", zip_path_resolved)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        with zipfile.ZipFile(zip_path_resolved, "r") as zf:
            zf.extractall(self.data_dir)

        extracted = self._find_existing_csvs()
        logger.info("Extracted %d CSV files to %s", len(extracted), self.data_dir)
        return extracted

    def get_dataset_metadata(self) -> Dict[str, Any]:
        """Get metadata about the Olist dataset.

        Returns:
            Dict with dataset info: slug, title, file count, sizes, etc.
        """
        meta: Dict[str, Any] = {
            "slug": self.dataset_slug,
            "title": "Brazilian E-Commerce Public Dataset by Olist",
            "source": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
            "data_dir": str(self.data_dir),
            "expected_files": EXPECTED_FILES,
            "file_count": len(EXPECTED_FILES),
        }

        # Add actual file info if downloaded
        existing = self._find_existing_csvs()
        file_info = []
        total_size = 0
        for fp in existing:
            size = fp.stat().st_size
            total_size += size
            file_info.append({
                "name": fp.name,
                "size_bytes": size,
                "size_mb": round(size / 1_048_576, 2),
            })

        meta["downloaded"] = len(existing) > 0
        meta["files_found"] = len(existing)
        meta["files"] = file_info
        meta["total_size_mb"] = round(total_size / 1_048_576, 2)

        # Try to get remote metadata from Kaggle API
        try:
            api = self._get_api()
            owner, name = self.dataset_slug.split("/")
            ds_list = api.dataset_list(search=name, user=owner)
            if ds_list:
                ds = ds_list[0]
                meta["kaggle_info"] = {
                    "total_bytes": getattr(ds, "totalBytes", None),
                    "usability_rating": getattr(ds, "usabilityRating", None),
                    "last_updated": str(getattr(ds, "lastUpdated", "")),
                }
        except Exception as exc:
            logger.debug("Could not fetch remote metadata: %s", exc)

        return meta

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_already_downloaded(self) -> bool:
        """Check if at least 7 of 9 expected CSV files exist."""
        found = sum(
            1 for f in EXPECTED_FILES if (self.data_dir / f).exists()
        )
        return found >= 7

    def _find_existing_csvs(self) -> List[Path]:
        """Find all CSV files in data_dir."""
        if not self.data_dir.exists():
            return []
        return sorted(self.data_dir.glob("*.csv"))
