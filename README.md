# AnonEx Python Connector

Official Python client for the AnonEx cryptocurrency exchange API.

## Installation

```bash
pip install -e .
# or install dependencies directly
pip install requests websocket-client
```

## Quick Start

```python
from anonex import AnonExClient, AnonExWebSocket

# Public data (no auth needed)
client = AnonExClient()
markets = client.get_market_list()
ticker = client.get_ticker('BTC_USDT')

# Authenticated
client = AnonExClient(api_key='YOUR_KEY', api_secret='YOUR_SECRET')
balances = client.get_balances()
```

## Authentication

Two methods are supported:

**HMAC-SHA256 (default, recommended):**
```python
client = AnonExClient(api_key='key', api_secret='secret', auth_method='hmac')
```

**Basic Auth:**
```python
client = AnonExClient(api_key='key', api_secret='secret', auth_method='basic')
```

API keys are created on the AnonEx platform. Permissions: `read`, `read,trade`, `read,trade,withdraw`. Withdrawal operations require IP whitelisting.

## REST API

### Public Endpoints

| Method | Description |
|--------|-------------|
| `get_info()` | Exchange information |
| `get_time()` | Server time |
| `get_summary()` | Market summary |
| `get_assets(skip, limit, search)` | List all assets |
| `get_asset_info(asset_id, ticker)` | Asset details |
| `get_asset_chart(ticker, interval, currency)` | Simple price chart |
| `get_market_list()` | All markets (simple) |
| `get_market_list_full()` | All markets (full details) |
| `get_markets_paginated(base, skip, limit, order, dir, search)` | Paginated markets |
| `get_market_info(market_id, symbol)` | Market details |
| `get_candles(symbol, from_time, to_time, resolution, count_back)` | OHLCV candles |
| `get_market_orderbook(market_id, symbol, limit)` | Order book |
| `get_market_trades(symbol, limit, type)` | Recent trades |
| `get_markets(type)` | Markets list |
| `get_pairs()` | Trading pairs |
| `get_ticker(symbol)` | Single ticker |
| `get_tickers()` | All tickers |
| `get_orderbook(ticker_id, depth)` | Orderbook |
| `get_order_snapshot(market_id)` | Order book snapshot |
| `get_trades(market_id, since)` | Trades by market ID |
| `get_pool_list()` | All pools |
| `get_pool_list_full()` | All pools (full) |
| `get_pools_paginated(...)` | Paginated pools |
| `get_pool_info(pool_id, symbol)` | Pool details |
| `get_pool_trades(symbol, limit, type)` | Pool trades |
| `get_pool_tickers()` | All pool tickers |
| `get_pool_ticker(symbol)` | Single pool ticker |
| `get_account_by_address(address)` | Find account by address |

### Private Endpoints

| Method | Description |
|--------|-------------|
| `get_balances(ticker_list)` | Account balances |
| `get_trading_fees()` | Fee rates |
| `get_deposit_address(ticker)` | Deposit address |
| `get_deposits(ticker, limit, skip, since)` | Deposit history |
| `get_withdrawals(ticker, limit, skip, since)` | Withdrawal history |
| `create_withdrawal(ticker, address, quantity, paymentid, quantityistotal)` | Create withdrawal |
| `get_transfers(ticker, limit, skip)` | Transfer history |
| `create_transfer(ticker, accountid, quantity, notes)` | Internal transfer |
| `find_transaction(transfer_id)` | Find transaction |
| `create_order(symbol, side, type, quantity, price, ...)` | Place order |
| `create_trigger_order(symbol, ...)` | Place stop order |
| `cancel_order(order_id, type)` | Cancel order |
| `cancel_all_orders(symbol, side)` | Cancel all orders |
| `get_order(order_id)` | Get order |
| `get_order_with_trades(order_id)` | Order with fills |
| `get_account_orders(symbol, status, limit, skip, side)` | Account orders |
| `get_orders(symbol, status, limit, skip, side)` | Get orders |
| `get_pool_liquidity(symbol, limit, skip)` | Pool positions |
| `get_account_trades(symbol, limit, skip, since)` | Trade history |
| `get_my_trades(symbol, limit, skip, since)` | Trades |
| `get_trades_since(symbol, limit, skip, since)` | Trades since |
| `get_my_pool_trades(symbol, limit, skip, since)` | Pool trades |
| `get_pool_trades_since(symbol, limit, skip, since)` | Pool trades since |

## WebSocket API

### Public Subscriptions

```python
ws = AnonExWebSocket()

@ws.on('ticker')
def on_ticker(data):
    print(data)

@ws.on('orderbook')
def on_orderbook(data):
    print(data)

@ws.on('trades')
def on_trades(data):
    print(data)

ws.connect()
ws.subscribe_ticker('BTC/USDT')
ws.subscribe_orderbook('BTC/USDT', limit=20)
ws.subscribe_trades('BTC/USDT')
ws.subscribe_candles('BTC/USDT', period=5)
```

### Authenticated WebSocket

```python
ws = AnonExWebSocket(api_key='key', api_secret='secret')

@ws.on('connected')
def on_connected(data):
    ws.login()

@ws.on('reports')
def on_report(data):
    print('Order update:', data)

@ws.on('balances')
def on_balance(data):
    print('Balance update:', data)

ws.connect()
ws.subscribe_reports()
ws.subscribe_balances()

# Trade via WebSocket
ws.new_order(symbol='BTC/USDT', side='buy', type='limit', quantity='0.001', price='50000')
ws.cancel_order('ORDER_ID')
```

### WebSocket Methods

| Method | Auth | Description |
|--------|------|-------------|
| `ping()` | No | Heartbeat |
| `subscribe_ticker(symbol)` | No | Ticker updates |
| `subscribe_only_tickers(symbols)` | No | Subscribe to specific tickers only |
| `unsubscribe_ticker(symbol)` | No | Stop ticker updates |
| `subscribe_orderbook(symbol, limit)` | No | Orderbook updates |
| `unsubscribe_orderbook(symbol)` | No | Stop orderbook updates |
| `subscribe_trades(symbol)` | No | Trade updates |
| `unsubscribe_trades(symbol)` | No | Stop trade updates |
| `subscribe_candles(symbol, period)` | No | Candle updates |
| `unsubscribe_candles(symbol, period)` | No | Stop candle updates |
| `get_asset(ticker)` | No | Asset info |
| `get_assets()` | No | All assets |
| `get_market(symbol)` | No | Market info |
| `get_markets()` | No | All markets |
| `login()` | Yes | Authenticate |
| `get_trading_balance()` | Yes | Balances |
| `get_balance_values()` | Yes | Balance values |
| `subscribe_reports()` | Yes | Order reports |
| `subscribe_balances()` | Yes | Balance updates |
| `subscribe_transfers()` | Yes | Transfer updates |
| `new_order(...)` | Yes | Place order |
| `new_trigger_order(...)` | Yes | Place stop order |
| `cancel_order(id, type)` | Yes | Cancel order |
| `get_orders(symbol)` | Yes | Active orders |
| `get_ws_trades(symbol, limit)` | Yes | Trade history |

### Events

| Event | Description |
|-------|-------------|
| `connected` | WebSocket connected |
| `disconnected` | WebSocket disconnected |
| `error` | Error occurred |
| `message` | Raw message received |
| `ticker` | Ticker update |
| `orderbook` | Orderbook update |
| `trades` | Trade update |
| `candles` | Candle update |
| `reports` | Order execution report |
| `balances` | Balance update |
| `transfers` | Transfer update |
| `pong` | Pong response |

## Error Handling

```python
from anonex import AnonExClient, AnonExAPIError, AnonExAuthError

client = AnonExClient(api_key='key', api_secret='secret')

try:
    order = client.create_order(symbol='BTC/USDT', side='buy', type='limit',
                                quantity='0.001', price='50000')
except AnonExAPIError as e:
    print(f"API Error: {e} (code: {e.code}, description: {e.description})")
except AnonExAuthError as e:
    print(f"Auth Error: {e}")
```

## Configuration

```python
client = AnonExClient(
    api_key='key',
    api_secret='secret',
    base_url='https://api.anonex.io',  # Default
    auth_method='hmac',                 # 'hmac' or 'basic'
    timeout=30,                         # Request timeout in seconds
)

ws = AnonExWebSocket(
    api_key='key',
    api_secret='secret',
    ws_url='wss://api.anonex.io',      # Default
    reconnect=True,                     # Auto-reconnect
    reconnect_interval=5,              # Seconds between reconnect attempts
)
```
