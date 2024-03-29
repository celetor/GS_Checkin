# coding=utf-8
import time
import os
import re
import requests
import urllib.parse

# 以下两种登录方式二选一或同时使用
# cookie登录
MT_Cookie = os.environ.get('MT_Cookie')
# 账号密码登录
MT_USER = os.environ.get('MT_USER')
MT_PWD = os.environ.get('MT_PWD')

QYWX_KEY = os.environ.get('QYWX_KEY')

HEADERS = {
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


def retry(times=3, interval=10):
    def decorator(func):
        def wrapper(*args, **kwargs):
            retry_time = 0
            while retry_time < times:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    retry_time += 1
                    print(f'第{retry_time}次重试,{e}')
                    time.sleep(interval)
            return func(*args, **kwargs)

        return wrapper

    return decorator


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
    except Exception as e:
        message = f'{e}'
    return message


def escape(s):
    rep = [{'key': '&lt;', 'val': '<'}, {'key': '&gt;', 'val': '>'}, {'key': '&nbsp;', 'val': ' '},
           {'key': '&amp;', 'val': '&'}, {'key': '&quot;', 'val': '"'}]
    for r in rep:
        s = s.replace(r['key'], r['val'])
    return s


def url_encode(s):
    return urllib.parse.quote(s)


@retry(times=3, interval=15)
def login(ueser, password, cookies):
    session = requests.session()

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1 Edg/110.0.0.0',
    }
    url = 'https://bbs.binmt.cc/forum.php?mod=guide&view=hot&mobile=2'
    session.get(url, headers=headers)

    url = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&mobile=2'
    res = session.get(url)
    text = res.text
    url = 'https://bbs.binmt.cc/' + escape(
        re.search(r'method=["\']post["\']\s+action=["\']([^\'"]+)', text).group(
            1)) + '&handlekey=loginform&inajax=1'
    form_hash = re.search(r'id=["\']formhash["\']\s+value=["\']([^"\']+)', text).group(1)
    referer = re.search(r'id=["\']referer["\']\s+value=["\']([^"\']+)', text).group(1)
    fast_login_field = re.search(r'name=["\']fastloginfield["\']\s+value=["\']([^"\']+)', text).group(1)
    cookie_time = re.search(r'name=["\']cookietime["\']\s+value=["\']([^"\']+)', text).group(1)
    data = {
        'formhash': form_hash,
        'referer': referer,
        'fastloginfield': fast_login_field,
        'cookietime': cookie_time,
        'username': ueser,
        'password': password,
        'questionid': '0',
        'answer': ''
    }
    res = session.post(url, data=data)
    text = res.text
    if text.find('欢迎您回来') > -1:
        # user_info = re.search(r"{'username'[^}]+", text).group()
        # print(user_info)
        url = re.search(r"location\.href\s*=\s*[\"']([^\"']+)", text).group(1)
        headers['referer'] = 'https://bbs.binmt.cc/member.php?mod=logging&action=login&mobile=2'
        session.post(url, headers=headers)
        # cookies = requests.utils.dict_from_cookiejar(session.cookies)
        cookies.update(session.cookies)
        return True
    return False


@retry(times=3, interval=10)
def checkin(mt_cookie):
    cookies = {}
    if isinstance(mt_cookie, str):
        for kv in re.split(r';\s*', mt_cookie):
            arr = kv.split('=', 1)
            if len(arr) == 2:
                cookies[arr[0]] = arr[1]
    else:
        cookies = mt_cookie
    headers = HEADERS.copy()

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
                message2 = f'今天已经签过到啦\n连续签到: {msg1.group(1)}天\n累计签到: {msg2.group(1)}天\n\n'
            except Exception as e:
                message2 = f"今天已经签过到啦 {e}\n\n"
        elif res2.find('已签到') > -1:
            message2 = f'签到成功\n\n'
        else:
            message2 = f"签到失败!原因: \n{res2}\n\n"
        time.sleep(1)
        message3 = get_point_info(cookies)
        msg = message1 + message2 + message3
    else:
        msg = "cookie失效"

    print(msg)
    return msg


if __name__ == '__main__':
    if MT_Cookie and len(MT_Cookie) > 0:
        all_cookies = MT_Cookie.split('&&')
        for per_cookie in all_cookies:
            print('cookies登录')
            checkin(per_cookie)

    if MT_USER and MT_PWD:
        mt_users = MT_USER.split('&&')
        mt_pwd = MT_PWD.split('&&')
        for i in range(len(mt_users)):
            per_cookie = {}
            print('账号密码登录')
            msg_send = '账号密码登录失败，异常未知'
            try:
                is_login = login(mt_users[i], mt_pwd[i], per_cookie)
            except Exception as e:
                is_login = False
                msg_send = f'账号密码登录失败:{e}'
                print(msg_send)

            if is_login:
                try:
                    msg_send = checkin(per_cookie)
                except Exception as e:
                    msg_send = f'签到失败:{e}'
                    print(msg_send)
            wechat('MT论坛签到详情', msg_send)
