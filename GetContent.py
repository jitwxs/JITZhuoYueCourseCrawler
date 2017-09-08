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
    session = None
    def __init__(self):
        #验证登陆
        lg = Login()
        while(lg.checkLogin() == False):
            lg.login()
        self.session = lg.getSession()
        self.parserData()

    #返回课程字典 K:课程名 V:课程url
    def getCourse(self):
        dict = {}
        soup = getSoupObj('http://223.2.193.200/moodle/my/',self.session)
        if soup != None:
            regionContent = soup('div',{'class':'region-content'})[0]
            hrefs = regionContent('a',{'class':'','href':re.compile(r'course')})
            dict = {}
            for i in hrefs:
                dict[i.text] = i['href']
        return dict

    #返回章节字典 K:章节名 V:对应Soup
    def getChapters(self,url):
        dict = {}
        soup = getSoupObj(url,self.session)
        regionContent = soup('div',{'class':'region-content'})[0]
        chapterSoup = regionContent('li',{'id':re.compile(r'section')})
        for i in chapterSoup:
            #如果出现except,代表该章节不可用，直接pass即可
            try:
                chapterName = i['aria-label']
                dict[chapterName] = i
            except:
                pass
        return dict

    #获取文件资源：包含content文件和resource文件
    def geResources(self,hrefs):  
        #链接字典
        urlsDict = {}

        #遍历所有文件
        for i in hrefs:
            #如果为content文件，无需处理
            if re.search( r'/content', i['href'], re.M|re.I):
                urlsDict[i.text] = i['href']

            #如果为resource文件，需要处理
            elif re.search( r'/resource', i['href'], re.M|re.I):
                #这里的链接并非文件真实下载链接，真实下载链接存在于get请求的响应头中
                headers = self.session.head(i['href']).headers
                headerDict = dict(headers)

                #如果响应头中存在链接，则直接保存
                if 'Location' in headerDict:
                    suffix = headerDict['Location'].split('?')[0].split('.')[-1]
                    name = i.text + '.' + suffix
                    urlsDict[name] = (headerDict['Location'])

                #如果响应头中不存在链接，则链接存在于html中
                else:
                    contentSoup = getSoupObj(i['href'],self.session)
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
            if os.path.exists(name):
                print(name,'文件已存在，跳过下载')
            else:
                print('下载文件：',name)
                r = session.get(url)
                with open(name, "wb") as code:
                     code.write(r.content)

    #获取文件夹资源
    def getFolderContents(self,hrefs):
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

            contentSoup = getSoupObj(url,self.session)
            regionContent = contentSoup('div',{'class':'region-content'})[0]
            contentsHrefs = regionContent('a',{'class':'','href':re.compile(r'content')})

            #保存文件字典
            for j in contentsHrefs:
                urlsDict[j.text] = j['href']

            #下载文件
            for name,url in urlsDict.items():
                if os.path.exists(name):
                    print(name,'文件已存在，跳过下载')
                else:
                    print('下载文件：',name)
                    r = session.get(url)
                    with open(name, "wb") as code:
                         code.write(r.content)

    #处理主方法
    def parserData(self):
        #跳转至root目录
        if not os.path.exists(ROOTLOC):
            os.mkdir(NAME)
            print('建立根文件夹: ' + NAME)
        
        dict = self.getCourse()

        #处理课程
        for name,url in dict.items() :

            os.chdir(ROOTLOC)
            courseLoc = ROOTLOC + '\\' + name
            if not os.path.exists(courseLoc):
                os.mkdir(name)
                print('建立课程文件夹: ' + name)
            os.chdir(courseLoc)

            chapterDict = self.getChapters(url)

            #处理章节
            for name,soup in chapterDict.items():

                os.chdir(courseLoc)
                chapterLoc = courseLoc + '\\' + name
                if not os.path.exists(chapterLoc):
                    os.mkdir(name)
                    print('建立章节文件夹: ' + name)
                os.chdir(chapterLoc)

                #得到文件链接列表
                resourcesHrefs = soup('a',{'href':re.compile(r'/resource|/content')})
                
                #得到文件夹链接列表
                folderHrefs = soup('a',{'href':re.compile(r'/folder')})

                if not len(resourcesHrefs) == 0 :
                    self.geResources(resourcesHrefs)
                if not len(folderHrefs) == 0 :
                    self.getFolderContents(folderHrefs)
