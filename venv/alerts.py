from datetime import datetime, date, time
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]
gdPairFills = ["BTC-USD", "ETH-USD", "BCH-USD", "LTC-USD"]
jsonFillsList = []
jsonStopLossList = []

cwAlerts = CWCryptoWatch()

jsonMarkets = cwAlerts.db_get("/markets", 60)
jsonAccountsList = cwAlerts.gd_accounts()

totalBalance = 0
for ja in jsonAccountsList:
    if ja['currency'] != "USD":
        jsonMarketExchangePairSummary = cwAlerts.db_get("/markets/gdax/" + ja['currency'].lower() + "usd/summary", 1)
        totalBalance += float(ja['balance']) * float(jsonMarketExchangePairSummary['price']['last'])
        if (float(ja['available']) * float(jsonMarketExchangePairSummary['price']['last'])) > 1:
            jsonStopLossList.append(ja['currency'])
    else:
        totalBalance += float(ja['balance'])

jsonPairList = []

for jm in jsonMarkets:
    jsonPairTrending = {}
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in pairWatch):
        jsonMarketExchangePair = cwAlerts.db_get(jm['route'], 60)
        jsonMarketExchangePairSummary = cwAlerts.db_get(jsonMarketExchangePair['routes']['summary'], 1)

        jsonPairTrending = {
            "pair": jm['pair'],
            "last": jsonMarketExchangePairSummary['price']['last'],
            "atr": cwAlerts.db_get_turtles(jsonMarketExchangePair['exchange'],
                                              jsonMarketExchangePair['pair'],
                                              jsonMarketExchangePairSummary['price']['last'],
                                              totalBalance
                                              )[0]
        }
        jsonPairList.append(jsonPairTrending)

for jf in gdPairFills:
    jsonFillsList.append(cwAlerts.gd_fills(jf)[0])

cwAlerts.al_trending(jsonPairList)
cwAlerts.al_fills(jsonFillsList)
cwAlerts.al_stoploss(jsonStopLossList)
cwAlerts.al_send()
print(datetime.now().isoformat() + " - notifier executed")
