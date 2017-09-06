#encoding:utf-8

import requests,re
import http.cookiejar as cookielib

from bs4 import BeautifulSoup

agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'
headers = {'User-Agent':agent}
loginUrl = 'http://223.2.193.200/moodle/login/index.php'

#得到session对象
session = requests.session()
session.cookies = cookielib.LWPCookieJar(filename='cookies')

#读取cookie文件
try:
    session.cookies.load(ignore_discard=True)
    print('Cookie加载成功')
except:
    print('Cookie未能加载')

#登陆类
class Login:
    def __init__(self):
        pass

    def getHTMLText(self,url):
        try:
            r = session.get(url,timeout=30,headers=headers)
            r.raise_for_status()
            r.encoding = r.apparent_encoding
            return r.text
        except:
            return None

    def getSoupObj(self,url):
        try:
            html = self.getHTMLText(url)
            soup = BeautifulSoup(html,'html.parser')
            return soup
        except:
            print('\nError: failed to get the Soup object')
            return None

    #验证是否登陆
    def checkLogin(self):
        soup = self.getSoupObj(loginUrl)
        loginInfo = soup('div',{'class':'logininfo'})
        try:
            info = loginInfo[0].text
            print(info)
            if info == '您尚未登录。':
                return False
            else:
                return True
        except:
            print('获取登录信息发生错误')
            return False

    def getSession(self):
        return session

    def login(self):
        user_name = input('请输入登陆名: ')
        password = input('请输入密码: ')

        post_data = {'username':user_name,
                     'password':password
                    }
        post_url = loginUrl

        try:
            login_page = session.post(post_url,headers = headers,data = post_data)
            print('登陆成功!')
            #保存Cookie
            session.cookies.save()
        except:
            print('登陆失败!')   
