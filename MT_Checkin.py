import os
import re
import requests

MT_Cookie = os.environ.get('MT_Cookie')
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


def checkin(mt_cookie):
    cookies = {}
    for kv in re.split(r';\s*', mt_cookie):
        arr = kv.split('=')
        if len(arr) == 2:
            cookies[arr[0]] = arr[1]
    headers = {
        'authority': 'bbs.binmt.cc',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'referer': 'https://bbs.binmt.cc/member.php?mod=logging&action=login&mobile=2',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-user': '?1',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/110.0.0.0',
    }
    try:
        res = requests.get("https://bbs.binmt.cc/k_misign-sign.html", headers=headers, cookies=cookies).text
        print(res)
        form_hash = re.search(r'formhash=([^&]+)&', res)
        if form_hash and res.find('登录') == -1:
            sign_url = f'https://bbs.binmt.cc/k_misign-sign.html?operation=qiandao&format=button&formhash=' + \
                       form_hash.group(1) + '&inajax=1&ajaxtarget=midaben_sign'
            headers['referer'] = "https://bbs.binmt.cc/k_misign-sign.html"
            res2 = requests.get(sign_url, headers=headers, cookies=cookies).text
            if res2.find('今日已签') > -1:
                msg = "今天已经签到过啦"
            elif res2.find('签到成功') > -1:
                msg1 = re.search(r'获得随机奖励\s*\d+\s*金币', res2)
                msg2 = re.search(r'已累计签到\s*\d+\s*天', res2)
                msg = "签到成功\n" + msg1.group() + "\n" + msg2.group()
            else:
                msg = "签到失败!原因未知" + f"：\n{res2}"
        else:
            msg = "cookie失效"
    except Exception as e:
        msg = f"签到接口请求出错:{e}"
    print(msg)
    wechat('MT论坛签到详情', msg)


if __name__ == '__main__':
    if MT_Cookie and len(MT_Cookie) > 0:
        all_cookies = MT_Cookie.split('&&')
        for per_cookie in all_cookies:
            checkin(per_cookie)

