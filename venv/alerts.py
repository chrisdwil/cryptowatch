from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]
gdPairFills = ["BTC-USD", "ETH-USD", "BCH-USD", "LTC-USD"]

cwAlerts = CWCryptoWatch()

for jm in jsonMarkets:
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in pairWatch):
        jsonMarketExchangePair = cwCurrency.db_get(jm['route'], 60)
        jsonMarketExchangePairSummary = cwCurrency.db_get(jsonMarketExchangePair['routes']['summary'], 1)

# for gpf in gdPairFills:
#     jsonFills = cwAlerts.gd_fills(product_string=gpf)
#     for jf in jsonFills:
#         print(jf['product_id'], jf['order_id'], jf['side'], jf['usd_volume'], jf['trade_id'])
