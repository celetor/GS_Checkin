# -*- coding: utf-8 -*-
# ==============================================================================
# @ Author : Celeter
# @ Link : https://github.com/celetor/GS_Checkin
# @ Date : 2023/10/27
# ==============================================================================
import os
import re
import requests

wx_key = os.environ.get('QYWX_KEY')
# 以下两种登录方式二选一
# cookie登录
Iku_Cookie = os.environ.get('Iku_Cookie')
# 账号密码登录
Iku_mail = os.environ.get('Iku_mail')
Iku_pwd = os.environ.get('Iku_pwd')


class Iku:
    def __init__(self):
        # https://ikuuu.me
        self._host = 'https://ikuuu.one'
        self._session = requests.session()
        self._session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
                          'Chrome/118.0.0.0 Safari/537.36 Edg/118.0.2088.69'
        })
        self.msg = ''

    @staticmethod
    def _format(string: str):
        return re.sub(r'\s+|<[^>]*>', '', string)

    @staticmethod
    def _str2dict(cookie_str: str):
        _dict = {}
        for kv in re.split(r';\s*', cookie_str):
            arr = kv.split('=', 1)
            if len(arr) == 2:
                _dict[arr[0]] = arr[1]
        return _dict

    @staticmethod
    def _dict2str(cookie_dict: dict):
        cookie_list = [f'{k}={v}' for k, v in cookie_dict.items()]
        return '; '.join(cookie_list)

    def send_msg(self):
        print(self.msg)
        if wx_key:
            url = f'https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key={wx_key}'
            json_data = {
                'msgtype': 'text',
                'text': {
                    'content': f'Ikuuu签到详情\n\n{self.msg}',
                }
            }
            headers = {
                'Content-Type': 'application/json'
            }
            rst = requests.post(url, json=json_data, headers=headers).text
            print(rst)

    def login_by_pwd(self, email: str, password: str):
        url = self._host + '/auth/login'
        response = self._session.get(url, allow_redirects=False)
        matcher = re.search(r'跳转到最新域名[:：]\s*(ikuuu[^</]+)', response.content.decode())
        if matcher:
            self._host = f'https://{matcher.group(1)}'
            self.msg += f'域名已更新: {self._host}\n'
            print(f'域名已更新: {self._host}')
            url = self._host + '/auth/login'
        data = {
            'email': email,
            'passwd': password,
            'code': ''
        }
        res = self._session.post(url, data=data, allow_redirects=False).json()
        print(res)
        self.msg += res['msg'] + '\n\n'
        return res['ret']

    def login_by_cookie(self, cookies):
        if isinstance(cookies, str):
            cookies = self._str2dict(cookies)
        self._session.cookies.update(cookies)
        url = self._host + '/user'
        res = self._session.get(url, allow_redirects=False)
        ret = 0 if res.headers.get('Location') else 1
        self.msg += ('登录成功' if ret == 1 else 'cookies失效') + '\n\n'
        return ret

    def get_user_info(self):
        url = self._host + '/user'
        try:
            res = self._session.get(url, allow_redirects=False).text
            duration = self._format(re.search(r'会员时长([\w\W]*?)<li', res).group(1))
            traffic = self._format(re.search(r'剩余流量([\w\W]*?)<li', res).group(1))
            used = self._format(re.search(r'今日已用\s*[:：]([^<]+)', res).group(1))
            o = {
                '会员时长': duration,
                '剩余流量': traffic,
                '今日已用': used
            }
            print(o)
            self.msg += f'会员时长: {duration}\n剩余流量: {traffic}\n今日已用: {used}\n'
        except Exception as e:
            print('/user', e)
            self.msg += f'/user异常: {e}\n'

    def checkin(self):
        url = self._host + '/user/checkin'
        try:
            res = self._session.post(url, allow_redirects=False).json()
            print(res)
            self.msg += res['msg'] + '\n'
            return res['ret']
        except Exception as e:
            print('/user/checkin', e)
            self.msg += f'/user/checkin异常: {e}\n'
            return 0

    def logout(self):
        url = self._host + '/user/logout'
        try:
            res = self._session.get(url, allow_redirects=False)
            ret = 1 if res.headers.get('Location') else 0
            self.msg += '退出成功' if ret == 1 else '退出失败'
            return ret
        except Exception as e:
            print('/user/logout', e)
            self.msg += f'/user/logout异常: {e}\n'


if __name__ == '__main__':
    if Iku_Cookie and len(Iku_Cookie) > 0:
        all_cookies = Iku_Cookie.split('&&')
        for per_cookie in all_cookies:
            obj = Iku()
            try:
                if obj.login_by_cookie(per_cookie):
                    obj.checkin()
                    obj.get_user_info()
            except Exception as e:
                print(e)
                obj.msg += f'异常: {e}'
            obj.send_msg()

    if Iku_mail and Iku_pwd:
        all_mail = Iku_mail.split('&&')
        all_pwd = Iku_pwd.split('&&')
        for i in range(len(all_mail)):
            obj = Iku()
            try:
                if obj.login_by_pwd(all_mail[i], all_pwd[i]):
                    obj.checkin()
                    obj.get_user_info()
                    obj.logout()
            except Exception as e:
                print(e)
                obj.msg += f'\n异常: {e}'
            obj.send_msg()
