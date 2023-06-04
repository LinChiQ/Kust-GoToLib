from requests import post
from requests import Session
from json import loads
from json import decoder
from yagmail import SMTP
from time import sleep
import urllib.request
import urllib.parse
import http.cookiejar
import http.cookies
from threading import Thread
from time import localtime

# 该部分出于GitHub上的GoToLibCookie项目


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
        self.libs_json = {"operationName": "list", "query": "query list {\n userAuth {\n reserve {\n libs(libType: -1) {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n libGroups {\n id\n group_name\n }\n reserve {\n isRecordUser\n }\n }\n record {\n libs {\n lib_id\n lib_floor\n is_open\n lib_name\n lib_type\n lib_group_id\n lib_comment\n lib_color_name\n lib_rt {\n seats_total\n seats_used\n seats_booking\n seats_has\n reserve_ttl\n open_time\n open_time_str\n close_time\n close_time_str\n advance_booking\n }\n }\n }\n rule {\n signRule\n }\n }\n}"}

    def GetFreeLibJson(self, free_lib_id):
        return {"operationName": "libLayout", "query": "query libLayout($libId: Int, $libType: Int) {\n userAuth {\n reserve {\n libs(libType: $libType, libId: $libId) {\n lib_id\n is_open\n lib_floor\n lib_name\n lib_type\n lib_layout {\n seats_total\n seats_booking\n seats_used\n max_x\n max_y\n seats {\n x\n y\n key\n type\n name\n seat_status\n status\n }\n }\n }\n }\n }\n}", "variables": {"libId": free_lib_id}}

    def GetFreeSeatJson(self, free_lib_id, free_seat_key):
        return {"operationName": "reserueSeat", "query": "mutation reserueSeat($libId: Int!, $seatKey: String!, $captchaCode: String, $captcha: String!) {\n userAuth {\n reserve {\n reserueSeat(\n libId: $libId\n seatKey: $seatKey\n captchaCode: $captchaCode\n captcha: $captcha\n )\n }\n }\n}", "variables": {"seatKey": f"{free_seat_key}", "libId": free_lib_id, "captchaCode": "", "captcha": ""}}


def GetLibsData(data_object):
    req = post(data_object.main_url,
               headers=data_object.headers, json=data_object.libs_json)
    try:
        text = loads(req.text)
        print("获得自习信息成功！")
    except Exception as e:
        print("未知错误", e)
        return False
    try:
        return text['data']['userAuth']['reserve']['libs']
    except Exception as e:
        print("请微信重新扫码并重新运行程序！！！")


def FindFreeLib(libs_data, esacpe_seats):
    step = 0
    last = 0
    if int(esacpe_seats[-1]) != 0:
        for i in esacpe_seats:
            if int(i) == last + 1:
                libs_data.pop(0)
                last += 1
            else:
                libs_data.pop(int(i) - last - 1)
                last += 1
    for lib_data in libs_data:
        seats_has = lib_data['lib_rt']['seats_has']
        lib_name = lib_data['lib_name']
        if (seats_has != 0):
            print(f"找到{lib_name}存在{seats_has}个空闲座位！")
            step += 1
            return lib_data['lib_id'], lib_data['lib_name']
    if step == 0:
        print("暂时不存在空闲图书室！")
        return False, step


def GetFreeLibSeats(data_object, free_lib_id, free_lib_name):
    free_lib_json = data_object.GetFreeLibJson(free_lib_id)
    req = post(data_object.main_url,
               headers=data_object.headers, json=free_lib_json)
    req.encoding = 'utf-8'
    try:
        text = loads(req.text)
        print(f"成功获得{free_lib_name}的座位表！")
    except Exception as e:
        print("发生未知错误 ", e)
    free_seats = text['data']['userAuth']['reserve']['libs'][0]['lib_layout']['seats']
    keys = []
    for free_seat in free_seats:
        seat_status = free_seat['seat_status']
        status = free_seat['status']
        if seat_status == 1 and status == False:
            keys.append(free_seat['key'])
            print("找到空闲座位，", free_seat['key'])
    return keys


def ReserveSeat(data_object, free_lib_id, free_seat_keys, free_lib_name, mail, receiver_mail):
    step = 0
    for free_seat_key in free_seat_keys:
        free_seat_json = data_object.GetFreeSeatJson(
            free_lib_id, free_seat_key)
        req = post(data_object.main_url,
                   json=free_seat_json, headers=data_object.headers)
        req.encoding = 'utf-8'
        try:
            text = loads(req.text)
        except Exception as e:
            print("未知错误 ", e)
        if text['data']['userAuth']['reserve']['reserueSeat'] is True:
            print(f"座位{free_seat_key}预定成功！")
            mail.send(receiver_mail, '座位预定成功！',
                      f'{free_lib_name}座位{free_seat_key}预定成功！')
            step += 1
            return True
        else:
            print(f"座位{free_seat_key}预定失败！", text)
            sleep(1)
            continue
    if step == 0:
        return False


def main():
    print("欢迎来到当日捡漏！\n\n")
    mail = SMTP('lateyoung111@163.com',
                'DJAFUFGCIMJXXRXU', 'smtp.163.com')
    url = input("请输入微信复制的链接：")
    receiver_mail = input("请输入接受通知邮箱（例：123456@qq.com）：")
    escaped_seats = input("请输入不想去的楼层（输入0选择所有楼层，输入14代表一楼四楼不选择）：")
    escaped_seats = list(escaped_seats)
    code = get_code(url)
    cookie_string = get_cookie_string(code)
    print("\n获取Cookie成功！\n")
    data_used = DataUsed('FROM_TYPE=weixin; v=5.5;'+cookie_string)
    KeepLive = Thread(target=KeepCookie, args=(
        cookie_string, mail, receiver_mail))
    KeepLive.setDaemon(True)
    KeepLive.start()
    print("\nCookie保持在线中！\n")
    sleep(1)
    hour = int(input("请输入抢座小时（立马开始输入0）："))
    min = int(input("请输入抢座分钟（立马开始输入0）："))
    if hour != 0 and min != 0:
        if localtime().tm_hour < hour:
            print(f"时间已过！现在是{localtime().tm_hour}：{localtime().tm_min}")
        elif localtime().tm_hour == hour and localtime().tm_min > min:
            print(f"时间已过！现在是{localtime().tm_hour}：{localtime().tm_min}")
        else:
            print(f"程序进入等待状态，运行时间为：{hour}：{min}")
            while True:
                if localtime().tm_hour == hour and localtime().tm_min == min:
                    break
    print("程序开始运行！")
    while True:
        libs_data = GetLibsData(data_used)
        free_lib_id, free_lib_name = FindFreeLib(libs_data, escaped_seats)
        if free_lib_id is False:
            print("3秒后执行下一次请求！")
            sleep()
            continue
        free_seat_keys = GetFreeLibSeats(data_used, free_lib_id, free_lib_name)
        success = ReserveSeat(data_used, free_lib_id,
                              free_seat_keys, free_lib_name, mail, receiver_mail)
        if success is True:
            print("程序退出！")
            exit(0)
        else:
            continue


if __name__ == '__main__':
    main()
