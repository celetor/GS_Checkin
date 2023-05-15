#!/usr/bin/python3
# -- coding: utf-8 --
# -------------------------------
# @Author : github@wd210010 https://github.com/wd210010/just_for_happy
# @Time : 2023/2/27 13:23
# -------------------------------
# cron "6,10,15 * * *" script-path=xxx.py,tag=匹配cron用
# const $ = new Env('一点万象签到')

import requests, time, hashlib, json
import os

# 一点万向签到领万向星 可抵扣停车费
# 登录后搜索https://app.mixcapp.com/mixc/gateway域名随意一个 请求体里面的deviceParams，token 多账号填多个单引号里面 用英文逗号隔开
QYWX_KEY = os.environ.get('QYWX_KEY')
# 青龙变量 ydwx_deviceParams ydwx_token
YDWX_BODY = 'mallNo=330281C001&appId=68a91a5bac6a4f3e91bf4b42856785c6&platform=h5&imei=2333&appVersion=3.32.0&osVersion=12.0.1&action=mixc.app.memberSign.signDate&apiVersion=1.0&timestamp=1684126791577&deviceParams=eyJwaG9uZSI6IiJ9&token=bc282fbcca714d8ab0400d07c47eb9ee&params=eyJtYWxsTm8iOiIzMzAyODFDMDAxIn0&sign=c124002de4782443be6a1ae7ab3b65ca'#os.environ.get('YDWX_BODY')


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


def Push(contents):
    # 推送加 token
    plustoken = os.getenv("plustoken")
    if plustoken:
        # plustoken推送
        headers = {'Content-Type': 'application/json'}
        json = {"token": plustoken, 'title': '一点万向签到', 'content': contents.replace('\n', '<br>'),
                "template": "json"}
        resp = requests.post(f'http://www.pushplus.plus/send', json=json, headers=headers).json()
        print('push+推送成功' if resp['code'] == 200 else 'push+推送失败')


def checkin(ydwx_deviceParams, ydwx_token, mall='20014'):
    log = []
    for i in range(len(ydwx_deviceParams)):
        # print(f'*****第{str(i + 1)}个账号*****')
        timestamp = str(int(round(time.time() * 1000)))
        md5 = hashlib.md5()
        md52 = hashlib.md5()
        sig = f'action=mixc.app.memberSign.sign&apiVersion=1.0&appId=68a91a5bac6a4f3e91bf4b42856785c6&appVersion=3.32.0&deviceParams={ydwx_deviceParams[i]}&imei=2333&mallNo={mall}&osVersion=12.0.1&params=eyJtYWxsTm8iOiIyMDAxNCJ9&platform=h5&timestamp={timestamp}&token={ydwx_token[i]}&P@Gkbu0shTNHjhM!7F'  # 创建md5加密对象
        md5.update(sig.encode('utf-8'))  # 指定需要加密的字符串
        sign = md5.hexdigest()  # 加密后的字符串
        url = 'https://app.mixcapp.com/mixc/gateway'
        headers = {
            'Host': 'app.mixcapp.com',
            'Connection': 'keep-alive',
            'Content-Length': '564',
            'Accept': 'application/json, text/plain, */*',
            'Origin': 'https://app.mixcapp.com',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; PCAM00 Build/QKQ1.190918.001; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/77.0.3865.92 Mobile Safari/537.36/MIXCAPP/3.42.2/AnalysysAgent/Hybrid',
            'Sec-Fetch-Mode': 'cors',
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-Requested-With': 'com.crland.mixc',
            'Sec-Fetch-Site': 'same-origin',
            'Referer': f'https://app.mixcapp.com/m/m-20014/signIn?showWebNavigation=true&timestamp=1676906528979&appVersion=3.42.2&mallNo={mall}',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7'
        }
        data = f'mallNo={mall}&appId=68a91a5bac6a4f3e91bf4b42856785c6&platform=h5&imei=2333&appVersion=3.32.0&osVersion=12.0.1&action=mixc.app.memberSign.sign&apiVersion=1.0&timestamp={timestamp}&deviceParams={ydwx_deviceParams[i]}&token={ydwx_token[i]}&params=eyJtYWxsTm8iOiIyMDAxNCJ9&sign={sign}'
        html = requests.post(url=url, headers=headers, data=data)
        result = f'帐号{i + 1}签到结果:' + '' + json.loads(html.text)['message']
        print(result)
        log.append(result)
    log2 = str(log).replace('[\'', '').replace('\']', '').replace(':', '\n').replace('\', \'', '\n')
    # print(log2)
    Push(contents=log2)
    wechat('一点万象签到', log2)


if __name__ == '__main__':
    if YDWX_BODY and len(YDWX_BODY) > 0:
        all_body = YDWX_BODY.split('&&')
        print(f'共配置了{len(all_body)}个账号')
        for per_body in all_body:
            param = {}
            for kv in str(per_body).split('&'):
                arr = kv.split('=')
                if len(arr) == 2:
                    param[arr[0]] = arr[1]
            deviceParams = param['deviceParams']
            token = param['token']
            checkin(deviceParams, token, '330281C001')
