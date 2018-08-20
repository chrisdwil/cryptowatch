from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]
gdPairFills = ["BTC-USD", "ETH-USD", "BCH-USD", "LTC-USD"]

cwAlerts = CWCryptoWatch()

jsonMarkets = cwAlerts.db_get("/markets", 60)

cwAlerts.al_init()

# for jm in jsonMarkets:
#     alert
#     if (jm['exchange'] in exchangesWatch) & (jm['pair'] in pairWatch):
#         jsonMarketExchangePair = cwAlerts.db_get(jm['route'], 60)
#         jsonMarketExchangePairSummary = cwAlerts.db_get(jsonMarketExchangePair['routes']['summary'], 1)
#
#         price_last = jsonMarketExchangePairSummary['price']['last']
#         print price_last
