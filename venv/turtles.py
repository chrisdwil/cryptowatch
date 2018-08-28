from colorama import Fore, Back, Style
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


class PrintTurtles:
    json_data = {
        "balance": 0,
        "turtles": [
            {
                "tag": "header",
                "product_id": "cur",
                "price_purchase": "pur$",
                "fee": 0,
                "u_size": "size",
                "price_sell": [
                    {
                        "stop_price": "stop",
                        "atr_1": "atr1",
                        "atr_2": "atr2",
                        "atr_3": "atr3",
                        "atr_4": "atr4",
                        "high_20": "h20",
                        "high_55": "h55",
                        "high_100": "h100",
                        "high_180": "h180",
                        "high_365": "h1y",
                        "sma_50": "s50",
                        "ema_20": "e20"
                    }
                ]
            }
        ]
    }

    def prn(self):
        #print(json.dumps(self.json_data, sort_keys=True, indent=4))
        for td in self.json_data['turtles']:
            print td['price_sell']

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]

cwTurtles = CWCryptoWatch()
jsonAccounts = cwTurtles.gd_accounts()
turtlesDashboard = PrintTurtles()
jsonMarkets = cwTurtles.db_get("/markets", 60)

jsonMarketsTurtles = [ "btcusd" ]

for ja in jsonAccounts:
    if ja['currency'] != "USD":
        jsonMarketExchangePairSummary = cwTurtles.db_get("/markets/gdax/" + ja['currency'].lower() + "usd/summary", 1)
        turtlesDashboard.json_data['balance'] += float(ja['balance']) * \
                                                       float(jsonMarketExchangePairSummary['price']['last'])
    else:
        turtlesDashboard.json_data['balance'] += float(ja['balance'])

for jm in jsonMarkets:
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in jsonMarketsTurtles):
        jsonMarketExchangePair = cwTurtles.db_get(jm['route'], 60)
        jsonMarketExchangePairSummary = cwTurtles.db_get(jsonMarketExchangePair['routes']['summary'], 1)
        jsonMarketExchangeOHLC = cwTurtles.db_get(jsonMarketExchangePair['routes']['ohlc'], 300)

        hl365 = cwTurtles.db_get_hl(
            jsonMarketExchangePair['exchange'],
            jsonMarketExchangePair['pair'],
            365
        )
        hl100 = cwTurtles.db_get_hl(
            jsonMarketExchangePair['exchange'],
            jsonMarketExchangePair['pair'],
            100
        )
        hl180 = cwTurtles.db_get_hl(
            jsonMarketExchangePair['exchange'],
            jsonMarketExchangePair['pair'],
            100
        )
        hl55 = cwTurtles.db_get_hl(
            jsonMarketExchangePair['exchange'],
            jsonMarketExchangePair['pair'],
            55
        )
        hl20 = cwTurtles.db_get_hl(
            jsonMarketExchangePair['exchange'],
            jsonMarketExchangePair['pair'],
            20
        )
        turtles20 = cwTurtles.db_get_turtles(
            jsonMarketExchangePair['exchange'],
            jsonMarketExchangePair['pair'],
            jsonMarketExchangePairSummary['price']['last'],
            turtlesDashboard.json_data['balance']
        )

        for i in range(0, 4, 1):
            price_purchase = jsonMarketExchangePairSummary['price']['last'] + float(turtles20['atr'] * i * 0.5)
            turtlesDashboard.json_data['turtles'].append(
                {
                "tag": "row",
                "product_id": jsonMarketExchangePair['pair'][0:3],
                "price_purchase": price_purchase,
                "fee": 0.997,
                "u_size": turtles20['u_size'],
                "price_sell": {
                    "stop_price": price_purchase - turtles20['atr']/3,
                    "atr_1": price_purchase + turtles20['atr'],
                    "atr_2": price_purchase + turtles20['atr'] * 2,
                    "atr_3": price_purchase + turtles20['atr'] * 3,
                    "atr_4": price_purchase + turtles20['atr'] * 2,
                    "high_20": hl20['high'],
                    "high_55": hl55['high'],
                    "high_100": hl100['high'],
                    "high_180": hl180['high'],
                    "high_365": hl365['high'],
                    "sma_50": cwTurtles.db_get_sma(
                        jsonMarketExchangePair['exchange'],
                        jsonMarketExchangePair['pair'],
                        50
                    ),
                    "ema_20": cwTurtles.db_get_ema(
                        jsonMarketExchangePair['exchange'],
                        jsonMarketExchangePair['pair'],
                        20
                    )
                    }
                }
            )
            # insert math here to calculate sums of stop, atr1, atr2, etc, insert them into a json footer variable
            # at end of for loop
        # insert footer of summarized results

turtlesDashboard.prn()
