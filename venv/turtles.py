import json
from colorama import Fore, Back, Style
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


class PrintTurtles:
    json_data = {
        "balance": 0,
        "turtles": []
    }

    def prn(self):
        #print(json.dumps(self.json_data, sort_keys=True, indent=4))
        for jt in self.json_data['turtles']:
            for jps in jt['price_buy']:
                if jps['tag'] == "header":
                    print("%6s|%6s|%6s|%6s|a1 %5d|a2 %5d|a3 %5d|a4 %5d|h20 %5d|h55 %5d|h100 %5d|h180 %5d|h1y %5d|s50 %5d|e20 %5d" % (
                        jps['price_purchase'],
                        jps['u_size'],
                        jps['stop_price_half'],
                        jps['stop_price_third'],
                        jps['atr_1'],
                        jps['atr_2'],
                        jps['atr_3'],
                        jps['atr_4'],
                        jps['high_20'],
                        jps['high_55'],
                        jps['high_100'],
                        jps['high_180'],
                        jps['high_365'],
                        jps['sma_50'],
                        jps['ema_20']
                        )
                    )
                elif jps['tag'] == "row":
                    print("%6d|%6d|%6d|%6d|%8d|%8d|%8d|%8d|%9d|%9d|%10d|%10d|%9d|%9d|%9d" % (
                        jps['price_purchase'],
                        jps['u_size'],
                        jps['stop_price_half'],
                        jps['stop_price_third'],
                        jps['atr_1'],
                        jps['atr_2'],
                        jps['atr_3'],
                        jps['atr_4'],
                        jps['high_20'],
                        jps['high_55'],
                        jps['high_100'],
                        jps['high_180'],
                        jps['high_365'],
                        jps['sma_50'],
                        jps['ema_20']
                        )
                    )
            print

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]

cwTurtles = CWCryptoWatch()
jsonAccounts = cwTurtles.gd_accounts()
turtlesDashboard = PrintTurtles()
jsonMarkets = cwTurtles.db_get("/markets", 60)

jsonMarketsTurtles = [ "btcusd", "ethusd" ]

for ja in jsonAccounts:
    if ja['currency'] != "USD":
        jsonMarketExchangePairSummary = cwTurtles.db_get("/markets/gdax/" + ja['currency'].lower() + "usd/summary", 1)
        turtlesDashboard.json_data['balance'] += float(ja['balance']) * \
                                                       float(jsonMarketExchangePairSummary['price']['last'])
    else:
        turtlesDashboard.json_data['balance'] += float(ja['balance'])

turtlesIndex=0
for jm in jsonMarkets:
    price_start = 0
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in jsonMarketsTurtles):
        price_start = input("What price do you want to start with for " + jm['pair'] + ": ")
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

        turtlesDashboard.json_data['turtles'].append(
            {
                "product_id": "cur",
                "price_start": price_start,
                "price_buy": [
                    {
                        "tag": "header",
                        "price_purchase": "pur$",
                        "u_size": "size$",
                        "stop_price_half": "stop.5",
                        "stop_price_third": "stop.3",
                        "atr_1": price_start + (turtles20['atr'] * 0.5),
                        "atr_2": price_start + (turtles20['atr'] * 1.0),
                        "atr_3": price_start + (turtles20['atr'] * 1.5),
                        "atr_4": price_start + (turtles20['atr'] * 2.0),
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
                ]
            }
        )

        for i in range(0, 4, 1):
            price_purchase = price_start + float(turtles20['atr'] * i * 0.5)
            u_size = turtles20['u_size_dollars'] / price_purchase
            turtlesDashboard.json_data['turtles'][turtlesIndex]['price_buy'].append(
                {
                    "tag": "row",
                    "price_purchase": price_purchase,
                    "u_size": turtles20['u_size_dollars'],
                    "stop_price_half": price_purchase - turtles20['atr'] * 0.5,
                    "stop_price_third": price_purchase - turtles20['atr'] * 0.33,
                    "atr_1": u_size * (price_start + turtles20['atr'] * 0.5),
                    "atr_2": u_size * (price_start + turtles20['atr'] * 1.0),
                    "atr_3": u_size * (price_start + turtles20['atr'] * 1.5),
                    "atr_4": u_size * (price_start + turtles20['atr'] * 2.0),
                    "high_20": u_size * hl20['high'],
                    "high_55": u_size * hl55['high'],
                    "high_100": u_size * hl100['high'],
                    "high_180": u_size * hl180['high'],
                    "high_365": u_size * hl365['high'],
                    "sma_50": u_size * cwTurtles.db_get_sma(
                        jsonMarketExchangePair['exchange'],
                        jsonMarketExchangePair['pair'],
                        50
                    ),
                    "ema_20": u_size * cwTurtles.db_get_ema(
                        jsonMarketExchangePair['exchange'],
                        jsonMarketExchangePair['pair'],
                        20
                    )
                }
            )
            # insert math here to calculate sums of stop, atr1, atr2, etc, insert them into a json footer variable
            # at end of for loop
        turtlesIndex += 1
        # insert footer of summarized results

turtlesDashboard.prn()
