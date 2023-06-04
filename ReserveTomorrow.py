from requests import post
from yagmail import SMTP
from json import decoder
from json import loads
from time import sleep
import urllib.request
import urllib.parse
import http.cookiejar
import http.cookies
from threading import Thread
from time import localtime
from requests import Session
from websocket import create_connection
from websocket import WebSocket


def get_code(url):
    query = urllib.parse.urlparse(url).query
    codes = urllib.parse.parse_qs(query).get('code')
    if codes:
        return codes.pop()
    else:
        raise ValueError("未找到授权码！")


def get_cookie_string(code):
    cookiejar = http.cookiejar.MozillaCookieJar()
    opener = urllib.request.build_opener(
        urllib.request.HTTPCookieProcessor(cookiejar))
    response = opener.open(
        "http://wechat.v2.traceint.com/index.php/urlNew/auth.html?" + urllib.parse.urlencode({
            "r": "https://web.traceint.com/web/index.html",
            "code": code,
            "state": 1
        })
    )
    cookie_items = []
    for cookie in cookiejar:
        cookie_items.append(f"{cookie.name}={cookie.value}")
    cookie_string = '; '.join(cookie_items)
    return cookie_string


def KeepCookie(cookie_string, mail, receiver_mail):
    session = Session()
    cookie = http.cookies.SimpleCookie()
    cookie.load(cookie_string)
    for key, morsel in cookie.items():
        session.cookies.set(key, morsel)
    while True:
        if session.cookies.keys().count("Authorization") > 1:
            session.cookies.set("Authorization", domain="", value=None)
        res = session.post("http://wechat.v2.traceint.com/index.php/graphql/", json={
            "query": 'query getUserCancleConfig { userAuth { user { holdValidate: getSchConfig(fields: "hold_validate", extra: true) } } }',
            "variables": {},
            "operationName": "getUserCancleConfig"
        })
        try:
            result = res.json()
        except decoder.JSONDecodeError as err:
            print("Error: %s" % err)
            break
        if result.get("errors") and result.get("errors")[0].get("code") != 0:
            print("Cookie过期！")
            mail.send(receiver_mail, 'Cookie过期！',
                      'Cookie过期，请重新微信扫码并联系作者本人：2251698595')
            exit(0)
        print("Cookie正常！")
        sleep(60)


class DataUsed(object):
    def __init__(self, cookies):
        self.main_url = 'https://wechat.v2.traceint.com/index.php/graphql/'
        self.headers = {
            'Host': 'wechat.v2.traceint.com',
            'Connection': 'keep-alive',
            'Content-Length': '729',
            'Origin': 'https://web.traceint.com',
            'Content-Type': 'application/json',
            'User-Agent': "Mozilla/5.0 (Windows NT 6.1WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6307062c)",
            'App-Version': '2.0.9',
            'Accept': '*/*',
            'Cookie': cookies,
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://web.traceint.com/web/index.html',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }


def HandleCookie(mail, receiver_mail):
    url = input("请输入微信复制的链接：")
    code = get_code(url)
    cookie_string = get_cookie_string(code)
    print("获取Cookie成功！")
    data_used = DataUsed('FROM_TYPE=weixin; v=5.5;'+cookie_string)
    KeepLive = Thread(target=KeepCookie, args=(
        cookie_string, mail, receiver_mail))
    KeepLive.setDaemon(True)
    KeepLive.start()
    print("Cookie保持在线中！")
    sleep(1)
    return data_used, 'FROM_TYPE=weixin; v=5.5;'+cookie_string


def GetMail():
    mail = SMTP('lateyoung111@163.com',
                'DJAFUFGCIMJXXRXU', 'smtp.163.com')
    receiver_mail = input("请输入接受通知邮箱（例：123456@qq.com）：")
    return mail, receiver_mail


def GetInQueue(cookie_string, hour, min):
    headers = ["Pragma: no-cache",
               "Cache-Control: no-cache",
               "User-Agent: Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.138 Safari/537.36 NetType/WIFI MicroMessenger/7.0.20.1781(0x6700143B) WindowsWechat(0x6307001e)",
               f"Cookie: {cookie_string}",
               "Accept-Language: zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
               "Sec-WebSocket-Extensions: permessage-deflate; client_max_window_bits",
               ]
    if int(hour) != 0:
        print("程序进入等待！")
        while True:
            if localtime().tm_hour == int(hour) and localtime().tm_min == int(min):
                print("时间到，正在排队！")
                break
    ws = WebSocket()
    ws.connect("wss://wechat.v2.traceint.com/ws?ns=prereserve/queue",
               header=headers)
    if ws.connected:
        # 接收实时数据，并打印出来
        while True:
            ws.send('{"ns":"prereserve/queue","msg":""}')
            a = ws.recv()
            if a.find('u6392') != -1:  # 排队成功返回的第一个字符
                print("排队结束！")
                break
        # 关闭连接
        ws.close()
    return True


def QueryIndex(data_used, escaped_libs):
    step = 0
    last = 0
    data = {"operationName": "index",
            "query": "query index {\n userAuth {\n user {\n prereserveAuto: getSchConfig(extra: true, fields: \"prereserve.auto\")\n }\n currentUser {\n sch {\n isShowCommon\n }\n }\n prereserve {\n libs {\n is_open\n lib_floor\n lib_group_id\n lib_id\n lib_name\n num\n seats_total\n }\n }\n oftenseat {\n prereserveList {\n id\n info\n lib_id\n seat_key\n status\n }\n }\n }\n}"}
    req = post(data_used.main_url, headers=data_used.headers, json=data)
    try:
        text = loads(req.text)
    except Exception as e:
        print("未知错误，", e)
    libs = text['data']['userAuth']['prereserve']['libs']
    if int(escaped_libs[-1]) != 0:
        for i in escaped_libs:
            if int(i) == last + 1:
                libs.pop(0)
                last += 1
            else:
                libs.pop(int(i) - last - 1)
                last += 1
    while True:
        for lib in libs:
            if lib['num'] != 0:
                print(f"找到{lib['lib_floor']}存在空闲{lib['num']}！")
                step += 1
                return lib['lib_id'], lib['lib_floor']
        if step == 0:
            print("暂时不存在空闲！")
            print("1秒后进行下一次请求！")
            sleep(1)


def LibLayOut(data_used, lib_id, lib_floor):
    data = {"operationName": "libLayout",
            "query": "query libLayout($libId: Int!) {\n userAuth {\n prereserve {\n libLayout(libId: $libId) {\n max_x\n max_y\n seats_booking\n seats_total\n seats_used\n seats {\n key\n name\n seat_status\n status\n type\n x\n y\n }\n }\n }\n }\n}", "variables": {"libId": lib_id}}
    req = post(data_used.main_url, headers=data_used.headers, json=data)
    try:
        text = loads(req.text)
        print(f"获取{lib_floor}座位成功！")
    except Exception as e:
        print("未知错误，", e)
    seats = text['data']['userAuth']['prereserve']['libLayout']['seats']
    keys = []
    for seat in seats:
        if seat['status'] is False and seat['type'] == 1:
            keys.append(seat['key'])
            print("找到空闲座位，", seat['key'])
    return keys


def TomorrowReserve(data_used, keys, lib_id, lib_floor, mail, receiver_mail):
    for key in keys:
        data = {
            "operationName": "save",
            "query": "mutation save($key: String!, $libid: Int!, $captchaCode: String, $captcha: String) {\n userAuth {\n prereserve {\n save(key: $key, libId: $libid, captcha: $captcha, captchaCode: $captchaCode)\n }\n }\n}",
            "variables": {
                "key": f"{key}.",
                "libid": lib_id,
                "captchaCode": "",
                "captcha": ""
            }
        }
        req = post(data_used.main_url, headers=data_used.headers, json=data)
        try:
            text = loads(req.text)
        except Exception as e:
            print("未知错误，", e)
        if text['data']['userAuth']['prereserve']['save'] is True:
            print(f"座位{lib_floor}的{key}预定成功！")
            mail.send(receiver_mail, '预定成功！', f"座位{lib_floor}的{key}预定成功！")
            return True
        else:
            print(f"座位{lib_floor}的{key}预定失败！")
            continue


def main():
    min = 0
    mail, receiver_mail = GetMail()
    hour = input("请输入预约时间（输入0即刻预约，若想在9点准时开始请输入21）：")
    if int(hour) != 0:
        min = input("请输入预约分钟（若想在9点准时开始请输入0）：")
    escaped_libs = input("请输入不想预约的楼层（0为全部预约，输入17代表一楼七楼不预约）：")
    escaped_libs = list(escaped_libs)
    data_used, cookie_string = HandleCookie(mail, receiver_mail)
    queue = GetInQueue(cookie_string, hour, min)
    if not queue:
        print("排队错误！")
        exit(0)
    lib_id, lib_floor = QueryIndex(data_used, escaped_libs)
    keys = LibLayOut(data_used, lib_id, lib_floor)
    TomorrowReserve(data_used, keys, lib_id, lib_floor, mail, receiver_mail)


if __name__ == '__main__':
    print("\n欢迎来到明日预约！\n")
    main()
