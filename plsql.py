# -*- coding: utf-8 -*-

defAction = "stdout" ## stdout|mailText|mailHTML|mailFile

import sys
def printV(v) :
  s = str(v).encode("utf8", errors='replace').decode(sys.stdout.encoding)
  print( s )
#

#----------------------------------------------------------------------#

def getData(src) :
  _thisScript_ = sys.argv[0]  ## __file__
  fn = src;  txt = "";
  if (fn is None or len(fn)== 0) : fn = _thisScript_
  with open(fn, 'r') as f:
    if (fn != _thisScript_) : 
      txt = f.read()
      # if (fn == _thisScript_) :
      #   p1 = txt.find('\n#__DATA__')
      #   if (p1 > 0) :
      #     p1 = txt.find('\n', p1+1)
      #     if (p1 > 0) :
      #       p2 = txt.find('\n#__DATA__', p1)
      #       if (p2 < p1) : p2 = len(txt)
      #       txt = txt[p1:p2]
    else :
      # for ln in f.readlines() :
      startData = 0
      while 1 :
        ln = f.readline(); 
        if ( ln == "" ) : break
        if ln.startswith("#__DATA__") :
          startData += 1
        elif ( (startData % 2)==1 ) :
          txt += ln[1:]
        #
      #
      #import os;  fn = os.path.abspath(_thisScript_);
    #
  #
  return [fn, txt];

def parseConnectionString(str) :
  l_str = str
  if l_str.startswith("$") :
    import os
    l_str = os.environ.get(l_str[1:], l_str)
  else :
    import re
    matchObj = re.match( r'(\S+)\/(\S+)@(\S+):(\S+):(\S+)', l_str, re.M|re.I )
    if ( matchObj and len(matchObj.groups())==5 ) :
      l_str = ( matchObj.group(1) + "/" + matchObj.group(2)
              + "@(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host="
              + matchObj.group(3) + ")(Port="
              + matchObj.group(4) + "))(CONNECT_DATA=(SID="
              + matchObj.group(5) + ")))"
              )
    else :
      matchObj = re.match( r'.*Data Source=(.+);User ID=(\S+);Password=(\S+);?', l_str, re.M|re.I )
      #if matchObj : print("\n** " + repr(len(matchObj.groups())) + "\n");
      if ( matchObj and len(matchObj.groups())==3 ) :
        l_str = matchObj.group(2) + "/" + matchObj.group(3) + "@" + matchObj.group(1)
      #
    #
  return l_str;

#print( parseConnectionString("a/b@c:d:e") )
#print( parseConnectionString("$PATH") )
#print( parseConnectionString("Provider=MSDAORA;Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host=mishp05.ap.mot.com)(Port=1521))(CONNECT_DATA=(SID=PADWHI)));User ID=dwh;Password=mfgdm1" ) )
#quit()

def getConnectionString(argv, idx) :
  if (len(argv)>idx) :
    return parseConnectionString(argv[idx])
  else :
    import os
    return os.getenv(
      'ORACLE_ADOCONN', os.getenv("ORACLE_UID", "") + "/" + os.getenv("ORACLE_PWD", "")
        + "@" + os.getenv("ORACLE_SID", "")
      # 'ORACLE_ADOCONN', "Provider=MSDAORA;Data Source=" + os.getenv("ORACLE_SID", "")
      #   + ";User ID=" + os.getenv("ORACLE_UID", "") + ";Password=" + os.getenv("ORACLE_PWD", "")
    )
  #
  return ""
#

#----------------------------------------------------------------------#

def runDbmsOutput(connection_string, plsql):
  plsql = plsql.strip()

  import re 
  if not re.match('^begin\s', plsql, re.M|re.IGNORECASE):
    plsql = "begin " + plsql + " end;"
  #
  print("\n"+plsql+"\n");

  ## python -m pip install --upgrade cx_Oracle ## http://cx-oracle.readthedocs.io/en/latest/installation.html
  import cx_Oracle;  cn = cx_Oracle.connect(connection_string);
  #print(cn.version)

  cur = cn.cursor();  cur.callproc("dbms_output.enable", (None,)) # or explicit integer size

  cur.execute(plsql)
  lineVar = cur.var(cx_Oracle.STRING)
  statusVar = cur.var(cx_Oracle.NUMBER)

  output = ""
  while True:
    cur.callproc("dbms_output.get_line", (lineVar, statusVar))
    if statusVar.getvalue() != 0: break
    # printV( lineVar.getvalue() )
    output = output + lineVar.getvalue() + "\n"
  #

  try   : cur.close(); 
  except: pass;
  cn.close()

  return output.strip()
#

#----------------------------------------------------------------------#

def saveOutput(output, filepath, overwrite):
  with open(filepath, "w", newline="\n") as fout:
    fout.write(output)
  return;
#

#----------------------------------------------------------------------#

def _sendMail(maillist, cclist, msgsubj, msgbody, contentType='plain', files=None):
  import os, os.path
  import smtplib, email.utils
  import email.mime.multipart, email.mime.application, email.mime.text

  msg = email.mime.multipart.MIMEMultipart()
  msg['From'] = os.environ.get('COMPUTERNAME') + "@gmail.com"  ##os.getenv('COMPUTERNAME', "")
  msg['To'] = maillist;  msg['Cc'] = cclist
  msg['Date'] = email.utils.formatdate(localtime=True)
  msg['Subject'] = msgsubj

  bodyContent = email.mime.text.MIMEText(msgbody, 'html') if (contentType=='html') else email.mime.text.MIMEText(msgbody)
  msg.attach( bodyContent )

  for f in files or []:
      with open(f, "rb") as fil:
          part = email.mime.application.MIMEApplication(
              fil.read(),
              Name=os.path.basename(f)
          )
      # After the file is closed
      part['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(f)
      msg.attach(part)
  #

  smtp = smtplib.SMTP("127.0.0.1")
  #smtp.sendmail(msg['From'], msg['To'], msg.as_string())
  smtp.send_message(msg)
  smtp.close()
  print("--sent--\n");
  return;

#----------------------------------------------------------------------#

def sendMail(src, headObj, headTxt, dataTxt, footTxt, contentType='plain', attachment=None) :
  newLine = "<br/>" if (contentType=='html') else "\n"
  import os;  footTxt +=  newLine + newLine + "[source: \\\\" + os.environ.get('COMPUTERNAME') + " \"" + os.path.basename(sys.argv[0]) + "\"]"
  msgbody = headTxt + newLine + newLine + dataTxt + newLine + footTxt

  msgsubj = ""
  if ( len(headObj.get('subject',"")) > 0 ) :
    msgsubj = headObj['subject']
  else :
    msgsubj = src
    p = msgsubj.rfind("\\");
    if (p > 0) : msgsubj = msgsubj[p+1:]
    p = msgsubj.rfind(".");
    if (p > 1) : msgsubj = msgsubj[0:p];
  #

  _sendMail(headObj.get('to'), headObj.get('cc'), msgsubj, msgbody, contentType, attachment);
#

#----------------------------------------------------------------------#

def takeAction(connection_string, plsql, src, headObj, headTxt, footTxt) :

  output = runDbmsOutput(connection_string, plsql)

  actionType = headObj.get('action', defAction)

  if ( actionType=="stdout" ) :

    printV( output )

  else :

    if ( len(output)==0 and headObj.get('sendNoData',False)==False ) :

      print("==output is blank==\n")

    else :

      contentType='plain'; dataTxt=""; attachment=None;

      if len(output)==0 :
        dataTxt = "\n==output is blank==\n"
      elif (actionType=="mailHTML") :
        contentType = 'html'
        dataTxt = "<br><br>" + output + "<br><br>"
      elif (actionType=="mailFile") :
        attachment = src + ".txt";  saveOutput(output, attachment, True)
        attachment = [attachment]
        dataTxt = "" 
      else :
        dataTxt = output
      #

      sendMail(src, headObj, headTxt, dataTxt, footTxt, contentType, attachment)

    #

  #

#

########################################################################

def main(argv) :
  src = ( argv[1] if (len(argv)>1) else "" );  # [ternary operator] value_when_true if condition else value_when_false
  if (src == "/?") :
    print("usage: plsql.py [source [connection_string]]");
    quit();
  #

  if (src=="-") :
    plsql = "".join(sys.stdin.readlines())
  else :
    data = getData(src)
    src = data[0];  plsql = data[1].strip();
  #

  headObj = {};  headTxt = "";  footTxt = "";

  if plsql.startswith("/*"):
    p = plsql.index("*/")
    headTxt = plsql[2:p]
    try :
      import json; headObj=json.loads(headTxt)
      headTxt = ""
    except:
      headObj = {}
    #
    if 'body' in headObj and len(headObj['body'])>0 : headTxt=headObj['body']
    plsql = plsql[p+2:].strip()
  #

  #print(src);
  #print(headTxt);
  #print(headObj.get('x'));
  print("\n"+plsql+"\n");

  connection_string =  parseConnectionString(headObj['connection_string']) if ('connection_string' in headObj) else getConnectionString(argv, 2)
  print(connection_string);  ## quit();

  takeAction(connection_string, plsql, src, headObj, headTxt, footTxt)
#

if __name__ == '__main__':
  main(sys.argv)
#

#__DATA__
# /* {
#   "connection_string": "scott/tiger@127.0.0.1:1521:ORCL"
# } */
#
# dbms_output.put_line('Line# 1: '||sysdate);
#
#__DATA__
#
