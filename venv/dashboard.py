import colorama
from colorama import Fore, Back, Style
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


class PrintCurrency:
    none = 0
    header = 1
    border = 2
    row = 3

    def currency(self,
                 type_print=0,
                 exchange="None",
                 pair="None",
                 unit_size=0,
                 atr=0,
                 ticker=0,
                 rsi=0,
                 sma=0,
                 ema=0,
                 low55=0,
                 low20=0,
                 high20=0,
                 high55=0,
                 total_balance=0
                 ):
        if type_print == PrintCurrency.header:
            print("%4s %4s %5s %5s %5s %5s %5s %5s %5s %5s %5s %5s" % ("exc",
                                                                       "cur",
                                                                       "usz",
                                                                       "atr",
                                                                       "tkr",
                                                                       "rsi",
                                                                       "s50",
                                                                       "e20",
                                                                       "l55",
                                                                       "l20",
                                                                       "h20",
                                                                       "h55"
                                                                       ))
        elif type_print == PrintCurrency.border:
            print "---------------------------- $%10.2f ----------------------------" % (round(total_balance, 2))
        elif type_print == PrintCurrency.row:
            reset = Fore.RESET
            if ticker >= high20:
                high20color = Fore.GREEN
            elif ticker > high20 - atr * 0.5:
                high20color = Fore.YELLOW
            else:
                high20color = Fore.RESET

            if ticker >= high55:
                high55color = Fore.GREEN
            elif ticker > high55 - atr * 0.5:
                high55color = Fore.YELLOW
            else:
                high55color = Fore.RESET

            if ticker <= low20:
                low20color = Fore.RED
            elif low20 >= low20 + atr * 0.5:
                low20color = Fore.YELLOW
            else:
                low20color = Fore.RESET

            if ticker <= low55:
                low55color = Fore.RED
            elif low55 >= low55 + atr * 0.5:
                low55color = Fore.YELLOW
            else:
                low55color = Fore.RESET

            if ticker >= ema20:
                emacolor = Fore.GREEN
            elif ticker >= ema20 - atr * 0.5:
                emacolor = Fore.YELLOW
            else:
                emacolor = Fore.RED

            if ticker >= sma50:
                smacolor = Fore.GREEN
            elif ticker >= sma50 - atr * 0.5:
                smacolor = Fore.YELLOW
            else:
                smacolor = Fore.RED

            if rsi >= 70:
                rsicolor = Fore.RED
            if rsi <= 30:
                rsicolor = Fore.GREEN
            else:
                rsicolor = Fore.CYAN

            print("%-4s|%4s|%5d|%5d|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s|%s%5d%s" % (exchange,
                                                                                                        pair,
                                                                                                        unit_size,
                                                                                                        atr,
                                                                                                        Fore.CYAN,
                                                                                                        ticker,
                                                                                                        reset,
                                                                                                        rsicolor,
                                                                                                        rsi,
                                                                                                        reset,
                                                                                                        smacolor,
                                                                                                        sma,
                                                                                                        reset,
                                                                                                        emacolor,
                                                                                                        ema,
                                                                                                        reset,
                                                                                                        low55color,
                                                                                                        low55,
                                                                                                        reset,
                                                                                                        low20color,
                                                                                                        low20,
                                                                                                        reset,
                                                                                                        high20color,
                                                                                                        high20,
                                                                                                        reset,
                                                                                                        high55color,
                                                                                                        high55,
                                                                                                        reset
                                                                                                        ))
        elif type_print == PrintCurrency.none:
            print "Must include PrintCurrency.header|border|row in PrintCurrency.currency(args)"


exchangesWatch = ["gdax"]
pairWatch = ["btcusd", "bchusd", "ethusd", "ltcusd"]

colorama.init()
cwCurrency = CWCryptoWatch()
printCurrency = PrintCurrency()

jsonMarkets = cwCurrency.db_get("/markets", 60)
jsonAccounts = cwCurrency.gd_accounts()

totalBalance = 0
for ja in jsonAccounts:
    if ja['currency'] != "USD":
        jsonMarketExchangePairSummary = cwCurrency.db_get("/markets/gdax/" + ja['currency'].lower() + "usd/summary", 1)
        totalBalance += float(ja['balance']) * float(jsonMarketExchangePairSummary['price']['last'])
    else:
        totalBalance += float(ja['balance'])

array_results = []

for jm in jsonMarkets:
    if (jm['exchange'] in exchangesWatch) & (jm['pair'] in pairWatch):
        jsonMarketExchangePair = cwCurrency.db_get(jm['route'], 60)
        jsonMarketExchangePairSummary = cwCurrency.db_get(jsonMarketExchangePair['routes']['summary'], 1)
        jsonMarketExchangeOHLC = cwCurrency.db_get(jsonMarketExchangePair['routes']['ohlc'], 300)

        pricelast = jsonMarketExchangePairSummary['price']['last']
        sma50 = cwCurrency.db_get_sma(jsonMarketExchangePair['exchange'],
                                      jsonMarketExchangePair['pair'],
                                      50)
        ema20 = cwCurrency.db_get_ema(jsonMarketExchangePair['exchange'],
                                      jsonMarketExchangePair['pair'],
                                      20)
        hl55 = cwCurrency.db_get_hl(jsonMarketExchangePair['exchange'],
                                    jsonMarketExchangePair['pair'],
                                    55)
        hl20 = cwCurrency.db_get_hl(jsonMarketExchangePair['exchange'],
                                    jsonMarketExchangePair['pair'],
                                    20)
        turtles20 = cwCurrency.db_get_turtles(jsonMarketExchangePair['exchange'],
                                              jsonMarketExchangePair['pair'],
                                              jsonMarketExchangePairSummary['price']['last'],
                                              totalBalance
                                              )
        rsi14 = cwCurrency.db_get_rsi(jsonMarketExchangePair['exchange'],
                                      jsonMarketExchangePair['pair'],
                                      14,
                                      35
                                      )
        array_results.append([
                                jsonMarketExchangePair['exchange'][0:4],
                                jsonMarketExchangePair['pair'][0:3],
                                turtles20[2],
                                turtles20[0],
                                pricelast,
                                rsi14,
                                sma50,
                                ema20,
                                hl55['low'],
                                hl20['low'],
                                hl20['high'],
                                hl55['high']
                            ]
                            )

printCurrency.currency(PrintCurrency.header)
printCurrency.currency(PrintCurrency.border, total_balance=totalBalance)
for i in array_results:
    printCurrency.currency(PrintCurrency.row,
                           i[0],
                           i[1],
                           i[2],
                           i[3],
                           i[4],
                           i[5],
                           i[6],
                           i[7],
                           i[8],
                           i[9],
                           i[10],
                           i[11]
                           )
