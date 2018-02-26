#encoding:utf-8

import requests,re,os
from bs4 import BeautifulSoup
from Login import *

BASELOC = os.getcwd()
# 根目录名
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
        self.main()

    #得到用户输入的序号，输入范围为0 <= n < k
    def getSelectNo(self, k):
        n = 0
        while True:
            n = input('请输入要下载的课程序号：')
            if n.isdigit() and int(n) >= 0 and int(n) < k:
                break
            else:
                print('输入不合法，请重新输入！')
                continue
        return int(n)

    #得到用户选择的课程名
    def getSelectCourse(self, courseDict):
        courseList = list(courseDict.keys())
        courseList.append('退出')

        k = 0
        print('------课程信息------')
        for i in courseList:
            print ("%-3d:%-10s"%(k,i))
            k += 1

        n = self.getSelectNo(k)
        return courseList[n]

    #得到用户选择的章节名
    def getSelectChapter(self, chapterDict):
        chapterList = list(chapterDict.keys())
        chapterList.insert(0,'所有章节')
        chapterList.append('退出')

        k = 0
        print('------章节信息------')
        for i in chapterList:
            print ("%-3d:%-10s"%(k,i))
            k += 1

        n = self.getSelectNo(k)
        return chapterList[n]

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
                print('建立子目录: ' + name)
            else:
                print('进入子目录: ' + name)
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

    #处理内容
    def parserData(self,chapterName,chapterDict, courseLoc):
        if chapterName == '所有章节':
            #处理章节
            for name,soup in chapterDict.items():
                os.chdir(courseLoc)

                chapterLoc = courseLoc + '\\' + name
                if not os.path.exists(chapterLoc):
                    os.mkdir(name)
                    print('建立章节: ' + name)
                else:
                    print('进入章节: ' + name)
                os.chdir(chapterLoc)

                #得到文件链接列表
                resourcesHrefs = soup('a',{'href':re.compile(r'/resource|/content')})
                    
                #得到文件夹链接列表
                folderHrefs = soup('a',{'href':re.compile(r'/folder')})

                if not len(resourcesHrefs) == 0 :
                    self.geResources(resourcesHrefs)
                if not len(folderHrefs) == 0 :
                    self.getFolderContents(folderHrefs)
        else :
            os.chdir(courseLoc)

            chapterLoc = courseLoc + '\\' + chapterName
            if not os.path.exists(chapterLoc):
                os.mkdir(chapterName)
                print('建立章节: ' + chapterName)
            else:
                print('进入章节: ' + chapterName)
            os.chdir(chapterLoc)

            soup = chapterDict.get(chapterName, None)
            if soup is not None:
                #得到文件链接列表
                resourcesHrefs = soup('a',{'href':re.compile(r'/resource|/content')})
                    
                #得到文件夹链接列表
                folderHrefs = soup('a',{'href':re.compile(r'/folder')})

                if not len(resourcesHrefs) == 0 :
                    self.geResources(resourcesHrefs)
                if not len(folderHrefs) == 0 :
                    self.getFolderContents(folderHrefs)
            else:
                print('获取内容错误')

    #主方法
    def main(self):
        #跳转至root目录
        if not os.path.exists(ROOTLOC):
            os.mkdir(NAME)
            print('建立根目录: ' + NAME)
        else:
            print('进入根目录：' + NAME)
        
        dict = self.getCourse()

        #处理课程
        while True:
            os.chdir(ROOTLOC)
            courseName = self.getSelectCourse(dict)
            if courseName == '退出':
                break
            courseLoc = ROOTLOC + '\\' + courseName
            if not os.path.exists(courseLoc):
                os.mkdir(courseName)
                print('创建课程: ' + courseName)
            else:
                print('进入课程: ' + courseName)
            os.chdir(courseLoc)

            #处理章节
            chapterDict = self.getChapters(dict[courseName])
            while True:
                chapterName = self.getSelectChapter(chapterDict)
                if chapterName == '退出':
                    break
                self.parserData(chapterName, chapterDict, courseLoc)
