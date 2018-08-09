import smtplib
from email.mime.text import MIMEText
from CWCryptoWatch.CWCryptoWatch import CWCryptoWatch


msg = MIMEText("hello world")

msg['Subject'] = "subject Hello World"
msg['To'] = "cwilkerson@gmail.com"
msg['From'] = "cryptowatch@syzygy.io"

s = smtplib.SMTP('localhost')
s.sendmail(msg['From'], msg['To'], msg.as_string())
s.quit()
