#encoding:utf-8

import requests,re,os
from bs4 import BeautifulSoup
from Login import *

BASELOC = os.getcwd()
NAME = 'Resources'
ROOTLOC = BASELOC + '\\' + NAME

agent = 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.81 Safari/537.36'
headers = {'User-Agent':agent}

def getHTMLText(url,session):
    try:
        r = session.get(url,headers=headers)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except:
        return None

def getSoupObj(url,session):
    try:
        html = getHTMLText(url,session)
        soup = BeautifulSoup(html,'html.parser')
        return soup
    except:
        return None

#获取信息类
class GetContent:
    def __init__(self):
        #验证登陆
        lg = Login()
        while(lg.checkLogin() == False):
            lg.login()
        session = lg.getSession()
        self.parserData(session)

    #返回课程字典
    def getCourse(self,session):
        dict = {}
        soup = getSoupObj('http://223.2.193.200/moodle/my/',session)
        if soup != None:
            regionContent = soup('div',{'class':'region-content'})[0]
            hrefs = regionContent('a',{'class':'','href':re.compile(r'course')})
            dict = {}
            for i in hrefs:
                dict[i.text] = i['href']
        return dict

    #获取文件资源
    def geResources(self,hrefs,session):  
        #链接字典
        urlsDict = {}

        #遍历所有文件
        for i in hrefs:
            #这里的链接并非文件真实下载链接，真实下载链接存在于get请求的响应头中
            headers = session.head(i['href']).headers
            headerDict = dict(headers)

            #如果响应头中存在链接，则直接保存
            if 'Location' in headerDict:
                suffix = headerDict['Location'].split('.')[-1]
                name = i.text + '.' + suffix
                urlsDict[name] = (headerDict['Location'])

            #如果响应头中不存在链接，则链接存在于html中
            else:
                contentSoup = getSoupObj(i['href'],session)
                if contentSoup is not None :
                    resourceworkarounds = contentSoup('div',{'class':'resourceworkaround'})
                    for j in resourceworkarounds:
                        try:
                            tmpUrls = j.find_all('a')
                            for k in tmpUrls:
                                suffix = k['href'].split('.')[-1]
                                name = i.text + '.' + suffix
                                urlsDict[name] = (k['href'])
                        except:
                            pass

        #下载文件
        for name,url in urlsDict.items():
            r = session.get(url)
            print('下载文件：',name)
            with open(name, "wb") as code:
                 code.write(r.content)

    #获取文件夹资源
    def getFolderContents(self,hrefs,session):
        courseLoc = os.getcwd()

        #遍历所有文件夹
        for i in hrefs:
            urlsDict = {}
            name = i.text.split(' ')[0]
            url = i['href']

            #建立子文件夹，注意每个文件夹爬完后要回退到上级目录
            os.chdir(courseLoc)
            folderLoc = courseLoc + '\\' + name
            if not os.path.exists(folderLoc):
                os.mkdir(name)
                print('建立子文件夹: ' + name)
            os.chdir(folderLoc)

            contentSoup = getSoupObj(url,session)
            regionContent = contentSoup('div',{'class':'region-content'})[0]
            contentsHrefs = regionContent('a',{'class':'','href':re.compile(r'content')})

            #保存文件字典
            for j in contentsHrefs:
                urlsDict[j.text] = j['href']

            #下载文件
            for name,url in urlsDict.items():
                r = session.get(url)
                print('下载文件：',name)
                with open(name, "wb") as code:
                     code.write(r.content)

    #处理主方法
    def parserData(self,session):
        #跳转至root目录
        if not os.path.exists(ROOTLOC):
            os.mkdir(NAME)
            print('建立根文件夹: ' + NAME)
        
        dict = self.getCourse(session)
        for name,url in dict.items() :
            os.chdir(ROOTLOC)
            courseLoc = ROOTLOC + '\\' + name
            if not os.path.exists(courseLoc):
                os.mkdir(name)
                print('建立课程文件夹: ' + name)
            os.chdir(courseLoc)

            soup = getSoupObj(url,session)
            regionContent = soup('div',{'class':'region-content'})[0]

            #得到文件链接列表
            resourcesHrefs = regionContent('a',{'class':'','href':re.compile(r'resource')})

            #得到文件夹链接列表
            folderHrefs = regionContent('a',{'class':'','href':re.compile(r'folder')})

            self.geResources(resourcesHrefs,session)
            self.getFolderContents(folderHrefs,session)
