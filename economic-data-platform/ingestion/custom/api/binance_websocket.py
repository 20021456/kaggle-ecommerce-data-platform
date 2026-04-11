"""
Binance WebSocket Client for real-time cryptocurrency data.

Binance provides real-time market data through WebSocket streams:
- Trade streams: Real-time trades
- Kline/Candlestick streams: OHLCV data
- Ticker streams: 24hr rolling window statistics
- Book Ticker: Best bid/ask prices
- Depth streams: Order book updates

API Documentation: https://binance-docs.github.io/apidocs/spot/en/#websocket-market-streams
"""

import asyncio
import json
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum

import websockets
from websockets.exceptions import ConnectionClosed

from src.ingestion.config import settings
from src.utils.logger import get_logger
from src.utils.helpers import timestamp_to_datetime


class StreamType(Enum):
    """Binance WebSocket stream types."""
    TRADE = "trade"
    AGG_TRADE = "aggTrade"
    KLINE = "kline"
    MINI_TICKER = "miniTicker"
    TICKER = "ticker"
    BOOK_TICKER = "bookTicker"
    DEPTH = "depth"
    DEPTH5 = "depth5"
    DEPTH10 = "depth10"
    DEPTH20 = "depth20"


class KlineInterval(Enum):
    """Kline/Candlestick intervals."""
    MINUTE_1 = "1m"
    MINUTE_3 = "3m"
    MINUTE_5 = "5m"
    MINUTE_15 = "15m"
    MINUTE_30 = "30m"
    HOUR_1 = "1h"
    HOUR_2 = "2h"
    HOUR_4 = "4h"
    HOUR_6 = "6h"
    HOUR_8 = "8h"
    HOUR_12 = "12h"
    DAY_1 = "1d"
    DAY_3 = "3d"
    WEEK_1 = "1w"
    MONTH_1 = "1M"


class BinanceWebSocket:
    """
    Binance WebSocket client for real-time market data streaming.
    
    Supports subscribing to multiple streams and processing data
    through callback functions.
    
    Example:
        async def on_trade(data):
            print(f"Trade: {data}")
        
        ws = BinanceWebSocket()
        await ws.connect()
        await ws.subscribe_trades(['btcusdt', 'ethusdt'], callback=on_trade)
        await ws.run_forever()
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
    ):
        """
        Initialize Binance WebSocket client.
        
        Args:
            base_url: WebSocket base URL (default from settings)
            api_key: Binance API key (optional, for authenticated streams)
            api_secret: Binance API secret (optional)
        """
        self.base_url = base_url or settings.BINANCE_WS_URL
        self.api_key = api_key or settings.BINANCE_API_KEY
        self.api_secret = api_secret or settings.BINANCE_API_SECRET
        
        self.logger = get_logger(self.__class__.__name__)
        
        self._websocket: Optional[websockets.WebSocketClientProtocol] = None
        self._subscriptions: Dict[str, Callable] = {}
        self._running = False
        self._reconnect_attempts = 0
        self._max_reconnect_attempts = 5
        self._reconnect_delay = 5  # seconds
    
    def get_source_name(self) -> str:
        """Return source name."""
        return "binance"
    
    def _build_stream_url(self, streams: List[str]) -> str:
        """
        Build the WebSocket URL for multiple streams.
        
        Args:
            streams: List of stream names
            
        Returns:
            Full WebSocket URL
        """
        if len(streams) == 1:
            return f"{self.base_url}/{streams[0]}"
        else:
            combined = "/".join(streams)
            return f"{self.base_url}/stream?streams={combined}"
    
    @staticmethod
    def get_trade_stream(symbol: str) -> str:
        """Get trade stream name for a symbol."""
        return f"{symbol.lower()}@trade"
    
    @staticmethod
    def get_agg_trade_stream(symbol: str) -> str:
        """Get aggregated trade stream name."""
        return f"{symbol.lower()}@aggTrade"
    
    @staticmethod
    def get_kline_stream(symbol: str, interval: Union[str, KlineInterval]) -> str:
        """Get kline/candlestick stream name."""
        if isinstance(interval, KlineInterval):
            interval = interval.value
        return f"{symbol.lower()}@kline_{interval}"
    
    @staticmethod
    def get_ticker_stream(symbol: str) -> str:
        """Get 24hr ticker stream name."""
        return f"{symbol.lower()}@ticker"
    
    @staticmethod
    def get_mini_ticker_stream(symbol: str) -> str:
        """Get mini ticker stream name."""
        return f"{symbol.lower()}@miniTicker"
    
    @staticmethod
    def get_book_ticker_stream(symbol: str) -> str:
        """Get book ticker stream name."""
        return f"{symbol.lower()}@bookTicker"
    
    @staticmethod
    def get_depth_stream(symbol: str, levels: int = 10) -> str:
        """Get depth/order book stream name."""
        return f"{symbol.lower()}@depth{levels}"
    
    @staticmethod
    def get_all_tickers_stream() -> str:
        """Get stream for all market tickers."""
        return "!ticker@arr"
    
    @staticmethod
    def get_all_mini_tickers_stream() -> str:
        """Get stream for all mini tickers."""
        return "!miniTicker@arr"
    
    async def connect(self, streams: List[str]) -> None:
        """
        Connect to Binance WebSocket.
        
        Args:
            streams: List of stream names to subscribe to
        """
        url = self._build_stream_url(streams)
        
        self.logger.info(f"Connecting to Binance WebSocket: {url}")
        
        try:
            self._websocket = await websockets.connect(
                url,
                ping_interval=20,
                ping_timeout=10,
            )
            self._running = True
            self._reconnect_attempts = 0
            self.logger.info("Connected to Binance WebSocket")
            
        except Exception as e:
            self.logger.error(f"Failed to connect: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Disconnect from WebSocket."""
        self._running = False
        
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        self.logger.info("Disconnected from Binance WebSocket")
    
    async def _reconnect(self, streams: List[str]) -> None:
        """Attempt to reconnect to WebSocket."""
        while self._reconnect_attempts < self._max_reconnect_attempts and self._running:
            self._reconnect_attempts += 1
            delay = self._reconnect_delay * self._reconnect_attempts
            
            self.logger.warning(
                f"Attempting reconnect ({self._reconnect_attempts}/{self._max_reconnect_attempts}) "
                f"in {delay}s..."
            )
            
            await asyncio.sleep(delay)
            
            try:
                await self.connect(streams)
                return
            except Exception as e:
                self.logger.error(f"Reconnect failed: {e}")
        
        self.logger.error("Max reconnect attempts reached")
        self._running = False
    
    def register_callback(
        self,
        stream_type: str,
        callback: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Register a callback for a stream type.
        
        Args:
            stream_type: Stream type identifier
            callback: Async or sync callback function
        """
        self._subscriptions[stream_type] = callback
    
    async def _process_message(self, message: str) -> None:
        """
        Process incoming WebSocket message.
        
        Args:
            message: Raw JSON message string
        """
        try:
            data = json.loads(message)
            
            # Combined stream format
            if "stream" in data and "data" in data:
                stream = data["stream"]
                payload = data["data"]
            else:
                # Single stream format
                stream = data.get("e", "unknown")
                payload = data
            
            # Find matching callback
            for stream_type, callback in self._subscriptions.items():
                if stream_type in stream or stream_type == stream:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(payload)
                    else:
                        callback(payload)
                    break
            
        except json.JSONDecodeError as e:
            self.logger.error(f"Failed to parse message: {e}")
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
    
    async def run(self, streams: List[str]) -> None:
        """
        Run the WebSocket client.
        
        Args:
            streams: List of stream names
        """
        await self.connect(streams)
        
        while self._running:
            try:
                if self._websocket is None:
                    await self._reconnect(streams)
                    continue
                
                message = await self._websocket.recv()
                await self._process_message(message)
                
            except ConnectionClosed as e:
                self.logger.warning(f"Connection closed: {e}")
                if self._running:
                    await self._reconnect(streams)
                    
            except Exception as e:
                self.logger.error(f"Error in run loop: {e}")
                if self._running:
                    await asyncio.sleep(1)
    
    async def subscribe_trades(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Subscribe to trade streams for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols (e.g., ['btcusdt', 'ethusdt'])
            callback: Callback function to process trade data
        """
        streams = [self.get_trade_stream(s) for s in symbols]
        self.register_callback("trade", callback)
        await self.run(streams)
    
    async def subscribe_klines(
        self,
        symbols: List[str],
        interval: Union[str, KlineInterval],
        callback: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Subscribe to kline/candlestick streams.
        
        Args:
            symbols: List of trading pair symbols
            interval: Kline interval
            callback: Callback function to process kline data
        """
        streams = [self.get_kline_stream(s, interval) for s in symbols]
        self.register_callback("kline", callback)
        await self.run(streams)
    
    async def subscribe_tickers(
        self,
        symbols: List[str],
        callback: Callable[[Dict[str, Any]], Any],
    ) -> None:
        """
        Subscribe to ticker streams for multiple symbols.
        
        Args:
            symbols: List of trading pair symbols
            callback: Callback function to process ticker data
        """
        streams = [self.get_ticker_stream(s) for s in symbols]
        self.register_callback("ticker", callback)
        await self.run(streams)
    
    async def subscribe_all_tickers(
        self,
        callback: Callable[[List[Dict[str, Any]]], Any],
    ) -> None:
        """
        Subscribe to all market tickers.
        
        Args:
            callback: Callback function to process all tickers
        """
        streams = [self.get_all_tickers_stream()]
        self.register_callback("!ticker@arr", callback)
        await self.run(streams)
    
    @staticmethod
    def parse_trade(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw trade data into standardized format.
        
        Args:
            data: Raw trade data from WebSocket
            
        Returns:
            Parsed trade record
        """
        return {
            "event_type": data.get("e"),
            "event_time": timestamp_to_datetime(data.get("E")),
            "symbol": data.get("s"),
            "trade_id": data.get("t"),
            "price": float(data.get("p", 0)),
            "quantity": float(data.get("q", 0)),
            "buyer_order_id": data.get("b"),
            "seller_order_id": data.get("a"),
            "trade_time": timestamp_to_datetime(data.get("T")),
            "is_buyer_maker": data.get("m"),
        }
    
    @staticmethod
    def parse_kline(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw kline data into standardized format.
        
        Args:
            data: Raw kline data from WebSocket
            
        Returns:
            Parsed kline/candlestick record
        """
        k = data.get("k", {})
        return {
            "event_type": data.get("e"),
            "event_time": timestamp_to_datetime(data.get("E")),
            "symbol": data.get("s"),
            "interval": k.get("i"),
            "open_time": timestamp_to_datetime(k.get("t")),
            "close_time": timestamp_to_datetime(k.get("T")),
            "open": float(k.get("o", 0)),
            "high": float(k.get("h", 0)),
            "low": float(k.get("l", 0)),
            "close": float(k.get("c", 0)),
            "volume": float(k.get("v", 0)),
            "quote_volume": float(k.get("q", 0)),
            "trades_count": k.get("n"),
            "is_closed": k.get("x"),
        }
    
    @staticmethod
    def parse_ticker(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse raw ticker data into standardized format.
        
        Args:
            data: Raw ticker data from WebSocket
            
        Returns:
            Parsed 24hr ticker record
        """
        return {
            "event_type": data.get("e"),
            "event_time": timestamp_to_datetime(data.get("E")),
            "symbol": data.get("s"),
            "price_change": float(data.get("p", 0)),
            "price_change_percent": float(data.get("P", 0)),
            "weighted_avg_price": float(data.get("w", 0)),
            "prev_close_price": float(data.get("x", 0)),
            "last_price": float(data.get("c", 0)),
            "last_quantity": float(data.get("Q", 0)),
            "bid_price": float(data.get("b", 0)),
            "bid_quantity": float(data.get("B", 0)),
            "ask_price": float(data.get("a", 0)),
            "ask_quantity": float(data.get("A", 0)),
            "open_price": float(data.get("o", 0)),
            "high_price": float(data.get("h", 0)),
            "low_price": float(data.get("l", 0)),
            "volume": float(data.get("v", 0)),
            "quote_volume": float(data.get("q", 0)),
            "open_time": timestamp_to_datetime(data.get("O")),
            "close_time": timestamp_to_datetime(data.get("C")),
            "trades_count": data.get("n"),
        }
