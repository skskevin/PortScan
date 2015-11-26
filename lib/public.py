# -*- coding:utf8 -*- #
import smtplib,email,email.MIMEMultipart,email.MIMEBase,email.MIMEText
import email.MIMEImage,base64,sys,re

def sendMail(mailmsg,tomail,title):
    mail_recv=re.split('[,;]',tomail)
    femail=('test@hotmail.com')
    temail =tomail
    msg=email.MIMEMultipart.MIMEMultipart()
    msg['From'] = femail
    msg['To'] = ';'.join(mail_recv)
    msg['Subject'] = title
    msg['Reply-To'] = femail
    body=email.MIMEText.MIMEText(mailmsg,_charset='utf8')
    msg.attach(body)
    smtp = smtplib.SMTP('10.11.11.11','25')
    smtp.login('user', '123456') 
    smtp.sendmail(femail,mail_recv,msg.as_string())
    smtp.close()
    print 'All mail were sended!'
