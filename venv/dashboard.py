from colorama import Fore, Back, Style
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


class PrintMarkets:

    json_data = {
        "balance": 0,
        "market": [
            {
                "tag": "header",
                "exchange": "exc",
                "pair": "cur",
                "u_size": "usz",
                "atr": "atr",
                "last": "tkr",
                "rsi": "rsi",
                "sma_50": "s50",
                "ema_20": "e20",
                "low_55": "l55",
                "low_20": "l20",
                "high_20": "h20",
                "high_55": "h55"
            }
        ]
    }

    def prn(self):
        for jdl in self.json_data['market']:
            if jdl['tag'] == "header":
                print("%4s %4s %5s %5s %5s %5s %5s %5s %5s %5s %5s %5s" % (
                    jdl['exchange'],
                    jdl['pair'],
                    jdl['u_size'],
                    jdl['atr'],
                    jdl['last'],
                    jdl['rsi'],
                    jdl['sma_50'],
                    jdl['ema_20'],
                    jdl['low_55'],
                    jdl['low_20'],
                    jdl['high_20'],
                    jdl['high_55']
                    )
                )
                print("---------------------------- $%10.2f ----------------------------" % (
                    round(self.json_data['balance'], 2)
                    )
                )
            elif jdl['tag'] == "row":
                reset = Fore.RESET
                if jdl['last'] >= jdl['high_20']:
                    high20color = Fore.GREEN
                elif jdl['last'] > jdl['high_20'] - jdl['atr'] * 0.5:
                    high20color = Fore.YELLOW
                else:
                    high20color = Fore.RESET

                if jdl['last'] >= jdl['high_55']:
                    high55color = Fore.GREEN
                elif jdl['last'] > jdl['high_55'] - jdl['atr'] * 0.5:
                    high55color = Fore.YELLOW
                else:
                    high55color = Fore.RESET

                if jdl['last'] <= jdl['low_20']:
                    low20color = Fore.RED
                elif jdl['low_20'] >= jdl['low_20'] + jdl['atr'] * 0.5:
                    low20color = Fore.YELLOW
                else:
                    low20color = Fore.RESET

                if jdl['last'] <= jdl['low_55']:
                    low55color = Fore.RED
                elif jdl['low_55'] >= jdl['low_55'] + jdl['atr'] * 0.5:
                    low55color = Fore.YELLOW
                else:
                    low55color = Fore.RESET

                if jdl['last'] >= jdl['ema_20']:
                    emacolor = Fore.GREEN
                elif jdl['last'] >= jdl['ema_20'] - jdl['atr'] * 0.5:
                    emacolor = Fore.YELLOW
                else:
                    emacolor = Fore.RED

                if jdl['last'] >= jdl['sma_50']:
                    smacolor = Fore.GREEN
                elif jdl['last'] >= jdl['sma_50'] - jdl['atr'] * 0.5:
                    smacolor = Fore.YELLOW
                else:
                    smacolor = Fore.RED

                if jdl['rsi'] >= 70:
                    rsicolor = Fore.RED
                if jdl['rsi'] <= 30:
                    rsicolor = Fore.GREEN
                else:
                    rsicolor = Fore.CYAN

                print("%-4s|%4s|%5d|%5d|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s" % (
                    jdl['exchange'],
                    jdl['pair'],
                    jdl['u_size'],
                    jdl['atr'],
                    Fore.CYAN,
                    jdl['last'],
                    reset,
                    rsicolor,
                    jdl['rsi'],
                    reset,
                    smacolor,
                    jdl['sma_50'],
                    reset,
                    emacolor,
                    jdl['ema_20'],
                    reset,
                    low55color,
                    jdl['low_55'],
                    reset,
                    low20color,
                    jdl['low_20'],
                    reset,
                    high20color,
                    jdl['high_20'],
                    reset,
                    high55color,
                    jdl['high_55'],
                    reset
                    )
                )

exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]

cwCurrency = CWCryptoWatch()
marketDashboard = PrintMarkets()

jsonMarkets = cwCurrency.db_get("/markets", 60)
jsonAccounts = cwCurrency.gd_accounts()

for ja in jsonAccounts:
    if ja['currency'] != "USD":
        jsonMarketExchangePairSummary = cwCurrency.db_get("/markets/gdax/" + ja['currency'].lower() + "usd/summary", 1)
        marketDashboard.json_data['balance'] += float(ja['balance']) * \
                                                       float(jsonMarketExchangePairSummary['price']['last'])
    else:
        marketDashboard.json_data['balance'] += float(ja['balance'])

for jm in jsonMarkets:
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in pairWatch):
        jsonMarketExchangePair = cwCurrency.db_get(jm['route'], 60)
        jsonMarketExchangePairSummary = cwCurrency.db_get(jsonMarketExchangePair['routes']['summary'], 1)
        jsonMarketExchangeOHLC = cwCurrency.db_get(jsonMarketExchangePair['routes']['ohlc'], 300)

        hl55 = cwCurrency.db_get_hl(jsonMarketExchangePair['exchange'],
                                    jsonMarketExchangePair['pair'],
                                    55)
        hl20 = cwCurrency.db_get_hl(jsonMarketExchangePair['exchange'],
                                    jsonMarketExchangePair['pair'],
                                    20)
        turtles20 = cwCurrency.db_get_turtles(jsonMarketExchangePair['exchange'],
                                              jsonMarketExchangePair['pair'],
                                              jsonMarketExchangePairSummary['price']['last'],
                                              marketDashboard.json_data['balance']
                                              )
        marketDashboard.json_data['market'].append(
            {
                "tag": "row",
                "exchange": jsonMarketExchangePair['exchange'][0:4],
                "pair": jsonMarketExchangePair['pair'][0:3],
                "u_size": turtles20['u_size_dollars'],
                "atr": turtles20['atr'],
                "last": jsonMarketExchangePairSummary['price']['last'],
                "rsi": cwCurrency.db_get_rsi(jsonMarketExchangePair['exchange'],
                                      jsonMarketExchangePair['pair'],
                                      14,
                                      33
                                      ),
                "sma_50": cwCurrency.db_get_sma(jsonMarketExchangePair['exchange'],
                                      jsonMarketExchangePair['pair'],
                                      50),
                "ema_20": cwCurrency.db_get_ema(jsonMarketExchangePair['exchange'],
                                      jsonMarketExchangePair['pair'],
                                      20),
                "low_55": hl55['low'],
                "low_20": hl20['low'],
                "high_20": hl20['high'],
                "high_55": hl55['high']
            }
        )

marketDashboard.prn()