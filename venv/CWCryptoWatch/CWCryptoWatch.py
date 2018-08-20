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
        self.log("Successfully initialized class and loaded configuration file.")

    def log(self, log_string):
        lfh = open(self.config_data['dev']['log'], "w")
        lfh.write(datetime.now().isoformat() + " - " + log_string)
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

        cursor_object.execute(createtablealerts)

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
            curema = (close[0] - prevema) * ema_weight + prevema
            prevema = curema

        self.db_close()
        return curema

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
                SELECT high, low, close
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
        cursor_object.execute(query, (url, cache_string, str(days * 2 + 1) + "days", "0 days",))
        hlc_array = cursor_object.fetchall()

        self.db_close()

        tr_sum = 0
        curr_n = 0

        if len(hlc_array) == days * 2 + 1:
            for i in range(0, days + 1, 1):
                tr_sum = tr_sum + max(hlc_array[i][0] - hlc_array[i][1],
                                      hlc_array[i][0] - hlc_array[i - 1][2],
                                      hlc_array[i - 1][2] - hlc_array[i][1]
                                      )

            prev_n = tr_sum / (days + 1)
            for i in range(days + 1, days * 2 + 1, 1):
                tr = max(hlc_array[i][0] - hlc_array[i][1],
                         hlc_array[i][0] - hlc_array[i - 1][2],
                         hlc_array[i - 1][2] - hlc_array[i][1]
                         )
                curr_n = ((days - 1) * prev_n + tr) / days

        if (lastprice > 0) & (curr_n > 0) & (balance > 0):
            dpp = balance / lastprice

            unit_size = (balance * .01) / (curr_n * dpp)
            unit_size_currency = unit_size * balance
            result_array = [curr_n, unit_size, unit_size_currency]
        else:
            result_array = [0, 0, 0]

        return result_array

    def db_get_rsi(self, exchange, pair, days_rsi, days_weight):
        cache_string = "360 minutes"
        string_days_weight = str(days_weight) + " days"
        url = self.config_data['cryptowatch']['url'] + "/markets/" + exchange + "/" + pair + "/ohlc"
        query = """
                SELECT close, 0, 0, 0, 0, 0, 0, 0
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
        cursor_object.execute(query, (url, cache_string, string_days_weight, "0 days",))
        close_array = cursor_object.fetchall()
        self.db_close()

        close_array = [list(row) for row in close_array]

        # test array, results should look like:
        # http://cns.bu.edu/~gsc/CN710/fincast/Technical%20_indicators/Relative%20Strength%20Index%20(RSI).htm
        # close_array = [
        #     [46.1250, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [47.1250, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [46.4375, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [46.9375, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [44.9375, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [44.2500, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [44.6250, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [45.7500, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [47.8125, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [47.5625, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [47.0000, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [44.5625, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [46.3125, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [47.6875, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [46.6875, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [45.6875, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [43.0625, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [43.5625, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [44.8750, 0, 0, 0, 0, 0, 0, 0, 0],
        #     [43.6875, 0, 0, 0, 0, 0, 0, 0, 0]
        # ]

        for i in range(1, len(close_array), 1):
            close_array[i][1] = close_array[i][0] - close_array[i - 1][0]
            if close_array[i][1] >= 0:
                close_array[i][2] = abs(close_array[i][1])
            else:
                close_array[i][3] = abs(close_array[i][1])

        for i in range(1, len(close_array), 1):
            if i == days_rsi:
                sum_adva = 0
                sum_decl = 0
                for j in range(i-days_rsi, days_rsi+1, 1):
                    sum_adva += close_array[j][2]
                    sum_decl += close_array[j][3]
                close_array[i][4] = sum_adva / days_rsi
                close_array[i][5] = sum_decl / days_rsi
                close_array[i][6] = close_array[i][4] / close_array[i][5]
                close_array[i][7] = 100 - (100 / (1 + close_array[i][6]))

            if i > days_rsi:
                close_array[i][4] = ((close_array[i-1][4] * 13) + close_array[i][2]) / days_rsi
                close_array[i][5] = ((close_array[i-1][5] * 13) + close_array[i][3]) / days_rsi
                close_array[i][6] = (((close_array[i-1][4] * 13) + close_array[i][2]) / days_rsi) / \
                                    (((close_array[i-1][5] * 13) + close_array[i][3]) / days_rsi)
                close_array[i][7] = 100 - (100 / (1 + close_array[i][6]))

            # if you ever need to print the chart and manually calculate rsi
            # print "%3i %10.4f %10.4f %10.4f %10.4f %10.4f %10.4f %10.4f %10.3f" % (i,
            #                                                                           close_array[i][0],
            #                                                                           close_array[i][1],
            #                                                                           close_array[i][2],
            #                                                                           close_array[i][3],
            #                                                                           close_array[i][4],
            #                                                                           close_array[i][5],
            #                                                                           close_array[i][6],
            #                                                                           close_array[i][7],
            #                                                                           close_array[i][8]
            #                                                                           )
        return close_array[len(close_array)-1][7]

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
        request = self.auth_client.get_fills(product_id=product_string, limit=100)
        return request[0]

    def gd_orders(self):
        self.gd_connect()
        request = self.auth_client.get_orders()
        return request

    def al_init(self):
        self.al_json = {
                        "trending" : {
                            "alert" : False,
                            "message" : "",
                            "pairs" : []
                            },
                        "fills" : {
                            "alert" : False,
                            "message" : "",
                            "order_ids" : []
                            },
                        "stoploss" : {
                            "alert" : False,
                            "message" : ""
                            }
                        }

    def al_db_put(self, callurl, json_object):
        return True

    def al_db_get(self, callurl):
        return True

    def al_send(self, alert_type, alert_string, subject_string=""):
        if self.config_data['dev']['mode'] == "production":
            msg = MIMEText(alert_string)

            msg['Subject'] = subject_string
            msg['From'] = self.config_data['mail']['from']
            msg['To'] = self.config_data['mail']['to']

            s = smtplib.SMTP(self.config_data['mail']['smtp'])
            s.sendmail(msg['From'], msg['To'], msg.as_string())
            s.quit()
        else:
            print(alert_string)
