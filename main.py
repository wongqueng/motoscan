# -*- coding: utf-8 -*-
import requests
from lxml import etree
from win32com.client import Dispatch
import sys
from PyQt4 import QtCore, QtGui

reload(sys)
sys.setdefaultencoding('utf-8')

SEARCH_URL = "https://btdb.cilimm.com/search/"
ThunderPath="D:\\360soft_install\\Thunder Network\\Thunder\\Program\\ThunderStart.exe"

class Popobox():
    titletype = ""
    title = ""
    moto_link = ""
    filesize = ""
    filecount = ""
    downloadnum = ""
    includedtime = ""
    latestdownload = ""
    filetype = ""

    def __str__(self):
        return '%s;标题=%s;文件大小=%s;文件个数=%s;下载次数=%s;上传时间=%s;filetype=%s' \
               %(self.titletype,
            self.title,
            self.filesize,
            self.filecount,
            self.downloadnum,
            self.includedtime,
            self.filetype
        )
class myqtThread(QtCore.QThread):
    finishSignal = QtCore.pyqtSignal(list)

    def __init__(self, motoscan,bango, parent=None):
        super(myqtThread, self).__init__(parent)
        self.scan=motoscan
        self.bango=bango

    def run(self):
        popos= self.scan.feed(self.bango)
        self.finishSignal.emit(popos)

class MotoScan():

    def __init__(self):
        self.parser = etree.HTMLParser(encoding="utf-8")
        self.thunder = Dispatch('ThunderAgent.Agent64.1')
    def feed(self, bango):
        if (bango == None or bango == ""):
            return
        self.popos = []
        self.count=0
        one_popos=self.getHtmlTrue(SEARCH_URL+bango)
        if(len(one_popos)==0):
            # print "没有找到相关资源"
            return self.popos
        two_popos=self.getHtmlTrue(SEARCH_URL+bango+"/2/0/0")
        self.popos.extend(one_popos)
        self.popos.extend(two_popos)
        return self.popos

    def getHtmlTrue(self,url):
        text = requests.get(url);
        htmlEmt = etree.fromstring(text.text, parser=self.parser)
        # htmlEmt = etree.parse("test.html", parser=self.parser)
        tip = htmlEmt.xpath('//div[@class="content"]/span[@class="red f14"]')
        popos = []
        if (len(tip) > 0):
            # print "没有找到相关资源"
            return popos

        self.count = int(htmlEmt.xpath('//*[@class="orange"]')[0].text)
        # print self.count
        popobox_list = htmlEmt.xpath('//*[@class="popobox"]')

        for popo_elem in popobox_list:
            popo = Popobox()
            title_elem = popo_elem.xpath('child::div[@class="title"]')[0]
            popo.titletype = title_elem.xpath('child::h3/span')[0].text

            title_spans = title_elem.xpath('child::h3/a/span')
            try:
                popo.title = "%s" % (title_elem.xpath('child::h3/a')[0].text)
                for span in title_spans:
                    popo.title = popo.title + "%s%s" % (span.text, span.tail)
            except:
                pass
            if (popo.title is None or popo.title == ""):
                popo.title = "%s%s" % (title_elem.xpath('child::h3/a')[0].text)
            popo.title = popo.title.replace("None", "")
            sort_bar = popo_elem.xpath('child::div[@class="sort_bar"]')[0]
            popo.moto_link = sort_bar.xpath('child::span[1]/a')[0].get("href")
            popo.filesize = sort_bar.xpath('child::span[2]/b')[0].text
            popo.filecount = sort_bar.xpath('child::span[3]/b')[0].text
            popo.downloadnum = sort_bar.xpath('child::span[4]/b')[0].text
            popo.includedtime = sort_bar.xpath('child::span[5]/b')[0].text
            popo.latestdownload = sort_bar.xpath('child::span[6]/b')[0].text
            try:
                type_elem = popo_elem.xpath('child::div[@class="slist"]/ul[1]/li[1]/span[last()-1]')
                tail = type_elem[0].tail
                popo.filetype = tail[tail.index(r'.'):]
            except:
                pass
            # print popo
            popos.append(popo)
        return popos

    def download(self,filename,motolink):
        self.thunder.AddTask(motolink, filename)
        self.thunder.CommitTasks()
class HelloPyQt(QtGui.QWidget):
    def __init__(self,  parent=None):
        super(HelloPyQt, self).__init__(parent)
        self.setWindowTitle(u"种子搜索器")
        self.scan = MotoScan()
        self.btnPress = QtGui.QPushButton(u"搜索")
        self.list = QtGui.QListWidget()
        self.list.itemDoubleClicked.connect(self.item_double_clcik)
        self.layout = QtGui.QVBoxLayout()
        self.scan_bar=QtGui.QHBoxLayout()
        self.edit=QtGui.QLineEdit(parent=self)
        self.scan_bar.addWidget(self.edit)
        self.scan_bar.addWidget(self.btnPress)
        self.layout.addLayout(self.scan_bar)
        self.layout.addWidget(self.list)
        self.setLayout(self.layout)
        self.btnPress.clicked.connect(self.btnPress_Clicked)

    def btnPress_Clicked(self):
        bango=self.edit.text()
        if(bango == ""):
            msgBox = QtGui.QMessageBox()
            msgBox.setWindowTitle(u'提示')
            msgBox.setText(u"\n请输入搜索信息")
            msgBox.setWindowIcon(QtGui.QIcon(r':/0102.png'))
            msgBox.exec_()
            return
        self.mythread = myqtThread(self.scan,bango)
        self.mythread.finishSignal.connect(self.updateList)
        self.mythread.start()

    def updateList(self,popos):
        self.popos=popos
        if (len(self.popos) > 0):
            self.list.clear()

            self.titles = []
            for popo in self.popos:
                self.titles.append(unicode(str(popo).decode("utf-8")))
            self.list.addItems(self.titles)
    def item_double_clcik(self, item):
        popo=self.popos[self.list.row(item)]
        self.scan.download(popo.title+popo.filetype,popo.moto_link)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWindow = HelloPyQt()
    mainWindow.setMinimumSize(720, 480)
    mainWindow.show()
    sys.exit(app.exec_())
