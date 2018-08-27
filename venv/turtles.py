from colorama import Fore, Back, Style
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


class PrintOrders:

    json_data = {
        "turtles": [
            {
                "tag": "header",
                "product_id": "cur",
                "type": "type",
                "u_size": "size",
                "price_current": "cur$",
                "price_sell": "sel$",
                "price": "trig"
            }
        ],
        "buy": [
            {
                "tag": "header",
                "product_id": "cur",
                "type": "type",
                "u_size": "size",
                "price_buy": "pur$",
                "price": "trig"
            }
        ]
    }

    def prn(self):
        for jol in self.json_data['sell']:
            if jol['tag'] == "header":
                print("%3s %7s %6s %5s %5s %5s" % (
                    jol['product_id'],
                    jol['type'],
                    jol['u_size'],
                    jol['price_current'],
                    jol['price_sell'],
                    jol['price']
                    )
                )
                print("------------------------------------")
            elif jol['tag'] == "row":
                if jol['type'] == "market":
                    typecolor = Fore.RED
                else:
                    typecolor = Fore.GREEN
                print("%3s|%s%7s%s|%1.4f|%5d|%5d|%5d" % (
                    jol['product_id'],
                    typecolor,
                    jol['type'],
                    Fore.RESET,
                    jol['u_size'],
                    jol['price_current'],
                    jol['price_sell'],
                    jol['price']
                    )
                )

        print

        for jol in self.json_data['buy']:
            if jol['tag'] == "header":
                print("%3s %7s %6s %5s %5s %5s" % (
                    jol['product_id'],
                    jol['type'],
                    jol['u_size'],
                    "",
                    jol['price_buy'],
                    jol['price']
                    )
                )
                print("------------------------------------")
            elif jol['tag'] == "row":
                print("%3s|%s%7s%s|%1.4f|%5s|%5d|%5d" % (
                    jol['product_id'],
                    Fore.GREEN,
                    jol['type'],
                    Fore.RESET,
                    jol['u_size'],
                    "",
                    jol['price_buy'],
                    jol['price']
                    )
                )

cwOrders = CWCryptoWatch()
jsonAccounts = cwOrders.gd_accounts()
orderDashboard = PrintOrders()
jsonMarkets = cwOrders.db_get("/markets", 60)

jsonOrders = cwOrders.gd_orders()

for jo in jsonOrders[0]:
    jsonMarketExchangePairSummary = cwOrders.db_get("/markets/gdax/" + jo['product_id'][0:3].lower() + "usd/summary", 1)
    if jo['side'] == "sell":
        price_cur = float(jo['size']) * float(jsonMarketExchangePairSummary['price']['last'])
        if jo['type'] == "limit":
            price_sell = float(jo['size']) * float(jo['price'])
            orderDashboard.json_data['sell'].append(
                {
                    "tag": "row",
                    "product_id": jo['product_id'][0:3].lower(),
                    "type": jo['type'],
                    "u_size": float(jo['size']),
                    "price_current": price_cur,
                    "price_sell": price_sell,
                    "price":  float(jo['price'])
                }
            )
        elif jo['type'] == "market":
            price_sell = float(jo['size']) * float(jo['stop_price'])
            orderDashboard.json_data['sell'].append(
                {
                    "tag": "row",
                    "product_id": jo['product_id'][0:3].lower(),
                    "type": jo['type'],
                    "u_size": float(jo['size']),
                    "price_current": price_cur,
                    "price_sell": price_sell,
                    "price": float(jo['stop_price'])
                }
            )

for jo in jsonOrders[0]:
    jsonMarketExchangePairSummary = cwOrders.db_get("/markets/gdax/" + jo['product_id'][0:3].lower() + "usd/summary", 1)
    if jo['side'] == "buy":
        if jo['type'] == "limit":
            price_buy = float(jo['size']) * float(jo['price'])
            unitSize = price_buy / float(jo['price'])
            orderDashboard.json_data['buy'].append(
                {
                    "tag": "row",
                    "product_id": jo['product_id'][0:3].lower(),
                    "type": jo['type'],
                    "u_size": unitSize,
                    "price_buy": price_buy,
                    "price": float(jo['price'])
                }
            )
        elif jo['type'] == "market":
            unitSize = float(jo['specified_funds']) / float(jo['stop_price'])
            orderDashboard.json_data['buy'].append(
                {
                    "tag": "row",
                    "product_id": jo['product_id'][0:3].lower(),
                    "type": jo['type'],
                    "u_size": unitSize,
                    "price_buy": float(jo['specified_funds']),
                    "price": float(jo['stop_price'])
                }
            )

orderDashboard.prn()
