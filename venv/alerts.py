from datetime import datetime, date, time
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]
gdPairFills = ["BTC-USD", "ETH-USD", "BCH-USD", "LTC-USD"]

cwAlerts = CWCryptoWatch()

jsonMarkets = cwAlerts.db_get("/markets", 60)
jsonAccounts = cwAlerts.gd_accounts()

totalBalance = 0
for ja in jsonAccounts:
    if ja['currency'] != "USD":
        jsonMarketExchangePairSummary = cwAlerts.db_get("/markets/gdax/" + ja['currency'].lower() + "usd/summary", 1)
        totalBalance += float(ja['balance']) * float(jsonMarketExchangePairSummary['price']['last'])
    else:
        totalBalance += float(ja['balance'])

jsonPairList = []

for jm in jsonMarkets:
    jsonPairTrending = {}
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in pairWatch):
        jsonMarketExchangePair = cwAlerts.db_get(jm['route'], 60)
        jsonMarketExchangePairSummary = cwAlerts.db_get(jsonMarketExchangePair['routes']['summary'], 1)

        jsonPairTrending = {
            "pair" : jm['pair'],
            "last" : jsonMarketExchangePairSummary['price']['last'],
            "atr" : cwAlerts.db_get_turtles(jsonMarketExchangePair['exchange'],
                                              jsonMarketExchangePair['pair'],
                                              jsonMarketExchangePairSummary['price']['last'],
                                              totalBalance
                                              )[0]
        }
        jsonPairList.append(jsonPairTrending)

cwAlerts.al_trending(jsonPairList)
cwAlerts.al_send()
print(datetime.now().isoformat() + " - notifier executed")