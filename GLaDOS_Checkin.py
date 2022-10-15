# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author :
# @ Desc : 
# @ Date : 2022/7/24
# ==============================================================================
import json
import math
import os

import requests

GET_STATUS_URL = "https://glados.rocks/api/user/status"
CHECK_IN_URL = "https://glados.rocks/api/user/checkin"
COOKIE_STR = os.environ.get('GLaDOS_Cookie')
QYWX_KEY = os.environ.get('GLaDOS_Cookie')
GLaDOS_SEND = os.environ.get('GLaDOS_SEND')


class GladosCheckIn:

    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 \
            (KHTML, like Gecko) Chrome/103.0.0.0 Safari/537.36",
        }
        self.cookies = {cookie.split("=")[0]: cookie.split("=")[1] for cookie in COOKIE_STR.split(";")}
        self.res = {}

    def get_status(self):

        resp = requests.get(url=GET_STATUS_URL, headers=self.headers, cookies=self.cookies)
        resp.raise_for_status()

        data = self.resp_json(resp)
        if data["code"] != 0:
            raise Exception("get status error")

        self.res["email"] = data["data"]["email"]
        self.res["left_days"] = float(data["data"]["leftDays"])
        self.res["traffic"] = self.convert_traffic_size(int(data["data"]["traffic"]))
        self.res["used_days"] = data["data"]["days"]

        return self

    def check_in(self):

        data = {"token": "glados.network"}

        resp = requests.post(url=CHECK_IN_URL, data=data, headers=self.headers, cookies=self.cookies)
        resp.raise_for_status()

        data = self.resp_json(resp)
        self.res["message"] = data.get("message")

        return self

    def print_result(self):
        print("账号: {}".format(self.res["email"]))
        print("剩余天数: {}".format(self.res["left_days"]))
        print("流量: {}".format(self.res["traffic"]))
        print("已用天数: {}".format(self.res["used_days"]))
        print("签到情况: {}".format(self.res["message"]))
        self.wechat(self.res)

    @staticmethod
    def resp_json(resp):
        encoding = requests.utils.guess_json_utf(resp.content)
        if encoding is not None:
            try:
                return json.loads(resp.content.decode(encoding))
            except UnicodeDecodeError:
                pass
        return json.loads(resp.text)

    @staticmethod
    def convert_traffic_size(size_bytes):
        if size_bytes == 0:
            return "0B"
        size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return "%s %s" % (s, size_name[i])

    @staticmethod
    def wechat(res):
        if QYWX_KEY and GLaDOS_SEND:
            url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={QYWX_KEY}'
            text = 'GlaDOS签到详情'
            desp = "账号: {}\n剩余天数: {}\n流量: {}\n已用天数: {}\n签到情况: {}".format(
                res["email"],
                res["left_days"],
                res["traffic"],
                res["used_days"],
                res["message"]
            )
            json_data = {
                'msgtype': 'text',
                'text': {
                    'content': f'{text}\n\n{desp}',
                }
            }
            headers = {
                'Content-Type': 'application/json'
            }
            rst = requests.post(url, json=json_data, headers=headers).text
            print(rst)


if __name__ == '__main__':
    checkin = GladosCheckIn()
    checkin.check_in().get_status().print_result()
