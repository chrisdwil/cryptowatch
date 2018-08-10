from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]
gdPairFills = ["BTC-USD", "ETH-USD", "BCH-USD", "LTC-USD"]

cwAlerts = CWCryptoWatch()


for gpf in gdPairFills:
    jsonFills = cwAlerts.gd_fills(product_string=gpf)
    print jsonFills
