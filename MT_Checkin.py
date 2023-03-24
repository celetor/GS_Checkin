import os
import re
import requests

MT_Cookie = os.environ.get('MT_Cookie')
QYWX_KEY = os.environ.get('QYWX_KEY')

HEADERS = {
    'authority': 'bbs.binmt.cc',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;'
              'q=0.8,application/signed-exchange;v=b3;q=0.7',
    'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
    'referer': 'https://bbs.binmt.cc/member.php?mod=logging&action=login&mobile=2',
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) '
                  'Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/110.0.0.0',
}


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


def get_point_info(cookies):
    try:
        headers = HEADERS.copy()
        headers['referer'] = "https://bbs.binmt.cc/home.php?mod=space&do=profile&mycenter=1"
        res3 = requests.get('https://bbs.binmt.cc/home.php?mod=spacecp&ac=credit',
                            headers=headers, cookies=cookies).text
        msg1 = re.search(r'积分:\s*<span>\s*(\d+)\s*<', res3)
        msg2 = re.search(r'金币:\s*</span>\s*(\d+)\s*[^<]*<', res3)
        msg3 = re.search(r'好评:\s*</span>\s*(\d+)\s*<', res3)
        msg4 = re.search(r'信誉:\s*</span>\s*(\d+)\s*<', res3)
        message = f'积分: {msg1.group(1)}\n金币: {msg2.group(1)}\n好评: {msg3.group(1)}\n信誉: {msg4.group(1)}'
    except Exception:
        message = ''
    return message


def checkin(mt_cookie):
    cookies = {}
    for kv in re.split(r';\s*', mt_cookie):
        arr = kv.split('=')
        if len(arr) == 2:
            cookies[arr[0]] = arr[1]
    headers = HEADERS.copy()
    try:
        res = requests.get("https://bbs.binmt.cc/k_misign-sign.html", headers=headers, cookies=cookies).text
        form_hash = re.search(r'formhash=([^&]+)&', res)
        if form_hash and res.find('登录') == -1:
            try:
                msg1 = re.search(r'<h2 class="fyy">\s*([^<]+)<', res)
                msg2 = re.search(r'comiis_tm">签到等级\s*([^<]+)<', res)
                message1 = f'用户: {msg1.group(1)}\n等级: {msg2.group(1)}\n\n'
            except Exception:
                message1 = '用户信息获取失败\n\n'
            # sign_url = 'https://bbs.binmt.cc/k_misign-sign.html?operation=qiandao&format=button&formhash=' + \
            #            form_hash.group(1) + '&inajax=1&ajaxtarget=midaben_sign'
            sign_url = 'https://bbs.binmt.cc/plugin.php?id=k_misign:sign&operation=qiandao&format=text&formhash=' + \
                       form_hash.group(1)
            headers['referer'] = "https://bbs.binmt.cc/k_misign-sign.html"
            res2 = requests.get(sign_url, headers=headers, cookies=cookies).text
            if res2.find('今日已签') > -1:
                try:
                    msg1 = re.search(r'连续签到[^>]*>\s*(\d+)\s*天<', res)
                    msg2 = re.search(r'累计签到[^>]*>\s*(\d+)\s*天<', res)
                    message2 = f'今天已经签到过啦\n连续签到: {msg1.group(1)}天\n累计签到: {msg2.group(1)}天\n\n'
                except Exception:
                    message2 = "今天已经签到过啦\n\n"
            elif res2.find('签到成功') > -1 or res2.find('已签到') > -1:
                try:
                    msg1 = re.search(r'获得随机奖励\s*\d+\s*金币', res2)
                    msg2 = re.search(r'已累计签到\s*\d+\s*天', res2)
                    message2 = "签到成功\n" + msg1.group() + "\n" + msg2.group() + "\n\n"
                except Exception:
                    message2 = "签到成功\n\n"
            else:
                message2 = f"签到失败!原因: \n{res2}\n\n"
            message3 = get_point_info(cookies)
            msg = message1 + message2 + message3
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
