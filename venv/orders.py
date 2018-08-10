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

array_buy = []
array_sell = []

for jo in jsonOrders[0]:
    if jo['side'] == "sell":
        if jo['type'] == "limit":
            price_sell = float(jo['size']) * float(jo['price'])
            array_sell.append([
                             jo['product_id'][0:3].lower(),
                             jo['type'],
                             price_sell,
                             float(jo['price'])
                             ])
        elif jo['type'] == "market":
            price_sell = float(jo['size']) * float(jo['stop_price'])
            array_sell.append([
                             jo['product_id'][0:3].lower(),
                             jo['type'],
                             price_sell,
                             float(jo['stop_price'])
                             ])

for jo in jsonOrders[0]:
    if jo['side'] == "buy":
        if jo['type'] == "limit":
            price_buy = float(jo['size']) * float(jo['price'])
            array_buy.append([
                            jo['product_id'][0:3].lower(),
                            jo['type'],
                            price_buy,
                            float(jo['price'])
                            ])
        elif jo['type'] == "market":
            array_buy.append([
                            jo['product_id'][0:3].lower(),
                            jo['type'],
                            float(jo['specified_funds']),
                            float(jo['stop_price'])
                            ])

printOrders.sell(printOrders.header)
printOrders.sell(printOrders.border)

for i in array_sell:
    printOrders.sell(printOrders.row,
                     i[0],
                     i[1],
                     i[2],
                     i[3]
                     )

print
printOrders.buy(printOrders.header)
printOrders.buy(printOrders.border)

for i in array_buy:
    printOrders.buy(printOrders.row,
                     i[0],
                     i[1],
                     i[2],
                     i[3]
                     )
