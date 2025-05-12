# -*- coding: UTF-8 -*-
import random
from time import time, localtime
import requests
import cityinfo
from requests import get, post
from datetime import datetime, date
from zhdate import ZhDate
import sys
import os
USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"

# 在程序开始时生成随机颜色列表
COLOR_LIST = ["#" + "%06x" % random.randint(0, 0xFFFFFF) for _ in range(100)]

def get_color():
    # 从预生成的颜色列表中随机选择一个颜色
    return random.choice(COLOR_LIST)

def get_access_token():
    # appId
    app_id = config["app_id"]
    # appSecret
    app_secret = config["app_secret"]
    post_url = ("https://api.weixin.qq.com/cgi-bin/token?grant_type=client_credential&appid={}&secret={}"
                .format(app_id, app_secret))
    try:
        access_token = get(post_url).json()['access_token']
    except KeyError:
        print("获取access_token失败，请检查app_id和app_secret是否正确")
        os.system("pause")
        sys.exit(1)
    # print(access_token)
    return access_token


def get_weather(province, city):
    # 城市id
    try:
        city_id = cityinfo.cityInfo[province][city]["AREAID"]
    except KeyError:
        print("推送消息失败，请检查省份或城市是否正确")
        os.system("pause")
        sys.exit(1)
    # city_id = 101280101
    # 毫秒级时间戳
    t = int(time() * 1000)
    headers = {
        "Referer": f"http://www.weather.com.cn/weather1d/{city_id}.shtml",
        "User-Agent": USER_AGENT
    }#统一使用 f-string 可使代码更简洁、易读且高效，是 Python 3.6+ 项目的推荐实践
    url = "http://d1.weather.com.cn/dingzhi/{}.html?_={}".format(city_id, t)
    response = get(url, headers=headers)
    response.encoding = "utf-8"
    response_data = response.text.split(";")[0].split("=")[-1]
    response_json = eval(response_data)
    # print(response_json)
    weatherinfo = response_json["weatherinfo"]
    # 天气
    weather = weatherinfo["weather"]
    # 最高气温
    temp = weatherinfo["temp"]
    # 最低气温
    tempn = weatherinfo["tempn"]
    return weather, temp, tempn


'''
def get_birthday(birthday, year, today):
    birthday_year = birthday.split("-")[0]
    # 判断是否为农历生日
    if birthday_year[0] == "r":
        r_mouth = int(birthday.split("-")[1])
        r_day = int(birthday.split("-")[2])
        # 今年生日
        birthday = ZhDate(year, r_mouth, r_day).to_datetime().date()
        year_date = birthday


    else:
        # 获取国历生日的今年对应月和日
        birthday_month = int(birthday.split("-")[1])
        birthday_day = int(birthday.split("-")[2])
        # 今年生日
        year_date = date(year, birthday_month, birthday_day)
    # 计算生日年份，如果还没过，按当年减，如果过了需要+1
    if today > year_date:
        if birthday_year[0] == "r":
            # 获取农历明年生日的月和日
            r_last_birthday = ZhDate((year + 1), r_mouth, r_day).to_datetime().date()
            birth_date = date((year + 1), r_last_birthday.month, r_last_birthday.day)
        else:
            birth_date = date((year + 1), birthday_month, birthday_day)
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    elif today == year_date:
        birth_day = 0
    else:
        birth_date = year_date
        birth_day = str(birth_date.__sub__(today)).split(" ")[0]
    return birth_day
'''

def get_birthday(birthday: str, year: int, today: date) -> int:
    parts = birthday.split('-')
    is_lunar = parts[0].startswith('r')
    
    if is_lunar:
        #农历处理
        r_month = int(parts[1])
        r_day = int(parts[2])
        current_year_date = ZhDate(year, r_month, r_day).to_datetime().date()
    else:
        # 公历处理
        month_day = parts[-2:]  # 取最后两个部分作为月和日
        month, day = map(int, month_day)
        current_year_date = date(year, month, day)
    
    if today > current_year_date:
        # 计算下一年的生日
        if is_lunar:
            next_year_date = ZhDate(year + 1, r_month, r_day).to_datetime().date()
        else:
            # 处理公历闰年2月29日情况
            try:
                next_year_date = date(year + 1, month, day)
            except ValueError:
                next_year_date = date(year + 1, month, day - 1)  # 简化为前一天，可根据需求调整
        birth_date = next_year_date
    elif today == current_year_date:
        return 0
    else:
        birth_date = current_year_date
    
    return (birth_date - today).days


def get_ciba():
    url = "https://open.iciba.com/dsapi/"
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    response = requests.get(url, headers=headers)
    data = response.json()

    note_en = data["content"]
    note_ch = data["note"]

    if len(note_en) > 40:
        note_en2 = note_en[40:]
        note_en = note_en[:40]
        
    else:
        note_en2 = ""

    if len(note_ch) > 20:
        note_ch2 = note_ch[20:]
        note_ch = note_ch[:20]
    else:
        note_ch2 = ""

    return note_ch, note_ch2, note_en, note_en2


def send_message(to_user, access_token, city_name, weather, max_temperature, min_temperature, note_ch, note_ch2, note_en, note_en2):
    url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
    weekdays_cn = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    year = localtime().tm_year
    today = date.today()
    week = weekdays_cn[today.weekday()]
    # 获取在一起的日子的日期格式
    try:
        love_date = datetime.strptime(config["love_date"], "%Y-%m-%d").date()
    except ValueError:
        # 处理非法日期格式
        raise ValueError("Invalid date format, expected YYYY-MM-DD")
    love_days = (today - love_date).days
    # 获取所有生日数据
    birthdays = {}
    for k, v in config.items():
        if k[0:5] == "birth":
            birthdays[k] = v
    data = {
        "touser": to_user,
        "template_id": config["template_id"],
        "url": "http://weixin.qq.com/download",
        "topcolor": "#FF0000",
        "data": {
            "date": {
                "value": "{} {}".format(today, week),
                "color": get_color()
            },
            "city": {
                "value": city_name,
                "color": get_color()
            },
            "weather": {
                "value": weather,
                "color": get_color()
            },
            "min_temperature": {
                "value": min_temperature,
                "color": get_color()
            },
            "max_temperature": {
                "value": max_temperature,
                "color": get_color()
            },
            "love_day": {
                "value": love_days,
                "color": get_color()
            },
            "note_en": {
                "value": note_en,
                "color": get_color()
            },
            "note_en2": {
                "value": note_en2,
                "color": get_color()
            },
            "note_ch": {
                "value": note_ch,
                "color": get_color()
            },
            "note_ch2": {
                "value": note_ch2,
                "color": get_color()
            }
        }
    }

    for key, value in birthdays.items():
        # 获取距离下次生日的时间
        birth_day = get_birthday(value["birthday"], year, today)
        if birth_day == 0:
            birthday_data = "今天{}生日哦，祝{}生日快乐！".format(value["name"], value["name"])
        else:
            birthday_data = "距离{}的生日还有{}天".format(value["name"], birth_day)
        # 将生日数据插入data
        data["data"][key] = {"value": birthday_data, "color": get_color()}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT
    }
    response = post(url, headers=headers, json=data).json()
    if response["errcode"] == 40037:
        print("推送消息失败，请检查模板id是否正确")
    elif response["errcode"] == 40036:
        print("推送消息失败，请检查模板id是否为空")
    elif response["errcode"] == 40003:
        print("推送消息失败，请检查微信号是否正确")
    elif response["errcode"] == 0:
        print("推送消息成功")
    else:
        print(response)


if __name__ == "__main__":
    try:
        with open("config.txt", encoding="utf-8") as f:
            config = eval(f.read())
    except FileNotFoundError:
        print("推送消息失败，请检查config.txt文件是否与程序位于同一路径")
        os.system("pause")
        sys.exit(1)
    except SyntaxError:
        print("推送消息失败，请检查配置文件格式是否正确")
        os.system("pause")
        sys.exit(1)

    # 获取accessToken
    accessToken = get_access_token()
    # 接收的用户
    users = config["user"]
    # 传入省份和市获取天气信息
    province, city = config["province"], config["city"]
    weather, max_temperature, min_temperature = get_weather(province, city)
    # 获取词霸每日金句
    note_ch, note_ch2, note_en, note_en2 = get_ciba()
    # 公众号推送消息
    for user in users:
        send_message(user, accessToken, city, weather, max_temperature, min_temperature, note_ch, note_ch2, note_en, note_en2)
