import sqlite3
import datetime
import os
import requests

QYWX_KEY = os.environ.get('QYWX_KEY')


def wechat(title, text):
    if QYWX_KEY:
        url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}'
        json_data = {
            'msgtype': 'text',
            'text': {
                'content': f'{title}\n\n{text}',
            }
        }
        headers = {
            'Content-Type': 'application/json'
        }
        rst = requests.post(url, json=json_data, headers=headers).text
        print(rst)


def get_time(n, fmt='%Y-%m-%d %H:%M:%S'):
    # 北京时间
    utc_time = datetime.datetime.utcnow()
    china_time = utc_time + datetime.timedelta(hours=8)
    # 往前n天
    final_date = china_time - datetime.timedelta(days=n)

    return final_date.strftime(fmt)


class OaDataBase:

    def __init__(self, path):
        self.conn = sqlite3.connect(path)

    def query_data(self, domain, date):
        cursor = self.conn.cursor()
        sql = f"select domain,date,days from renew_tbl where domain='{domain}' and date='{date}'"
        cursor.execute(sql)
        result = cursor.fetchone()
        cursor.close()
        if result:
            return {
                'domain': result[0],
                'date': result[1],
                'days': result[2]
            }
        else:
            return None

    def get_domain_list(self):
        cursor = self.conn.cursor()
        sql = f"select distinct domain from renew_tbl"
        cursor.execute(sql)
        result = cursor.fetchall()
        cursor.close()
        if result:
            return [r[0] for r in result]
        else:
            return []

    def insert_data(self, domain, date, days):
        cursor = self.conn.cursor()
        sql = f'insert into renew_tbl(domain,date,days) values("{domain}","{date}","{days}")'
        cursor.execute(sql)
        self.conn.commit()
        cursor.close()

    def update_cookies(self, domain, days):
        cursor = self.conn.cursor()
        sql = f'update renew_tbl set days="{days}" where domain="{domain}"'
        cursor.execute(sql)
        self.conn.commit()
        cursor.close()

    def close(self):
        self.conn.close()


def main():
    db = OaDataBase('freenom.db')
    today = get_time(0, '%Y-%m-%d')
    yesterday = get_time(1, '%Y-%m-%d')
    domain_list = db.get_domain_list()
    info_list = []
    for domain in domain_list:
        data = db.query_data(domain, today)
        if data:
            info_list.append(data)
            print(f'found {domain} {today} {data["days"]}')
        else:
            data = db.query_data(domain, yesterday)
            if data:
                print(f'found {domain} {yesterday} {data["days"]}')
                info_list.append({
                    'domain': domain,
                    'date': today,
                    'days': int(data['days']) - 1
                })
                db.insert_data(domain, today, int(data['days']) - 1)
    print(info_list)
    info = '\n'.join([f'{i["domain"]}\t{i["date"]}\t{i["days"]}天' for i in info_list])
    wechat('freenom续期', info)


main()
