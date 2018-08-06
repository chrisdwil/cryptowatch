import colorama
from colorama import Fore, Back, Style
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


class PrintOrders:

    none = 0
    header = 1
    border = 2
    row = 3

    def sell(self,
             type_print=0,
             currency="None",
             type_sell="None",
             price_sell=0,
             trigger=0
             ):
        if type_print == PrintOrders.header:
            print "%3s %7s %5s %5s" % ("cur", "type", "sel$", "trig")
        elif type_print == PrintOrders.border:
            print "-----------------------"
        elif type_print == PrintOrders.row:
            print "%3s|%s%7s%s|%5d|%5d" % (currency, Fore.RED, type_sell, Fore.RESET, price_sell, trigger)
        elif type_print == PrintOrders.none:
            print "Must include PrintOrders.header|border|row in PrintOrders.sell(args)"

    def buy(self, type_print=0,
            currency="None",
            type_buy="None",
            price_purchase=0,
            trigger=0
            ):
        if type_print == PrintOrders.header:
            print "%3s %7s %5s %5s" % ("cur", "type", "pur$", "trig")
        elif type_print == PrintOrders.border:
            print "-----------------------"
        elif type_print == PrintOrders.row:
            print "%3s|%s%7s%s|%5d|%5d" % (currency, Fore.GREEN, type_buy, Fore.RESET, price_purchase, trigger)
        elif type_print == PrintOrders.none:
            print "Must include PrintOrders.header|border|row in PrintOrders.buy(args)"

cwOrders = CWCryptoWatch()
jsonAccounts = cwOrders.gd_accounts()
printOrders = PrintOrders()
jsonMarkets = cwOrders.db_get("/markets", 60)

jsonOrders = cwOrders.gd_orders()

printOrders.sell(printOrders.header)
printOrders.sell(printOrders.border)

for jo in jsonOrders[0]:
    if jo['side'] == "sell":
        if jo['type'] == "limit":
            price_sell = float(jo['size']) * float(jo['price'])
            printOrders.sell(printOrders.row,
                             jo['product_id'][0:3].lower(),
                             jo['type'],
                             price_sell,
                             float(jo['price'])
                             )
        elif jo['type'] == "market":
            price_sell = float(jo['size']) * float(jo['stop_price'])
            printOrders.sell(printOrders.row,
                             jo['product_id'][0:3].lower(),
                             jo['type'],
                             price_sell,
                             float(jo['stop_price'])
                             )

print
printOrders.buy(printOrders.header)
printOrders.buy(printOrders.border)

for jo in jsonOrders[0]:
    if jo['side'] == "buy":
        if jo['type'] == "limit":
            printOrders.buy(printOrders.row,
                            jo['product_id'][0:3].lower(),
                            jo['type'],
                            float(jo['specified_funds']),
                            float(jo['price'])
                            )
        elif jo['type'] == "market":
            printOrders.buy(printOrders.row,
                            jo['product_id'][0:3].lower(),
                            jo['type'],
                            float(jo['specified_funds']),
                            float(jo['stop_price'])
                            )
