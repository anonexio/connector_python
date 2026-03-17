"""AnonEx WebSocket Client."""

import hashlib
import hmac
import json
import threading
import time
import uuid
from typing import Any, Callable, Dict, List, Optional

import websocket

from .exceptions import AnonExConnectionError


class AnonExWebSocket:
    """WebSocket client for the AnonEx exchange.

    Supports JSON-RPC 2.0 protocol for real-time market data and trading.

    Usage:
        ws = AnonExWebSocket()

        @ws.on('ticker')
        def on_ticker(data):
            print(data)

        ws.connect()
        ws.subscribe_ticker('BTC/USDT')

        # Authenticated usage
        ws = AnonExWebSocket(api_key='key', api_secret='secret')
        ws.connect()
        ws.login()
        ws.subscribe_reports()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        ws_url: str = 'wss://api.anonex.io',
        reconnect: bool = True,
        reconnect_interval: int = 5,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.ws_url = ws_url
        self.reconnect = reconnect
        self.reconnect_interval = reconnect_interval

        self._ws: Optional[websocket.WebSocketApp] = None
        self._thread: Optional[threading.Thread] = None
        self._callbacks: Dict[str, List[Callable]] = {}
        self._response_handlers: Dict[int, Callable] = {}
        self._msg_id = 0
        self._connected = False
        self._should_reconnect = True

    def _next_id(self) -> int:
        self._msg_id += 1
        return self._msg_id

    def on(self, event: str) -> Callable:
        """Decorator to register an event handler.

        Events: ticker, orderbook, trades, candles, reports, balances, transfers,
                connected, disconnected, error, message
        """
        def decorator(func: Callable) -> Callable:
            if event not in self._callbacks:
                self._callbacks[event] = []
            self._callbacks[event].append(func)
            return func
        return decorator

    def add_listener(self, event: str, callback: Callable):
        """Register an event handler."""
        if event not in self._callbacks:
            self._callbacks[event] = []
        self._callbacks[event].append(callback)

    def _emit(self, event: str, data: Any = None):
        """Emit an event to registered handlers."""
        for cb in self._callbacks.get(event, []):
            try:
                cb(data)
            except Exception as e:
                self._emit('error', e)

    def _on_open(self, ws):
        self._connected = True
        self._emit('connected', None)

    def _on_close(self, ws, close_status_code, close_msg):
        self._connected = False
        self._emit('disconnected', {'code': close_status_code, 'message': close_msg})
        if self.reconnect and self._should_reconnect:
            time.sleep(self.reconnect_interval)
            self._do_connect()

    def _on_error(self, ws, error):
        self._emit('error', error)

    def _on_message(self, ws, message):
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            return

        self._emit('message', data)

        # Handle response to a specific request
        msg_id = data.get('id')
        if msg_id and msg_id in self._response_handlers:
            handler = self._response_handlers.pop(msg_id)
            handler(data)

        # Route by method
        method = data.get('method', '')
        if method == 'ticker':
            self._emit('ticker', data.get('params', data))
        elif method == 'snapshotOrderbook' or method == 'updateOrderbook':
            self._emit('orderbook', data.get('params', data))
        elif method == 'snapshotTrades' or method == 'updateTrades':
            self._emit('trades', data.get('params', data))
        elif method == 'snapshotCandles' or method == 'updateCandles':
            self._emit('candles', data.get('params', data))
        elif method == 'report':
            self._emit('reports', data.get('params', data))
        elif method == 'balancereport':
            self._emit('balances', data.get('params', data))
        elif method == 'transferreport':
            self._emit('transfers', data.get('params', data))
        elif method == 'pong':
            self._emit('pong', data)

    def _do_connect(self):
        self._ws = websocket.WebSocketApp(
            self.ws_url,
            on_open=self._on_open,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_message,
        )
        self._thread = threading.Thread(target=self._ws.run_forever, daemon=True)
        self._thread.start()

    def connect(self):
        """Connect to the WebSocket server."""
        self._should_reconnect = True
        self._do_connect()
        # Wait for connection
        timeout = 10
        start = time.time()
        while not self._connected and time.time() - start < timeout:
            time.sleep(0.1)
        if not self._connected:
            raise AnonExConnectionError('WebSocket connection timed out')

    def disconnect(self):
        """Disconnect from the WebSocket server."""
        self._should_reconnect = False
        if self._ws:
            self._ws.close()

    def send(self, method: str, params: Optional[Dict] = None,
             callback: Optional[Callable] = None) -> int:
        """Send a JSON-RPC message. Returns the message ID."""
        msg_id = self._next_id()
        msg = {'method': method, 'params': params or {}, 'id': msg_id}
        if callback:
            self._response_handlers[msg_id] = callback
        if self._ws:
            self._ws.send(json.dumps(msg))
        return msg_id

    # ========================
    #  Public Methods
    # ========================

    def ping(self):
        """Send a ping."""
        self.send('ping')

    def subscribe_ticker(self, symbol: str, callback: Optional[Callable] = None):
        """Subscribe to ticker updates for a symbol (e.g. 'BTC/USDT')."""
        self.send('subscribeTicker', {'symbol': symbol}, callback)

    def subscribe_only_tickers(self, symbols: List[str], callback: Optional[Callable] = None):
        """Subscribe to only the specified tickers (replaces previous subscriptions)."""
        self.send('subscribeOnlyTickers', {'symbols': symbols}, callback)

    def unsubscribe_ticker(self, symbol: str):
        """Unsubscribe from ticker updates."""
        self.send('unsubscribeTicker', {'symbol': symbol})

    def subscribe_orderbook(self, symbol: str, limit: int = 100, callback: Optional[Callable] = None):
        """Subscribe to orderbook updates."""
        self.send('subscribeOrderbook', {'symbol': symbol, 'limit': limit}, callback)

    def unsubscribe_orderbook(self, symbol: str):
        """Unsubscribe from orderbook updates."""
        self.send('unsubscribeOrderbook', {'symbol': symbol})

    def subscribe_trades(self, symbol: str, callback: Optional[Callable] = None):
        """Subscribe to trade updates."""
        self.send('subscribeTrades', {'symbol': symbol}, callback)

    def unsubscribe_trades(self, symbol: str):
        """Unsubscribe from trade updates."""
        self.send('unsubscribeTrades', {'symbol': symbol})

    def subscribe_candles(self, symbol: str, period: int = 5, callback: Optional[Callable] = None):
        """Subscribe to candle updates. period in minutes."""
        self.send('subscribeCandles', {'symbol': symbol, 'period': period}, callback)

    def unsubscribe_candles(self, symbol: str, period: int = 5):
        """Unsubscribe from candle updates."""
        self.send('unsubscribeCandles', {'symbol': symbol, 'period': period})

    def get_asset(self, ticker: str, callback: Optional[Callable] = None):
        """Get asset info via WebSocket."""
        self.send('getAsset', {'ticker': ticker}, callback)

    def get_assets(self, callback: Optional[Callable] = None):
        """Get all assets via WebSocket."""
        self.send('getAssets', {}, callback)

    def get_market(self, symbol: str, callback: Optional[Callable] = None):
        """Get market info via WebSocket."""
        self.send('getMarket', {'symbol': symbol}, callback)

    def get_markets(self, callback: Optional[Callable] = None):
        """Get all markets via WebSocket."""
        self.send('getMarkets', {}, callback)

    # ========================
    #  Authenticated Methods
    # ========================

    def login(self, callback: Optional[Callable] = None):
        """Authenticate the WebSocket connection using API credentials."""
        if not self.api_key or not self.api_secret:
            raise AnonExConnectionError('API key and secret required for login')

        self.send('login', {
            'algo': 'BASIC',
            'pKey': self.api_key,
            'sKey': self.api_secret,
        }, callback)

    def get_trading_balance(self, callback: Optional[Callable] = None):
        """Get trading balances (requires login)."""
        self.send('getTradingBalance', {}, callback)

    def get_balance_values(self, callback: Optional[Callable] = None):
        """Get balance values in USD (requires login)."""
        self.send('getBalanceValues', {}, callback)

    def subscribe_reports(self, callback: Optional[Callable] = None):
        """Subscribe to order execution reports (requires login)."""
        self.send('subscribeReports', {}, callback)

    def subscribe_sub_account_reports(self, callback: Optional[Callable] = None):
        """Subscribe to sub-account order reports (requires login)."""
        self.send('subscribeSubAccountReports', {}, callback)

    def subscribe_balances(self, callback: Optional[Callable] = None):
        """Subscribe to balance updates (requires login)."""
        self.send('subscribeBalances', {}, callback)

    def subscribe_sub_account_balances(self, callback: Optional[Callable] = None):
        """Subscribe to sub-account balance updates (requires login)."""
        self.send('subscribeSubAccountBalances', {}, callback)

    def subscribe_transfers(self, callback: Optional[Callable] = None):
        """Subscribe to transfer updates (requires login)."""
        self.send('subscribeTransfers', {}, callback)

    def subscribe_sub_account_transfers(self, callback: Optional[Callable] = None):
        """Subscribe to sub-account transfer updates (requires login)."""
        self.send('subscribeSubAccountTransfers', {}, callback)

    def new_order(self, symbol: str, side: str, type: str = 'limit',
                  quantity: str = '0', price: str = '0',
                  user_provided_id: str = None, strict_validate: bool = False,
                  quote_order_qty: str = None,
                  callback: Optional[Callable] = None):
        """Place a new order via WebSocket (requires login).
        For market buy orders, pass quote_order_qty to specify total spend in quote currency."""
        params = {
            'symbol': symbol, 'side': side, 'type': type,
            'quantity': quantity, 'price': price, 'strictValidate': strict_validate
        }
        if user_provided_id:
            params['userProvidedId'] = user_provided_id
        if quote_order_qty:
            params['quoteOrderQty'] = quote_order_qty
        self.send('newOrder', params, callback)

    def new_trigger_order(self, symbol: str, stoptriggertype: str, stoptriggerprice: str,
                          stoporderside: str, stopordertype: str = 'limit',
                          stoporderquantity: str = '0', stoporderprice: str = '0',
                          stoporderqtyismax: str = 'yes',
                          callback: Optional[Callable] = None):
        """Place a new trigger/stop order via WebSocket (requires login)."""
        self.send('newTriggerOrder', {
            'symbol': symbol, 'stoptriggertype': stoptriggertype,
            'stoptriggerprice': stoptriggerprice, 'stoporderside': stoporderside,
            'stopordertype': stopordertype, 'stoporderquantity': stoporderquantity,
            'stoporderPrice': stoporderprice, 'stoporderqtyismax': stoporderqtyismax
        }, callback)

    def cancel_order(self, order_id: str, type: str = 'standard',
                     callback: Optional[Callable] = None):
        """Cancel an order via WebSocket (requires login)."""
        self.send('cancelOrder', {'id': order_id, 'type': type}, callback)

    def get_orders(self, symbol: str = None, callback: Optional[Callable] = None):
        """Get active orders via WebSocket (requires login)."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        self.send('getOrders', params, callback)

    def get_ws_trades(self, symbol: str = None, limit: int = None,
                      offset: int = None, sort: str = None,
                      callback: Optional[Callable] = None):
        """Get trade history via WebSocket (requires login)."""
        params = {}
        if symbol:
            params['symbol'] = symbol
        if limit:
            params['limit'] = limit
        if offset:
            params['offset'] = offset
        if sort:
            params['sort'] = sort
        self.send('getTrades', params, callback)
