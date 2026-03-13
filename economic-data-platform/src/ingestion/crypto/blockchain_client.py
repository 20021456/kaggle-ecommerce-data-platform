"""
Blockchain.info API Client for Bitcoin blockchain data.

Blockchain.info provides:
- Bitcoin blockchain statistics
- Block data
- Transaction data
- Address information
- Market prices

API Documentation: https://www.blockchain.com/explorer/api
Rate Limits: No strict limits, but be reasonable
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from src.ingestion.base_client import BaseAPIClient
from src.ingestion.config import settings
from src.utils.helpers import timestamp_to_datetime


class BlockchainClient(BaseAPIClient):
    """
    Client for Blockchain.info Bitcoin data API.
    
    Provides methods to fetch:
    - Network statistics
    - Block information
    - Transaction data
    - Market prices
    - Address data
    
    Example:
        client = BlockchainClient()
        
        # Get network stats
        stats = client.get_stats()
        
        # Get latest block
        block = client.get_latest_block()
        
        # Get market prices
        prices = client.get_ticker()
    """
    
    def __init__(self):
        """Initialize Blockchain.info client."""
        super().__init__(
            base_url=settings.BLOCKCHAIN_INFO_URL,
            api_key=None,  # No API key required
            rate_limit=30,  # Conservative rate limit
            timeout=30,
            max_retries=3,
            cache_ttl=60,  # 1 minute cache
        )
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "blockchain_info"
    
    def health_check(self) -> bool:
        """Check if Blockchain.info API is accessible."""
        try:
            response = self.get("/ticker")
            return "USD" in response
        except Exception as e:
            self.logger.error(f"Health check failed: {e}")
            return False
    
    # =========================================================================
    # STATISTICS ENDPOINTS
    # =========================================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get Bitcoin network statistics.
        
        Returns:
            Network stats including hash rate, difficulty, etc.
        """
        return self.get("/stats", params={"format": "json"})
    
    def get_chart_data(
        self,
        chart_name: str,
        timespan: str = "1year",
        rolling_average: Optional[str] = None,
        start: Optional[str] = None,
        format: str = "json",
    ) -> Dict[str, Any]:
        """
        Get chart data for various Bitcoin metrics.
        
        Available charts:
        - market-price: Bitcoin market price
        - total-bitcoins: Total Bitcoins in circulation
        - n-transactions: Number of transactions per day
        - hash-rate: Network hash rate
        - difficulty: Mining difficulty
        - miners-revenue: Miners revenue
        - transaction-fees: Total transaction fees
        - n-unique-addresses: Unique addresses used
        - mempool-size: Mempool size in bytes
        
        Args:
            chart_name: Name of the chart
            timespan: Time span (e.g., '1year', '30days', 'all')
            rolling_average: Rolling average period
            start: Start date (ISO format)
            format: Response format
            
        Returns:
            Chart data with values over time
        """
        params = {
            "timespan": timespan,
            "format": format,
        }
        
        if rolling_average:
            params["rollingAverage"] = rolling_average
        if start:
            params["start"] = start
        
        return self.get(f"/charts/{chart_name}", params=params)
    
    def get_market_price_chart(
        self,
        timespan: str = "1year",
    ) -> List[Dict[str, Any]]:
        """
        Get Bitcoin market price history.
        
        Args:
            timespan: Time span
            
        Returns:
            List of price data points
        """
        data = self.get_chart_data("market-price", timespan=timespan)
        return self._parse_chart_data(data)
    
    def get_hash_rate_chart(
        self,
        timespan: str = "1year",
    ) -> List[Dict[str, Any]]:
        """
        Get Bitcoin hash rate history.
        
        Args:
            timespan: Time span
            
        Returns:
            List of hash rate data points
        """
        data = self.get_chart_data("hash-rate", timespan=timespan)
        return self._parse_chart_data(data)
    
    def get_difficulty_chart(
        self,
        timespan: str = "1year",
    ) -> List[Dict[str, Any]]:
        """
        Get Bitcoin mining difficulty history.
        
        Args:
            timespan: Time span
            
        Returns:
            List of difficulty data points
        """
        data = self.get_chart_data("difficulty", timespan=timespan)
        return self._parse_chart_data(data)
    
    def get_transactions_chart(
        self,
        timespan: str = "1year",
    ) -> List[Dict[str, Any]]:
        """
        Get daily transaction count history.
        
        Args:
            timespan: Time span
            
        Returns:
            List of transaction count data points
        """
        data = self.get_chart_data("n-transactions", timespan=timespan)
        return self._parse_chart_data(data)
    
    # =========================================================================
    # MARKET DATA ENDPOINTS
    # =========================================================================
    
    def get_ticker(self) -> Dict[str, Dict[str, Any]]:
        """
        Get current Bitcoin price in multiple currencies.
        
        Returns:
            Dict mapping currencies to price data
        """
        return self.get("/ticker")
    
    def get_btc_price_usd(self) -> float:
        """
        Get current Bitcoin price in USD.
        
        Returns:
            Current BTC/USD price
        """
        ticker = self.get_ticker()
        return ticker.get("USD", {}).get("last", 0.0)
    
    # =========================================================================
    # BLOCK ENDPOINTS
    # =========================================================================
    
    def get_latest_block(self) -> Dict[str, Any]:
        """
        Get information about the latest block.
        
        Returns:
            Latest block data
        """
        return self.get("/latestblock")
    
    def get_block(self, block_hash: str) -> Dict[str, Any]:
        """
        Get information about a specific block.
        
        Args:
            block_hash: Block hash
            
        Returns:
            Block data
        """
        return self.get(f"/rawblock/{block_hash}")
    
    def get_block_height(self, height: int) -> List[Dict[str, Any]]:
        """
        Get blocks at a specific height.
        
        Args:
            height: Block height
            
        Returns:
            List of blocks at the height
        """
        response = self.get(f"/block-height/{height}", params={"format": "json"})
        return response.get("blocks", [])
    
    def get_blocks_for_day(self, timestamp_ms: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get blocks mined on a specific day.
        
        Args:
            timestamp_ms: Day timestamp in milliseconds (default: today)
            
        Returns:
            List of blocks
        """
        params = {"format": "json"}
        if timestamp_ms:
            params["time"] = timestamp_ms
        
        response = self.get("/blocks", params=params)
        return response.get("blocks", [])
    
    # =========================================================================
    # TRANSACTION ENDPOINTS
    # =========================================================================
    
    def get_transaction(self, tx_hash: str) -> Dict[str, Any]:
        """
        Get information about a specific transaction.
        
        Args:
            tx_hash: Transaction hash
            
        Returns:
            Transaction data
        """
        return self.get(f"/rawtx/{tx_hash}")
    
    def get_unconfirmed_transactions(self) -> Dict[str, Any]:
        """
        Get current unconfirmed transactions.
        
        Returns:
            Unconfirmed transactions data
        """
        return self.get("/unconfirmed-transactions", params={"format": "json"})
    
    # =========================================================================
    # ADDRESS ENDPOINTS
    # =========================================================================
    
    def get_address(
        self,
        address: str,
        limit: int = 50,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Get information about a Bitcoin address.
        
        Args:
            address: Bitcoin address
            limit: Number of transactions to return
            offset: Transaction offset
            
        Returns:
            Address data with transactions
        """
        params = {
            "limit": limit,
            "offset": offset,
            "format": "json",
        }
        
        return self.get(f"/rawaddr/{address}", params=params)
    
    def get_address_balance(self, address: str) -> int:
        """
        Get balance of a Bitcoin address in satoshis.
        
        Args:
            address: Bitcoin address
            
        Returns:
            Balance in satoshis
        """
        response = self.get(f"/balance", params={"active": address})
        return response.get(address, {}).get("final_balance", 0)
    
    def get_multi_address(
        self,
        addresses: List[str],
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Get information about multiple addresses.
        
        Args:
            addresses: List of Bitcoin addresses
            limit: Number of transactions per address
            
        Returns:
            Multi-address data
        """
        params = {
            "active": "|".join(addresses),
            "limit": limit,
        }
        
        return self.get("/multiaddr", params=params)
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _parse_chart_data(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse chart data into standardized format.
        
        Args:
            data: Raw chart data
            
        Returns:
            List of data points with timestamp and value
        """
        values = data.get("values", [])
        result = []
        
        for item in values:
            record = {
                "timestamp": item.get("x"),
                "datetime": timestamp_to_datetime(item.get("x")),
                "value": item.get("y"),
            }
            result.append(record)
        
        return result
    
    def get_network_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive Bitcoin network summary.
        
        Returns:
            Summary of key network metrics
        """
        stats = self.get_stats()
        ticker = self.get_ticker()
        latest_block = self.get_latest_block()
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "price_usd": ticker.get("USD", {}).get("last"),
            "market_cap_usd": stats.get("market_price_usd", 0) * stats.get("totalbc", 0) / 1e8,
            "hash_rate": stats.get("hash_rate"),
            "difficulty": stats.get("difficulty"),
            "total_btc": stats.get("totalbc", 0) / 1e8,
            "block_height": latest_block.get("height"),
            "transactions_24h": stats.get("n_tx"),
            "btc_sent_24h": stats.get("total_btc_sent", 0) / 1e8,
            "miners_revenue_24h": stats.get("miners_revenue_usd"),
            "n_blocks_mined_24h": stats.get("n_blocks_total"),
            "mempool_size": stats.get("mempool_bytes"),
            "estimated_transaction_volume": stats.get("estimated_btc_sent", 0) / 1e8,
        }
