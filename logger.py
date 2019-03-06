import os
import datetime

class Logger():

    def __init__(self):
        self.path = "./"
        self.fn = "logger.log"
        p = self.path + self.fn
        self.f = open(p, 'a')
        if not os.path.isfile(p):
            print "Error: log file not found"
            exit(0)
            
        self.fn_deleted = "deleted.log"
        p = self.path + self.fn_deleted
        self.f_deleted = open(p, 'a')
        if not os.path.isfile(p):
            print "Error: log file not found"
            exit(0)

        self.fn_synched = "synchronized.log"
        p = self.path + self.fn_synched
        self.f_synched = open(p, 'a')
        if not os.path.isfile(p):
            print "Error: log file not found"
            exit(0)

        self.fn_err = "error.log"
        p = self.path + self.fn_err
        self.f_err = open(p, 'a')
        if not os.path.isfile(p):
            print "Error: log file not found"
            exit(0)

        ts = datetime.datetime.now()

        self.f.write("Logger started @" + str(ts)+'\n')
        self.f_deleted.write("Logger started @" + str(ts)+'\n')
        self.f_synched.write("Logger started @" + str(ts)+'\n')
        self.f_err.write("Logger started @" + str(ts)+'\n')

    def log(self, line):
        self.f.write(line+'\n')
        self.f.flush()

    def logerror(self, line):
        ts = datetime.datetime.now()
        self.f_err.write(str(ts)+'\n'+line+'\n')
        self.f_err.flush()

    def logdeleted(self, fn_list):
        ts = datetime.datetime.now()
        self.f_deleted.write(str(ts)+'\n')
        for fn in fn_list: 
            self.f_deleted.write(fn+'\n')
        self.f_deleted.flush()

    def logsynched(self, fn_list):
        ts = datetime.datetime.now()
        self.f_synched.write(str(ts)+'\n')
        for fn in fn_list: 
            self.f_synched.write(fn+'\n')
        self.f_synched.flush()

    def send_sms_via_email(self, msg):
    
        import smtplib
        from email.mime.text import MIMEText
        msg = MIMEText(msg) #fp.read())
        me = 'apashnin@cern.ch'
        you = '41754111323@mail2sms.cern.ch'
        msg['Subject'] = 'Error!'
        msg['From'] = me
        msg['To'] = you
        
        s = smtplib.SMTP('cernmx.cern.ch:25')
        s.sendmail(me, [you], msg.as_string())
        print 'sent'
        s.quit()



