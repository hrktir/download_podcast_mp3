import urllib2
from xml.dom.minidom import parse
from time import strptime
from datetime import datetime
from datetime import timedelta
import time
import re
import os
import sys


# The following url is feed format and can not be accepted. 
# url = "http://www.bbc.co.uk/worldservice/learningenglish/general/sixminute/index.xml"
# The following url is rss format and can be accepted.
# url = "http://downloads.bbc.co.uk/podcasts/worldservice/how2/rss.xml"

def getPodcastXmlDom(url):
    response = urllib2.urlopen(url)
    #msg = response.read()
    dom1 = parse(response)
    return dom1

def getItemList(dom):
    items = dom.getElementsByTagName('item')
    if len(items) > 0:
        return parseItemsAsRSS(items)
    else:
        raise Exception("no item element found")

def parseItemsAsRSS(items):
    results = []
    for item in items:
        idict = dict()

        enc = item.getElementsByTagName('enclosure')
        if len(enc) == 1:
            idict["url"] = enc[0].getAttribute("url")

        idate = item.getElementsByTagName('pubDate')
        if len(idate) == 1:
            idict["date"] = getGMTDatetime(idate[0].firstChild.wholeText)

        ititle = item.getElementsByTagName('title')
        if len(ititle) == 1:
            idict["title"] = ititle[0].firstChild.wholeText

        if idict.has_key("url") and idict.has_key("date") and idict.has_key("title"):
            results.append(idict)
    return results

def getGMTDatetime(idateStr):
    tlag = 0
    if re.search("[\+\-][0-9]{4}",idateStr):
        tlag = int( re.findall("[\+\-][0-9]{4}", idateStr)[0] ) / 100     
        idateStr = re.sub("[\+\-][0-9]{4}", "GMT", idateStr)
    for s, v in {
       "ADT":-3,
       "AST":-4,
       "EDT":-4,
       "EST":-5,
       "PDT":-7,
       "PST":-8,
       "JST":9
    }.iteritems():
        if re.search(s, idateStr):
            tlag = v
            idateStr = re.sub(s, "GMT", idateStr)
    try:
        idateValue = strptime(idateStr, "%a, %d %b %Y %H:%M:%S %Z")
    except:
        idateValue = strptime(idateStr, "%a, %d %b %Y %H:%M %Z")
    idate = datetime(idateValue.tm_year,idateValue.tm_mon, idateValue.tm_mday, idateValue.tm_hour, idateValue.tm_min, idateValue.tm_sec)
    idate = idate - timedelta(hours = tlag)
    return idate
 
def getFilename4mp3(idict):
    ret = ""
    if idict.has_key("prefix"):
        ret = ret + idict["prefix"]
    ret = ret + re.sub("[^a-zA-Z0-9]", "_", idict["title"])
    ret = ret + "_"
    ret = ret + idict["date"].strftime("%Y_%m_%d_%H_%M")
    ret = ret + ".mp3"
    return ret

def downloadFile(url, filename):
    print "download " + url + " as " + filename
    response = urllib2.urlopen(url)
    tofile = open(filename,"w")
    tofile.write(response.read())        
    response.close()
    tofile.close()

def changeAccessTime(filename, pubdate):
    t = int(time.mktime(pubdate.timetuple()))
    os.utime(filename, (t,t))

def getLatestItem(items, nhoursago):
    tdy = datetime.today()
# make t as GMT 
    t = datetime(tdy.year, tdy.month, tdy.day, tdy.hour, tdy.minute)
# assume this environment is in JST (+0900)
    t = t - timedelta(seconds = 9 * 3600)

    ndaysago = int(nhoursago / 24)
    nsecsago = (nhoursago - 24.0 * ndaysago) * 3600
    
    results = filter(lambda i:i["date"] > t - timedelta(days = ndaysago, seconds = nsecsago) ,items)
    return results

def main():
    if len(sys.argv) < 2:
        print "Usage:" + sys.argv[0] + " url_of_podcast_rss [options]"
        print """Options:
    --since n      : gets mp3s newer than n hours ago. 
                     default is 148 (24hours * 7days) 
    --title TITLE  : uses TITLE as filename
    --prefix PREFIX  : add prefix to the filename
"""
        sys.exit()
    url = sys.argv[1]
    nhoursago = 7 * 24
    alttitle = None
    prefix = None
    for i in range(2, len(sys.argv)):
        if sys.argv[i] == "--since" and i + 1 < len(sys.argv):
            nhoursago = int(sys.argv[i + 1])
        if sys.argv[i] == "--title" and i + 1 < len(sys.argv):
            alttitle = sys.argv[i + 1]
        if sys.argv[i] == "--prefix" and i + 1 < len(sys.argv):
            prefix = sys.argv[i + 1]

#    items = getItemList(getPodcastXmlDom(url))
    items = getLatestItem(getItemList(getPodcastXmlDom(url)),nhoursago)
    for item in items:
        if alttitle:
            item["title"] = alttitle
        if prefix:
            item["prefix"] = prefix
        downloadFile(item["url"], getFilename4mp3(item))
        changeAccessTime(getFilename4mp3(item), item["date"])

def testGetGMTDatetime():
    print getGMTDatetime("Sun, 22 Jan 2012 13:00:01 +0000")
    print getGMTDatetime("Thu, 27 Jan 2012 22:48:45 PDT")
    print getGMTDatetime("Thu, 26 Jan 2012 08:44:15 -0800")
    print getGMTDatetime("Fri, 27 Jan 2012 03:30:33 EST")

if __name__ == '__main__':
#    testGetGMTDatetime()
    main()

