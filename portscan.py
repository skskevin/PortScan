# -*- coding:UTF-8 -*- #
#++++++++++++++++++++++++++++++++++++++++++++++++++++
#  Func:Port Scan..
#  By:dongchuan
#  Date:2015/11/18
#++++++++++++++++++++++++++++++++++++++++++++++++++++
import sys,os,time
from ConfigParser import ConfigParser
from libnmap.process import NmapProcess
from libnmap.parser import NmapParser, NmapParserException

BaseDir=os.path.dirname(os.path.abspath(__file__))
LibDir=BaseDir+'/lib'

sys.path.append(LibDir)

from handleMysql import handleMysql
from public import sendMail


#全局变量
CFG_FILE=BaseDir+'/conf/conf.ini'
IP_FILE=BaseDir+'/conf/ip.ini'

CF=ConfigParser()
CF.read(CFG_FILE)

DBHOST=CF.get('DB','dbhost')
DBNAME=CF.get('DB','dbname')
DBUSER=CF.get('DB','dbuser')
DBPWD=CF.get('DB','dbpwd')
DBPORT=CF.get('DB','dbport')

SUBJECT=CF.get('NMAP','subject')
MAIL=CF.get('NMAP','maillist')

SYNC=handleMysql(DBHOST, DBUSER, DBPWD, DBNAME, int(DBPORT),'utf8')

#开始扫描时间
SCAN_TIME=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
#print SCAN_TIME
time.sleep(1)
# start a new nmap scan on localhost with some specific options
def do_scan(targets, options):
    parsed = None
    nmproc = NmapProcess(targets, options)
    rc = nmproc.run()
    if rc != 0:
        print("nmap scan failed: {0}".format(nmproc.stderr))
    #print(nmproc.stdout)

    try:
        parsed = NmapParser.parse(nmproc.stdout)
    except NmapParserException as e:
        print("Exception raised while parsing scan: {0}".format(e.msg))

    return parsed


# print scan results from a nmap report
def saveToDB(nmap_report):
    print("Starting Nmap {0} ( http://nmap.org )".format(nmap_report.version))
    
    for host in nmap_report.hosts:
        hostname=''
        newports=[]
        print("Nmap scan : {0}".format(host.address))
        #print host.address,host.endtime,host.hostnames,host.status
        if len(host.hostnames)>0:
            hostname=host.hostnames[0]
        if host.status=='down':
            print("host:{0} is down!".format(host.address))
            continue
        else:
            print("host:{0} is up!".format(host.address))
        endtime=time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(float(host.endtime)))

        first_scan=isFirstScan(host.address)

        for serv in host.services:
            newports.append(str(serv.port))
            #print str(serv.port),serv.protocol,serv.service
            sql="select id from data_portscan where ip='%s' and port='%s' " %(host.address,str(serv.port))
            rows=SYNC.Select(sql)
          
            if len(rows)>0:
                sql="update data_portscan set hostname='%s',service='%s',last_date='%s' where id=%d " %(hostname,serv.service,endtime,rows[0][0])
                SYNC.DMLSQL(sql)
            else:
                
                if first_scan==False:#IP非首次扫描,且端口新增,则认定为新开端口
                    sql2="insert into data_newport( `ip`, `port`, `service`, `date`) \
                          values('%s','%s','%s','%s')"%(host.address,str(serv.port),serv.service,endtime)
                    SYNC.DMLSQL(sql2)

                sql="insert into data_portscan(`hostname`, `ip`, `port`, `service`, `date`, `last_date`) \
                     values('%s','%s','%s','%s','%s','%s')" % (hostname,host.address,str(serv.port),serv.service,endtime,endtime)
                SYNC.DMLSQL(sql)
        delDownPort(host.address,newports) #删除库中已经关闭的端口

    print(nmap_report.summary) 

def isFirstScan(ip): 
    flag=True #默认首次扫描  
    sql="select count(id) from data_portscan where ip='%s' " % ip 
    rows=SYNC.Select(sql)
    for row in rows:
        if row[0] > 0:
            flag=False
    return flag

def delDownPort(ip,newlist):
    oldlist=[]
    sql="select port from data_portscan where ip='%s'" % ip
    rows=SYNC.Select(sql)
    for row in rows:
        oldlist.append(row[0])
    downPorts=set(oldlist)-set(newlist) #closed ports
    for p in list(downPorts):
        sql2="delete from data_portscan where ip='%s' and port='%s'" %(ip,p)
        SYNC.DMLSQL(sql2)

def notification():
    sql="select ip,port,service from data_newport where date > '%s' order by ip" % SCAN_TIME
    rows=SYNC.Select(sql)
    count = len(rows)
    mailMsg='扫描时间:%s\n'%SCAN_TIME
    mailMsg+='共有%d个端口新增:\n'% count
    mailMsg+='端口列表:\n'
    mailMsg+='{0:<15s}  {1:<6s}  {2}\n'.format('IP','PORT','SERVICE')
    for row in rows:
        mailMsg+='{0:<15s}  {1:<6s}  {2}\n'.format(row[0],row[1],row[2])
    if count > 0:
        sendMail(mailMsg,MAIL,SUBJECT)
    else:
        print("No new ports returned")      

if __name__ == "__main__":
    
    nmap_options=CF.get('NMAP','options')
    with open(IP_FILE) as f:
        for line in f.readlines():
            ip = line.strip()
            report = do_scan(ip, nmap_options)
            if report:
                saveToDB(report) #扫描结果入库
                pass
            else:
                print("No results returned")
        notification() #新增端口报警
    SYNC.Disconnect()
