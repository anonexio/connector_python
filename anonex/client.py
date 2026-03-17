"""AnonEx REST API Client."""

import hashlib
import hmac
import time
import uuid
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urlencode

import requests

from .exceptions import AnonExAPIError, AnonExAuthError, AnonExConnectionError


class AnonExClient:
    """REST client for the AnonEx cryptocurrency exchange API.

    Supports two authentication methods:
    - Basic Auth (simple but sends secret in headers)
    - HMAC-SHA256 signing (preferred, more secure)

    Usage:
        # Public endpoints (no auth needed)
        client = AnonExClient()
        markets = client.get_markets()

        # Authenticated endpoints
        client = AnonExClient(api_key='your_key', api_secret='your_secret')
        balances = client.get_balances()
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        base_url: str = 'https://api.anonex.io',
        auth_method: str = 'hmac',
        timeout: int = 30,
    ):
        self.api_key = api_key
        self.api_secret = api_secret
        self.base_url = base_url.rstrip('/')
        self.auth_method = auth_method  # 'hmac' or 'basic'
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def _sign_request(self, method: str, url: str, body: str = '') -> Dict[str, str]:
        """Generate HMAC-SHA256 signature headers."""
        nonce = str(int(time.time() * 1000)) + str(uuid.uuid4().hex[:8])
        message = self.api_key + url + body + nonce
        signature = hmac.new(
            self.api_secret.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return {
            'x-api-key': self.api_key,
            'x-api-nonce': nonce,
            'x-api-sign': signature,
        }

    def _get_auth_headers(self, method: str, url: str, body: str = '') -> Dict[str, str]:
        """Get authentication headers based on configured auth method."""
        if not self.api_key or not self.api_secret:
            raise AnonExAuthError('API key and secret are required for authenticated endpoints')

        if self.auth_method == 'basic':
            import base64
            credentials = base64.b64encode(
                f'{self.api_key}:{self.api_secret}'.encode()
            ).decode()
            return {'Authorization': f'Basic {credentials}'}
        else:
            return self._sign_request(method, url, body)

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        auth: bool = False,
    ) -> Any:
        """Make an HTTP request to the API."""
        url = f'{self.base_url}{path}'

        if params:
            params = {k: v for k, v in params.items() if v is not None}
            if params:
                url += '?' + urlencode(params)

        body_str = ''
        if data:
            import json
            body_str = json.dumps(data)

        headers = {}
        if auth:
            headers = self._get_auth_headers(method, url, body_str)

        try:
            response = self.session.request(
                method,
                url,
                json=data if data else None,
                headers=headers,
                timeout=self.timeout,
            )
        except requests.exceptions.ConnectionError as e:
            raise AnonExConnectionError(f'Connection failed: {e}')
        except requests.exceptions.Timeout as e:
            raise AnonExConnectionError(f'Request timed out: {e}')

        try:
            result = response.json()
        except ValueError:
            return response.text

        if isinstance(result, dict) and 'error' in result:
            err = result['error']
            raise AnonExAPIError(
                err.get('message', 'Unknown error'),
                code=err.get('code'),
                description=err.get('description'),
            )

        return result

    def _get(self, path: str, params: Optional[Dict] = None, auth: bool = False) -> Any:
        return self._request('GET', path, params=params, auth=auth)

    def _post(self, path: str, data: Optional[Dict] = None, auth: bool = False) -> Any:
        return self._request('POST', path, data=data, auth=auth)

    # ========================
    #  Public Endpoints
    # ========================

    def get_info(self) -> Dict:
        """Get exchange information."""
        return self._get('/api/v2/info')

    def get_time(self) -> Dict:
        """Get server time."""
        return self._get('/api/v2/time')

    def get_summary(self) -> List:
        """Get market summary (CMC format)."""
        return self._get('/api/v2/summary')

    # --- Assets ---

    def get_assets(self, skip: int = None, limit: int = None, search: str = None) -> List:
        """Get list of all assets."""
        return self._get('/api/v2/asset/getlist', {'skip': skip, 'limit': limit, 'search': search})

    def get_asset_info(self, asset_id: str = None, ticker: str = None) -> Dict:
        """Get asset info by ID or ticker."""
        return self._get('/api/v2/asset/info', {'id': asset_id, 'ticker': ticker})

    def get_asset_chart(self, ticker: str, interval: str = '1D', currency: str = 'USD') -> List:
        """Get simple chart data for an asset. interval: 1D,1M,3M,1Y,5Y,All. currency: USD,BTC."""
        return self._get(f'/api/v2/asset/getsimplechart/{ticker}', {'interval': interval, 'currency': currency})

    # --- Markets ---

    def get_market_list(self) -> List:
        """Get simple list of all markets."""
        return self._get('/api/v2/market/getlist')

    def get_market_list_full(self) -> List:
        """Get full details of all markets."""
        return self._get('/api/v2/market/listfull')

    def get_markets_paginated(self, base: str = None, skip: int = None, limit: int = None,
                              order: str = None, dir: str = None, search: str = None) -> Dict:
        """Get paginated market list with sorting and filtering."""
        return self._get('/api/v2/market/list', {
            'base': base, 'skip': skip, 'limit': limit,
            'order': order, 'dir': dir, 'search': search
        })

    def get_market_info(self, market_id: str = None, symbol: str = None) -> Dict:
        """Get market info by ID or symbol (e.g. 'BTC/USDT')."""
        return self._get('/api/v2/market/info', {'id': market_id, 'symbol': symbol})

    def get_candles(self, symbol: str, from_time: int = None, to_time: int = None,
                    resolution: int = 5, count_back: int = None, first_data_request: int = None) -> Dict:
        """Get OHLCV candle data. resolution in minutes (1,5,15,30,60,240,720,1440)."""
        return self._get('/api/v2/market/candles', {
            'symbol': symbol, 'from': from_time, 'to': to_time,
            'resolution': resolution, 'countBack': count_back,
            'firstDataRequest': first_data_request
        })

    def get_market_orderbook(self, market_id: str = None, symbol: str = None, limit: int = None) -> Dict:
        """Get order book for a market. Max limit: 500."""
        return self._get('/api/v2/market/orderbook', {'marketId': market_id, 'symbol': symbol, 'limit': limit})

    def get_market_trades(self, symbol: str, limit: int = None, type: str = None) -> List:
        """Get recent trades for a market. Max limit: 200. type: buy/sell."""
        return self._get('/api/v2/market/trades', {'symbol': symbol, 'limit': limit, 'type': type})

    def get_markets(self, type: str = None) -> List:
        """Get markets list (nomics format). type: all/spot/pool."""
        return self._get('/api/v2/markets', {'type': type})

    def get_pairs(self) -> List:
        """Get all trading pairs (CoinGecko format)."""
        return self._get('/api/v2/pairs')

    def get_ticker(self, symbol: str) -> Dict:
        """Get ticker for a single market. symbol: e.g. 'BTC_USDT' or 'BTC/USDT'."""
        return self._get(f'/api/v2/ticker/{symbol}')

    def get_tickers(self) -> List:
        """Get all market tickers."""
        return self._get('/api/v2/tickers')

    def get_orderbook(self, ticker_id: str, depth: int = None) -> Dict:
        """Get orderbook (CoinGecko format). ticker_id: e.g. 'BTC_USDT'."""
        return self._get('/api/v2/orderbook', {'ticker_id': ticker_id, 'depth': depth})

    def get_order_snapshot(self, market_id: str) -> Dict:
        """Get order book snapshot by market ID."""
        return self._get('/api/v2/orders/snapshot', {'market': market_id})

    def get_trades(self, market_id: str, since: str = None) -> List:
        """Get trades by market ID, optionally since a trade ID."""
        return self._get('/api/v2/trades', {'market': market_id, 'since': since})

    # --- Pools ---

    def get_pool_list(self) -> List:
        """Get simple list of all liquidity pools."""
        return self._get('/api/v2/pool/getlist')

    def get_pool_list_full(self) -> List:
        """Get full details of all pools."""
        return self._get('/api/v2/pool/listfull')

    def get_pools_paginated(self, base: str = None, skip: int = None, limit: int = None,
                            order: str = None, dir: str = None, search: str = None) -> Dict:
        """Get paginated pool list with sorting and filtering."""
        return self._get('/api/v2/pool/list', {
            'base': base, 'skip': skip, 'limit': limit,
            'order': order, 'dir': dir, 'search': search
        })

    def get_pool_info(self, pool_id: str = None, symbol: str = None) -> Dict:
        """Get pool info by ID or symbol."""
        return self._get('/api/v2/pool/info', {'id': pool_id, 'symbol': symbol})

    def get_pool_trades(self, symbol: str, limit: int = None, type: str = None) -> List:
        """Get recent pool trades. Max limit: 200."""
        return self._get('/api/v2/pool/trades', {'symbol': symbol, 'limit': limit, 'type': type})

    def get_pool_tickers(self) -> List:
        """Get all pool tickers."""
        return self._get('/api/v2/pooltickers')

    def get_pool_ticker(self, symbol: str) -> Dict:
        """Get ticker for a single pool."""
        return self._get(f'/api/v2/poolticker/{symbol}')

    # --- Misc Public ---

    def get_account_by_address(self, address: str) -> Dict:
        """Find account by deposit address."""
        return self._get(f'/api/v2/getaccountbyaddress/{address}')


    # ========================
    #  Private Endpoints
    # ========================

    # --- Account ---

    def get_balances(self, ticker_list: str = None) -> List:
        """Get account balances. ticker_list: comma-separated tickers e.g. 'BTC,ETH'."""
        return self._get('/api/v2/balances', {'tickerlist': ticker_list}, auth=True)

    def get_trading_fees(self) -> Dict:
        """Get your current trading fee rates."""
        return self._get('/api/v2/tradingfees', auth=True)


    # --- Deposits ---

    def get_deposit_address(self, ticker: str) -> Dict:
        """Get deposit address for a ticker."""
        return self._get(f'/api/v2/getdepositaddress/{ticker}', auth=True)

    def get_deposits(self, ticker: str = None, limit: int = None, skip: int = None, since: int = None) -> List:
        """Get deposit history. Max limit: 500."""
        return self._get('/api/v2/getdeposits', {
            'ticker': ticker, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)

    # --- Withdrawals ---

    def get_withdrawals(self, ticker: str = None, limit: int = None, skip: int = None, since: int = None) -> List:
        """Get withdrawal history. Max limit: 500."""
        return self._get('/api/v2/getwithdrawals', {
            'ticker': ticker, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)

    def create_withdrawal(self, ticker: str, address: str, quantity: str,
                          paymentid: str = '', quantityistotal: int = 0) -> Dict:
        """Create a withdrawal. Requires API key with withdraw permission and IP whitelist."""
        return self._post('/api/v2/createwithdrawal', {
            'ticker': ticker, 'address': address, 'paymentid': paymentid,
            'quantity': quantity, 'quantityistotal': quantityistotal
        }, auth=True)

    # --- Transfers ---

    def get_transfers(self, ticker: str = None, limit: int = None, skip: int = None) -> List:
        """Get transfer history."""
        return self._get('/api/v2/gettransfers', {
            'ticker': ticker, 'limit': limit, 'skip': skip
        }, auth=True)

    def create_transfer(self, ticker: str, accountid: str, quantity: str, notes: str = '') -> Dict:
        """Create an internal transfer. accountid can be email, user ID, or deposit address."""
        return self._post('/api/v2/createtransfer', {
            'ticker': ticker, 'accountid': accountid, 'quantity': quantity, 'notes': notes
        }, auth=True)

    def find_transaction(self, transfer_id: str) -> List:
        """Find a transaction by ID or transaction hash."""
        return self._get(f'/api/v2/findtransaction/{transfer_id}', auth=True)

    # --- Orders ---

    def create_order(self, symbol: str, side: str, type: str = 'limit',
                     quantity: str = '0', price: str = '0',
                     user_provided_id: str = None, strict_validate: bool = False,
                     quote_order_qty: str = None) -> Dict:
        """Create a new order. side: buy/sell. type: limit/market.
        For market buy orders, pass quote_order_qty to specify total spend in quote currency
        (e.g. USDT). The engine fills as much as possible within the budget."""
        body = {
            'symbol': symbol, 'side': side, 'type': type,
            'quantity': quantity, 'price': price, 'strictValidate': strict_validate
        }
        if user_provided_id:
            body['userProvidedId'] = user_provided_id
        if quote_order_qty:
            body['quoteOrderQty'] = quote_order_qty
        return self._post('/api/v2/createorder', body, auth=True)

    def create_trigger_order(self, symbol: str, stoptriggertype: str, stoptriggerprice: str,
                             stoporderside: str, stopordertype: str = 'limit',
                             stoporderquantity: str = '0', stoporderprice: str = '0',
                             stoporderqtyismax: str = 'yes') -> Dict:
        """Create a stop/trigger order."""
        return self._post('/api/v2/createtriggerorder', {
            'symbol': symbol, 'stoptriggertype': stoptriggertype,
            'stoptriggerprice': stoptriggerprice, 'stoporderside': stoporderside,
            'stopordertype': stopordertype, 'stoporderquantity': stoporderquantity,
            'stoporderPrice': stoporderprice, 'stoporderqtyismax': stoporderqtyismax
        }, auth=True)

    def cancel_order(self, order_id: str, type: str = 'standard') -> Dict:
        """Cancel an order by ID or userProvidedId. type: standard/stop."""
        return self._post('/api/v2/cancelorder', {'id': order_id, 'type': type}, auth=True)

    def cancel_all_orders(self, symbol: str, side: str = 'all') -> Dict:
        """Cancel all orders for a symbol. side: buy/sell/all."""
        return self._post('/api/v2/cancelallorders', {'symbol': symbol, 'side': side}, auth=True)

    def get_order(self, order_id: str) -> Dict:
        """Get a single order by ID or userProvidedId."""
        return self._get(f'/api/v2/getorder/{order_id}', auth=True)

    def get_order_with_trades(self, order_id: str) -> Dict:
        """Get an order with its trade fills."""
        return self._get(f'/api/v2/getorderwithtrades/{order_id}', auth=True)

    def get_account_orders(self, symbol: str = None, status: str = None,
                           limit: int = None, skip: int = None, side: str = None) -> List:
        """Get account orders. status: active/filled/cancelled."""
        return self._get('/api/v2/account/orders', {
            'symbol': symbol, 'status': status, 'limit': limit, 'skip': skip, 'side': side
        }, auth=True)

    def get_orders(self, symbol: str = None, status: str = None,
                   limit: int = None, skip: int = None, side: str = None) -> List:
        """Get orders (legacy endpoint)."""
        return self._get('/api/v2/getorders', {
            'symbol': symbol, 'status': status, 'limit': limit, 'skip': skip, 'side': side
        }, auth=True)

    def get_pool_liquidity(self, symbol: str = None, limit: int = None, skip: int = None) -> List:
        """Get pool liquidity positions."""
        return self._get('/api/v2/account/pliquidity', {
            'symbol': symbol, 'limit': limit, 'skip': skip
        }, auth=True)

    # --- Trade History ---

    def get_account_trades(self, symbol: str = None, limit: int = None,
                           skip: int = None, since: int = None) -> List:
        """Get account trade history."""
        return self._get('/api/v2/account/trades', {
            'symbol': symbol, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)

    def get_my_trades(self, symbol: str = None, limit: int = None,
                      skip: int = None, since: int = None) -> List:
        """Get trades (legacy endpoint)."""
        return self._get('/api/v2/gettrades', {
            'symbol': symbol, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)

    def get_trades_since(self, symbol: str = None, limit: int = None,
                         skip: int = None, since: int = None) -> List:
        """Get trades since a timestamp."""
        return self._get('/api/v2/gettradessince', {
            'symbol': symbol, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)

    def get_my_pool_trades(self, symbol: str = None, limit: int = None,
                           skip: int = None, since: int = None) -> List:
        """Get pool trade history."""
        return self._get('/api/v2/getpooltrades', {
            'symbol': symbol, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)

    def get_pool_trades_since(self, symbol: str = None, limit: int = None,
                              skip: int = None, since: int = None) -> List:
        """Get pool trades since a timestamp."""
        return self._get('/api/v2/getpooltradessince', {
            'symbol': symbol, 'limit': limit, 'skip': skip, 'since': since
        }, auth=True)
