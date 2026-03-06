"""AnonEx API Python Connector - Usage Examples."""

import time
from anonex import AnonExClient, AnonExWebSocket

# ========================================
#  Public REST API (no authentication)
# ========================================

client = AnonExClient()

# Exchange info
info = client.get_info()
print("Exchange:", info['name'])

# Server time
server_time = client.get_time()
print("Server time:", server_time['serverTime'])

# List all assets
assets = client.get_assets(limit=10)
print(f"First 10 assets: {len(assets)} returned")

# Get asset info
btc = client.get_asset_info(ticker='BTC')
print(f"BTC: {btc['name']}")

# List markets
markets = client.get_market_list()
print(f"Total markets: {len(markets)}")

# Get market info
market = client.get_market_info(symbol='BTC/USDT')
print(f"BTC/USDT last price: {market.get('lastPrice')}")

# Get ticker
ticker = client.get_ticker('BTC_USDT')
print(f"BTC/USDT ticker: bid={ticker.get('bid')}, ask={ticker.get('ask')}")

# Get orderbook
ob = client.get_market_orderbook(symbol='BTC/USDT', limit=5)
print(f"Orderbook: {len(ob.get('bids', []))} bids, {len(ob.get('asks', []))} asks")

# Get candles
candles = client.get_candles('BTC/USDT', resolution=60, count_back=10, first_data_request=1)
print(f"Candles: {len(candles.get('bars', []))} bars")

# Get recent trades
trades = client.get_market_trades('BTC/USDT', limit=5)
print(f"Recent trades: {len(trades)}")

# Pools
pools = client.get_pool_list()
print(f"Total pools: {len(pools)}")

# ========================================
#  Authenticated REST API
# ========================================

auth_client = AnonExClient(
    api_key='YOUR_API_KEY',
    api_secret='YOUR_API_SECRET',
    auth_method='hmac',  # or 'basic'
)

# Get balances
# balances = auth_client.get_balances()
# balances = auth_client.get_balances(ticker_list='BTC,ETH,USDT')

# Get trading fees
# fees = auth_client.get_trading_fees()
# print(f"Maker fee: {fees['makerFee']}%, Taker fee: {fees['takerFee']}%")

# Get deposit address
# addr = auth_client.get_deposit_address('BTC')
# print(f"BTC deposit address: {addr['address']}")

# Get deposit history
# deposits = auth_client.get_deposits(ticker='BTC', limit=10)

# Get withdrawal history
# withdrawals = auth_client.get_withdrawals(limit=10)

# Create a limit order
# order = auth_client.create_order(
#     symbol='BTC/USDT',
#     side='buy',
#     type='limit',
#     quantity='0.001',
#     price='50000',
# )
# print(f"Order created: {order['id']}")

# Create a market order
# order = auth_client.create_order(
#     symbol='BTC/USDT',
#     side='buy',
#     type='market',
#     quantity='0.001',
# )

# Cancel an order
# result = auth_client.cancel_order('ORDER_ID')

# Cancel all orders for a symbol
# result = auth_client.cancel_all_orders('BTC/USDT', side='all')

# Get order status
# order = auth_client.get_order('ORDER_ID')
# print(f"Order status: {order['status']}")

# Get order with trade fills
# order = auth_client.get_order_with_trades('ORDER_ID')

# Get active orders
# orders = auth_client.get_account_orders(symbol='BTC/USDT', status='active')

# Get trade history
# trades = auth_client.get_account_trades(symbol='BTC/USDT', limit=50)

# Create a withdrawal (requires withdraw permission + IP whitelist)
# wd = auth_client.create_withdrawal(
#     ticker='BTC',
#     address='bc1q...',
#     quantity='0.01',
# )

# Create an internal transfer
# transfer = auth_client.create_transfer(
#     ticker='USDT',
#     accountid='recipient@email.com',
#     quantity='100',
#     notes='Payment',
# )

# ========================================
#  WebSocket - Public Data
# ========================================

ws = AnonExWebSocket()


@ws.on('connected')
def on_connected(data):
    print('WebSocket connected!')
    ws.subscribe_ticker('BTC/USDT')
    ws.subscribe_orderbook('BTC/USDT', limit=10)
    ws.subscribe_trades('BTC/USDT')


@ws.on('ticker')
def on_ticker(data):
    print(f"Ticker: {data}")


@ws.on('orderbook')
def on_orderbook(data):
    print(f"Orderbook update: {data.get('symbol', '')}")


@ws.on('trades')
def on_trades(data):
    print(f"Trade: {data}")


@ws.on('error')
def on_error(error):
    print(f"Error: {error}")


# ws.connect()
# time.sleep(30)  # Listen for 30 seconds
# ws.disconnect()

# ========================================
#  WebSocket - Authenticated Trading
# ========================================

auth_ws = AnonExWebSocket(
    api_key='YOUR_API_KEY',
    api_secret='YOUR_API_SECRET',
)


@auth_ws.on('connected')
def on_auth_connected(data):
    print('Authenticated WS connected!')
    auth_ws.login()


@auth_ws.on('reports')
def on_report(data):
    print(f"Order report: {data}")


@auth_ws.on('balances')
def on_balance(data):
    print(f"Balance update: {data}")


@auth_ws.on('message')
def on_login_response(data):
    if data.get('result') and data.get('id'):
        # After successful login, subscribe to reports
        auth_ws.subscribe_reports()
        auth_ws.subscribe_balances()

        # Place an order via WebSocket
        # auth_ws.new_order(
        #     symbol='BTC/USDT',
        #     side='buy',
        #     type='limit',
        #     quantity='0.001',
        #     price='50000',
        # )


# auth_ws.connect()
# time.sleep(60)
# auth_ws.disconnect()

print("\nExamples complete. Uncomment sections to run live.")
