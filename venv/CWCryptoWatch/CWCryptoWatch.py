import os
from pathlib import Path
import gdax
import json
import psycopg2
import re
import requests
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, date, time


class CWCryptoWatch:

    def __init__(self):
        self.postgres_object = None
        self.auth_client = None
        home = os.path.expanduser("~")
        config_json_file = Path(home + "/etc/config.json")
        if not config_json_file.is_file():
            config_json_file = Path("/etc/config.json")
        elif not config_json_file.is_file():
            print("config.json was not found in ~/etc or /etc")
        else:
            with open(str(config_json_file)) as json_data_file:
                self.config_data = json.load(json_data_file)
        self.alerts_json_data = {
                        "trending": {
                            "alert": False,
                            "message": "",
                            "pairs": []
                            },
                        "fills": {
                            "alert": False,
                            "message": "",
                            "fill_list": []
                            },
                        "stoploss": {
                            "alert": False,
                            "message": "",
                            "last_alert": ""
                            }
                        }
        self.log("Successfully initialized class and loaded configuration file.")

    def log(self, log_string):
        lfh = open(self.config_data['dev']['log'], "a+")
        lfh.write(datetime.now().isoformat() + " - " + log_string + "\n")
        lfh.close()

    def db_connect(self):
        self.postgres_object = psycopg2.connect(
            "dbname='" + self.config_data['postgresql']['dbname'] +
            "' user='" + self.config_data['postgresql']['user'] +
            "' host='" + self.config_data['postgresql']['host'] +
            "' password='" + self.config_data['postgresql']['password'] +
            "'")

    def db_commit(self):
        self.postgres_object.commit()
        return True

    def db_close(self):
        self.postgres_object.close()
        return True

    def db_initialize(self):
        tablenames = ["assets", "exchanges", "markets", "alerts"]

        querycreatetablearray = """
                        DROP TABLE public.tablename;
                        
                        CREATE TABLE public.tablename
                        (
                            id serial NOT NULL PRIMARY KEY,
                            ts timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
                            callurl text NOT NULL,
                            callresult jsonb NOT NULL
                        )
                        TABLESPACE pg_default;

                        ALTER TABLE public.tablename
                        OWNER to pgadmin;
                    """

        self.db_connect()
        cursor_object = self.postgres_object.cursor()

        for name in tablenames:
            loopquerycreate = re.sub(r"tablename", name, querycreatetablearray)

            cursor_object.execute(loopquerycreate)

        self.db_commit()
        self.db_close()

    def db_put(self, url, json_object):
        tablename = re.split("/", url)

        query = """
                    INSERT INTO tablename ( callurl, callresult ) 
                    VALUES ( %s, %s )
                """
        query = re.sub("tablename", tablename[3], query)

        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (url, json.dumps(json_object)))
        self.db_commit()

    def db_get(self, url, interval):
        interval = interval * 60
        cache_string = str(interval) + " seconds"
        if self.config_data['cryptowatch']['url'] not in url:
            url = self.config_data['cryptowatch']['url'] + url

        tablename = re.split("/", url)

        query = """
                    SELECT jsonb_extract_path(callresult, 'result') 
                    FROM tablename
                    WHERE callurl = %s AND ts >= CURRENT_TIMESTAMP - interval %s
                    ORDER BY ts DESC LIMIT 1
                """

        query = re.sub("tablename", tablename[3], query)

        self.db_connect()
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (url, cache_string,))

        if not cursor_object.fetchall():
            result = self.cw_get_url(url)
            self.db_put(url, result)

        cursor_object.execute(query, (url, cache_string,))
        result = cursor_object.fetchone()
        self.db_close()

        return result[0]

    def db_get_sma(self, exchange, pair, days):
        cache_string = '360 minutes'
        day_string = str(days) + " days"
        url = self.config_data['cryptowatch']['url'] + "/markets/" + exchange + "/" + pair + "/ohlc"
        query = """
                SELECT SUM(close)/%s
                FROM (
                    SELECT
                        to_timestamp(CAST(jsonb_array_elements(ohlc_array)->>0 AS INT)) AS ts,
                        CAST(jsonb_array_elements(ohlc_array)->>1 AS FLOAT) AS open,
                        CAST(jsonb_array_elements(ohlc_array)->>2 AS FLOAT) AS high,
                        CAST(jsonb_array_elements(ohlc_array)->>3 AS FLOAT) AS low, 
                        CAST(jsonb_array_elements(ohlc_array)->>4 AS FLOAT) AS close, 
                        CAST(jsonb_array_elements(ohlc_array)->>5 AS FLOAT) AS volume
                    FROM (
                        SELECT callresult->'result'->'86400' AS ohlc_array
                        FROM markets
                        WHERE callurl = %s AND ts >= CURRENT_TIMESTAMP - interval %s
                        ORDER BY ts DESC LIMIT 1
                        ) AS ohlc_array
                    ) AS ohlc
                WHERE ts >= CURRENT_TIMESTAMP - interval %s AND ts <= CURRENT_TIMESTAMP - interval %s
                """

        self.db_connect()
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (days, url, cache_string, day_string, "0 days",))
        result = cursor_object.fetchall()
        self.db_close()
        return result[0][0]

    def db_get_ema(self, exchange, pair, days):
        curema = None
        cache_string = '360 minutes'
        url = self.config_data['cryptowatch']['url'] + "/markets/" + exchange + "/" + pair + "/ohlc"
        ema_weight = 2 / (float(days) + 1)
        query = """
                SELECT columnname
                FROM (
                    SELECT
                        to_timestamp(CAST(jsonb_array_elements(ohlc_array)->>0 AS INT)) AS ts,
                        CAST(jsonb_array_elements(ohlc_array)->>1 AS FLOAT) AS open,
                        CAST(jsonb_array_elements(ohlc_array)->>2 AS FLOAT) AS high,
                        CAST(jsonb_array_elements(ohlc_array)->>3 AS FLOAT) AS low,
                        CAST(jsonb_array_elements(ohlc_array)->>4 AS FLOAT) AS close,
                        CAST(jsonb_array_elements(ohlc_array)->>5 AS FLOAT) AS volume
                    FROM (
                        SELECT callresult->'result'->'86400' AS ohlc_array
                        FROM markets
                        WHERE callurl = %s AND ts >= CURRENT_TIMESTAMP - interval %s
                        ORDER BY ts DESC LIMIT 1
                        ) AS ohlc_array
                    ) AS ohlc
                WHERE ts >= CURRENT_TIMESTAMP - interval %s AND ts <= CURRENT_TIMESTAMP - interval %s
                """

        self.db_connect()
        querysma = re.sub("columnname", "SUM(close)/" + str(days), query)
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(querysma, (url, cache_string, str(days * 2) + " days", str(days) + " days",))
        result = cursor_object.fetchall()
        prevema = result[0][0]

        query20dayclose = re.sub("columnname", "close", query)
        cursor_object.execute(query20dayclose, (url, cache_string, str(days) + " days", "0 days",))
        result = cursor_object.fetchall()

        for close in result:
            ema_curr = (close[0] - prevema) * ema_weight + prevema
            ema_prev = ema_curr

        self.db_close()
        return ema_curr

    def db_get_hl(self, exchange, pair, days):
        cache_string = '360 minutes'
        url = self.config_data['cryptowatch']['url'] + "/markets/" + exchange + "/" + pair + "/ohlc"
        query = """
                SELECT to_json (ohlcResults)
                FROM (
                    SELECT columnname
                    FROM (
                        SELECT
                            to_timestamp(CAST(jsonb_array_elements(ohlc_array)->>0 AS INT)) AS ts,
                            CAST(jsonb_array_elements(ohlc_array)->>1 AS FLOAT) AS open,
                            CAST(jsonb_array_elements(ohlc_array)->>2 AS FLOAT) AS high,
                            CAST(jsonb_array_elements(ohlc_array)->>3 AS FLOAT) AS low,
                            CAST(jsonb_array_elements(ohlc_array)->>4 AS FLOAT) AS close,
                            CAST(jsonb_array_elements(ohlc_array)->>5 AS FLOAT) AS volume
                        FROM (
                            SELECT callresult->'result'->'86400' AS ohlc_array
                            FROM markets
                            WHERE callurl = %s AND ts >= CURRENT_TIMESTAMP - interval %s
                            ORDER BY ts DESC LIMIT 1
                        ) AS ohlc_array
                    ) AS ohlc
                    WHERE ts >= CURRENT_TIMESTAMP - interval %s AND ts <= CURRENT_TIMESTAMP - interval %s
                ) AS ohlcResults
                """

        self.db_connect()
        query = re.sub("columnname", "MAX(high) AS high, MIN(low) AS low", query)
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (url, cache_string, str(days) + " days", "0 days",))
        result = cursor_object.fetchall()

        self.db_close()
        return result[0][0]

    def db_get_turtles(self, exchange, pair, lastprice, balance):
        days = 20
        cache_string = '360 minutes'
        url = self.config_data['cryptowatch']['url'] + "/markets/" + exchange + "/" + pair + "/ohlc"
        query = """
                SELECT array_to_json(array_agg(row_to_json(ohlcResults)))
                FROM (
                    SELECT *
                    FROM (
                        SELECT
                            to_timestamp(CAST(jsonb_array_elements(ohlc_array)->>0 AS INT)) AS ts,
                            CAST(jsonb_array_elements(ohlc_array)->>1 AS FLOAT) AS open,
                            CAST(jsonb_array_elements(ohlc_array)->>2 AS FLOAT) AS high,
                            CAST(jsonb_array_elements(ohlc_array)->>3 AS FLOAT) AS low,
                            CAST(jsonb_array_elements(ohlc_array)->>4 AS FLOAT) AS close,
                            CAST(jsonb_array_elements(ohlc_array)->>5 AS FLOAT) AS volume
                        FROM (
                            SELECT callresult->'result'->'86400' AS ohlc_array
                            FROM markets
                            WHERE callurl = %s AND ts >= CURRENT_TIMESTAMP - interval %s
                            ORDER BY ts DESC LIMIT 1
                        ) AS ohlc_array
                    ) AS ohlc
                    WHERE ts >= CURRENT_TIMESTAMP - interval %s AND ts <= CURRENT_TIMESTAMP - interval %s
                ) as ohlcResults
                """

        self.db_connect()
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (url, cache_string, str(days * 2 + 1) + " days", "0 days",))
        json_hlc = cursor_object.fetchone()[0]
        self.db_close()

        tr_sum = 0
        curr_n = 0

        if len(json_hlc) == days * 2 + 1:
            for i in range(0, days + 1, 1):
                tr_sum = tr_sum + max(json_hlc[i]['high'] - json_hlc[i]['low'],
                                      json_hlc[i]['high'] - json_hlc[i - 1]['close'],
                                      json_hlc[i - 1]['close'] - json_hlc[i]['low']
                                      )

            prev_n = tr_sum / (days + 1)
            for i in range(days + 1, days * 2 + 1, 1):
                tr = max(json_hlc[i]['high'] - json_hlc[i]['low'],
                         json_hlc[i]['high'] - json_hlc[i - 1]['close'],
                         json_hlc[i - 1]['close'] - json_hlc[i]['low']
                         )
                curr_n = ((days - 1) * prev_n + tr) / days

        if (lastprice > 0) & (curr_n > 0) & (balance > 0):
            dpp = balance / lastprice

            unit_size = (balance * .01) / (curr_n * dpp)
            unit_size_currency = unit_size * balance
            json_result = {
                "atr": curr_n,
                "u_size": unit_size,
                "u_size_dollars": unit_size_currency
            }
        else:
            json_result = {
                "atr": 0,
                "u_size:": 0,
                "u_size_dollars": 0
            }

        return json_result

    def db_get_rsi(self, exchange, pair, days_rsi, days_weight):
        cache_string = "360 minutes"
        string_days_weight = str(days_weight) + " days"
        url = self.config_data['cryptowatch']['url'] + "/markets/" + exchange + "/" + pair + "/ohlc"
        query = """
                SELECT array_to_json(array_agg(row_to_json(ohlcResults)))
                FROM (
                    SELECT close, 0 as change, 0 as gain, 0 as loss, 0 as avg_gain, 0 as avg_loss, 0 as rs, 0 as rsi
                    FROM (
                        SELECT
                            to_timestamp(CAST(jsonb_array_elements(ohlc_array)->>0 AS INT)) AS ts,
                            CAST(jsonb_array_elements(ohlc_array)->>1 AS FLOAT) AS open,
                            CAST(jsonb_array_elements(ohlc_array)->>2 AS FLOAT) AS high,
                            CAST(jsonb_array_elements(ohlc_array)->>3 AS FLOAT) AS low,
                            CAST(jsonb_array_elements(ohlc_array)->>4 AS FLOAT) AS close,
                            CAST(jsonb_array_elements(ohlc_array)->>5 AS FLOAT) AS volume
                        FROM (
                            SELECT callresult->'result'->'86400' AS ohlc_array
                            FROM markets
                            WHERE callurl = %s AND ts >= CURRENT_TIMESTAMP - interval %s
                            ORDER BY ts DESC LIMIT 1
                            ) AS ohlc_array
                        ) AS ohlc
                    WHERE ts >= CURRENT_TIMESTAMP - interval %s AND ts <= CURRENT_TIMESTAMP - interval %s
                ) as ohlcResults
                """

        self.db_connect()
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (url, cache_string, string_days_weight, "0 days",))
        json_rsi = cursor_object.fetchone()[0]
        self.db_close()

        for i in range(1, len(json_rsi), 1):
            json_rsi[i]['change'] = json_rsi[i]['close'] - json_rsi[i - 1]['close']
            if json_rsi[i]['change'] >= 0:
                json_rsi[i]['gain'] = abs(json_rsi[i]['change'])
            else:
                json_rsi[i]['loss'] = abs(json_rsi[i]['change'])

        for i in range(1, len(json_rsi), 1):
            if i == days_rsi:
                sum_gain = 0
                sum_loss = 0
                for j in range(i-days_rsi, days_rsi+1, 1):
                    sum_gain += json_rsi[j]['gain']
                    sum_loss += json_rsi[j]['loss']
                json_rsi[i]['avg_gain'] = sum_gain / days_rsi
                json_rsi[i]['avg_loss'] = sum_loss / days_rsi
                json_rsi[i]['rs'] = json_rsi[i]['avg_gain'] / json_rsi[i]['avg_loss']
                json_rsi[i]['rsi'] = 100 - (100 / (1 + json_rsi[i]['rs']))

            if i > days_rsi:
                json_rsi[i]['avg_gain'] = ((json_rsi[i-1]['avg_gain'] * 13) + json_rsi[i]['gain']) / days_rsi
                json_rsi[i]['avg_loss'] = ((json_rsi[i-1]['avg_loss'] * 13) + json_rsi[i]['loss']) / days_rsi
                json_rsi[i]['rs'] = (((json_rsi[i-1]['avg_gain'] * 13) + json_rsi[i]['gain']) / days_rsi) / \
                                    (((json_rsi[i-1]['avg_loss'] * 13) + json_rsi[i]['loss']) / days_rsi)
                json_rsi[i]['rsi'] = 100 - (100 / (1 + json_rsi[i]['rs']))

        return json_rsi[len(json_rsi)-1]['rsi']

    def cw_status(self):
        requests.get(
            self.config_data['cryptowatch']['url'],
            timeout=self.config_data['cryptowatch']['timeout']
        ).json()

    def cw_get_url(self, url):
        if self.config_data['cryptowatch']['url'] not in url:
            url = self.config_data['cryptowatch']['url'] + url

        results = requests.get(
            url,
            timeout=self.config_data['cryptowatch']['timeout']
        ).json()

        return results

    def gd_connect(self):
        self.auth_client = gdax.AuthenticatedClient(self.config_data['coinbasepro']['key'],
                                                    self.config_data['coinbasepro']['secret'],
                                                    self.config_data['coinbasepro']['passphrase']
                                                    )

    def gd_accounts(self):
        self.gd_connect()
        request = self.auth_client.get_accounts()
        return request

    def gd_fills(self, product_string="BTC-USD"):
        self.gd_connect()
        request = self.auth_client.get_fills(product_id=product_string, limit=1)
        return request[0]

    def gd_orders(self):
        self.gd_connect()
        request = self.auth_client.get_orders()
        return request

    def al_db_put(self):
        query = """
                    INSERT INTO alerts ( callurl, callresult ) 
                    VALUES ( %s, %s )
                """

        self.db_connect()
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, ("alerts", json.dumps(self.alerts_json_data)))
        self.db_commit()
        self.db_close()

    def al_db_get(self, callurl):
        query = """
                    SELECT callresult->%s
                    FROM alerts
                    WHERE callresult->%s IS NOT NULL
                    ORDER BY ts DESC LIMIT 1
                """

        self.db_connect()
        cursor_object = self.postgres_object.cursor()
        cursor_object.execute(query, (callurl, callurl,))
        result = cursor_object.fetchone()
        self.db_close()

        if not result:
            return []

        return result[0]

    def al_send(self):
        self.al_db_put()

        for als in [ "trending", "fills", "stoploss" ]:
            if self.alerts_json_data[als]['alert']:
                if self.config_data['dev']['mode'] == "production":
                    msg = MIMEText(als + ": " + self.alerts_json_data[als]['message'])

                    msg['From'] = self.config_data['mail']['from']
                    msg['To'] = self.config_data['mail']['to']

                    s = smtplib.SMTP(self.config_data['mail']['smtp'])
                    s.sendmail(msg['From'], msg['To'], msg.as_string())
                    s.quit()
                else:
                    print(als + ": " + self.alerts_json_data[als]['message'])

    def al_trending(self, current_atr_list):
        if self.config_data['dev']['mode'] == "production":
            atr_change = 0.33
        else:
            atr_change = 0.0000001

        previous_alert = self.al_db_get("trending")

        json_pair_list = []
        if not previous_alert:
            self.alerts_json_data['trending']['pairs'] = current_atr_list
            self.alerts_json_data['trending']['alert'] = True
            self.alerts_json_data['trending']['message'] = "all"
        else:
            for jc in current_atr_list:
                for jp in previous_alert['pairs']:
                    if jp['pair'] == jc['pair']:
                        if jc['last'] >= jp['last'] + jc['atr'] * atr_change:
                            self.alerts_json_data['trending']['message'] = \
                                self.alerts_json_data['trending']['message'] + jc['pair'] + "+" + \
                                str(round(jc['last'],0)) + " "
                            self.alerts_json_data['trending']['alert'] = True
                            json_pair_list.append(jc)
                        elif jc['last'] <= jp['last'] - jc['atr'] * atr_change:
                            self.alerts_json_data['trending']['message'] = \
                                self.alerts_json_data['trending']['message'] + jc['pair'] + "-" + \
                                str(round(jc['last'],0)) + " "
                            json_pair_list.append(jc)
                        else:
                            json_pair_list.append(jp)
            self.alerts_json_data['trending']['pairs'] = json_pair_list

    def al_fills(self, current_fill_list):
        # select ts, callresult from alerts where (callresult->'fills'->'orders')::jsonb ? '1';
        # example of how to search for specific fill/order id in json/pgsql, use this later

        previous_alert = self.al_db_get("fills")

        json_fill_list = []
        if not previous_alert:
            self.alerts_json_data['fills']['fill_list'] = current_fill_list
            self.alerts_json_data['fills']['alert'] = True
            self.alerts_json_data['fills']['message'] = "all"
        else:
            for jc in current_fill_list:
                for jp in previous_alert['fill_list']:
                    if jp['product_id'] == jc['product_id']:
                        if jc['trade_id'] > jp['trade_id']:
                            self.alerts_json_data['fills']['message'] = \
                                self.alerts_json_data['fills']['message'] + " " + jc['product_id']
                            self.alerts_json_data['fills']['alert'] = True
                            json_fill_list.append(jc)
                        else:
                            json_fill_list.append(jp)
            self.alerts_json_data['fills']['fill_list'] = json_fill_list

    def al_stoploss(self, stoploss_list):

        previous_alert = self.al_db_get("stoploss")

        if previous_alert:
            if stoploss_list:
                self.alerts_json_data['stoploss']['alert'] = True
                self.alerts_json_data['stoploss']['last_alert'] = str(datetime.now())
                for sl in stoploss_list:
                    self.alerts_json_data['stoploss']['message'] = \
                        self.alerts_json_data['stoploss']['message'] + sl + " "
