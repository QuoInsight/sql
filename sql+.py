# -*- coding: utf-8 -*-

defAction = "mailFile" ## stdout|mailText|mailHTML|mailFile|updateGoogleSheets|mailGoogleSheets
defTarget = "https://docs.google.com/spreadsheets/d/fileId/edit#gid=0"
defOption = "REFRESH" ## REFRESH|OVERWRITE|INSERT_ROWS

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
#print( parseConnectionString("Provider=MSDAORA;Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host=127.0.0.1)(Port=1521))(CONNECT_DATA=(SID=ORACL)));User ID=scott;Password=tiger" ) )
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

def connectDB(connection_string) :
  if connection_string.startswith("[sqlite3]") :
    import sqlite3;  cn = sqlite3.connect(connection_string[9:])
    #print(sqlite3.version_info)
  elif connection_string.startswith("postgresql") :
    ## python -m pip install --upgrade psycopg2
    import psycopg2;  cn = psycopg2.connect(connection_string)
    #print(cn.dsn)
  elif connection_string.startswith("Driver=") :
    ## python -m pip install --upgrade pyodbc
    import pyodbc;  cn = pyodbc.connect(connection_string)
    #print( pyodbc.version )
  else :
    ## python -m pip install --upgrade cx_Oracle ## http://cx-oracle.readthedocs.io/en/latest/installation.html
    import cx_Oracle;  cn = cx_Oracle.connect(connection_string);
    #print(cn.version)
  #
  return cn
#

#----------------------------------------------------------------------#

def pad(str, n, c) :
  absN = abs(n);
  i = absN - len(str);
  if (n==0) :
    return ""
  elif (i==0) :
    return str
  elif (i < 0) :
    return str[0:absN] if (n > 0) else str[len(str)-absN:];
  elif (i > 0) :
    return str.ljust(absN, c) if (n > 0) else str.rjust(absN, c);
  return str;

#----------------------------------------------------------------------#

def rs2html(cur, rs):
  import prettytable # python -m pip install PrettyTable
  # return prettytable.from_db_cursor(cur).get_html_string()
  t = prettytable.from_db_cursor(cur)
  for r in rs: t.add_row(r)
  html = t.get_html_string()
  ## printV(html);  quit()
  return html
#

def rs2txt(cur, rs, lineMaxWidth):
  if (lineMaxWidth==-9) :
    import prettytable # python -m pip install PrettyTable
    if True :
      t = prettytable.PrettyTable([ i[0] for i in cur.description ])
      t.padding_width= 0 # space between column edges and contents (default=1)
      t.align = "l" # Left align
      for r in cur: t.add_row(r)
    return t.get_string();

    # import prettytable # python -m pip install PTable
    # return prettytable.from_db_cursor(cur).get_string();
  else :
    txt = "";  data = {};
    x = 0;  colType = [];  colMaxWidth = [];
    for colDescr in cur.description:
      data["-2,"+str(x)] = colDescr[0];
      ## print(colDescr[0] + " >> colDescr[1]==" + str(colDescr[1]));
      colType.append(str(colDescr[1]));
      colMaxWidth.append(len(colDescr[0])); # colMaxWidth.append(1);
      x += 1;
    #
    countCol = x;
    i = 0
    for r in rs: #for r in cur:
      for x in range(0, countCol, 1) :
        v = "" if r[x] is None else str(r[x]);  l = len(v);
        data[str(i)+","+str(x)] = v;
        if (l > colMaxWidth[x]) : colMaxWidth[x] = l;
      #
      i += 1
    #
    countRow = i;

    lineWidth = -1;
    for x in range(0, countCol, 1) :
      lineWidth = lineWidth + colMaxWidth[x] + 1;
      if (colType[x]=="Number" or colType[x]=="<class 'cx_Oracle.NUMBER'>") :
        colMaxWidth[x] = -colMaxWidth[x];
    #

    for i in range(-2, countRow, 1) :
      v = "-" if (i==-1) else " ";
      l = ""
      for x in range(0, countCol, 1) :
        if (x > 0) : l += " ";
        d = data.get(str(i)+","+str(x));
        if (d is None): d = "";
        l += pad(str(d), colMaxWidth[x], v);
      #
      if (lineMaxWidth > 0 and lineWidth > lineMaxWidth) : l = l[0:lineMaxWidth] + "<";
      txt += l + "\n";
    #
    return txt;

def saveRScsv(cur, rs, filepath, overwrite):
  import csv
  with open(filepath, 'w', newline='') as fout:
    writer = csv.writer(fout)
    writer.writerow([ i[0] for i in cur.description ]) # heading row
    writer.writerows(rs)  ## cur.fetchall()
  return;

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

## python -m pip install --upgrade google-auth google-auth-httplib2
import google.oauth2.service_account ## replace oauth2client with google-auth
def getGoogleCredentials():
  svcAcct = "QuoInsightSvc@developer.gserviceaccount.com"
  jsonkeyfile = r"D:\OAuth2\QuoInsightSvc.json"
  scopes = ["https://www.googleapis.com/auth/drive"]

  credentials = google.oauth2.service_account.Credentials.from_service_account_file(
    jsonkeyfile, scopes=scopes
  )

  return credentials
#

## python -m pip install --upgrade google-api-python-client
import googleapiclient.discovery
def connectGoogleSheets(credentials) :
  return googleapiclient.discovery.build('sheets', 'v4', credentials=credentials)
#

#----------------------------------------------------------------------#

def getWorkSheetTitle(googleSheetsSvc, fileId, gid) :
  spreadsheetInfo = googleSheetsSvc.spreadsheets().get(
    spreadsheetId=fileId, includeGridData=False
  ).execute()
  for s in spreadsheetInfo["sheets"] :
    p = s["properties"]
    if ( p["sheetType"]=="GRID" and p["sheetId"]==gid ):
      return p["title"]
    #
  #
  return ""
#

def deleteAllRows(googleSheetsSvc, fileId, gid, clearValuesOnly=False) :
  batchRequest = [
    {"deleteDimension": {"range": {"sheetId":gid, "dimension":"ROWS", "startIndex":1} } }, # delete entire cells
    {"deleteDimension": {"range": {"sheetId":gid, "dimension":"COLUMNS", "startIndex":1} } }, # delete entire cells
    {"deleteRange": {"range": {"sheetId":gid, "startRowIndex":0, "startColumnIndex":0}, "shiftDimension": "ROWS" } } # clear values only !!
  ]
  if (clearValuesOnly) :
    batchRequest = [
      {"deleteRange": {"range": {"sheetId":gid, "startRowIndex":0, "startColumnIndex":0}, "shiftDimension": "ROWS" } }
    ]
  #
  try :
    result = googleSheetsSvc.spreadsheets().batchUpdate(spreadsheetId=fileId,body={"requests":batchRequest}).execute()
  except Exception as err:
    result = str(err)
  #
  printV("deleteAllRows("+str(clearValuesOnly)+"): " + str(result));  ## quit();
  return result
#

def insertRows2GoogleSheets(googleSheetsSvc, fileId, targetRange, dataRows, insertDataOption) :
  ## [ https://developers.google.com/sheets/api/reference/rest/v4/spreadsheets.values/append ]
  if (insertDataOption is not None and insertDataOption.upper()=="OVERWRITE") :
    insertDataOption = "OVERWRITE"
  else :
    insertDataOption = "INSERT_ROWS"
  #
  return googleSheetsSvc.spreadsheets().values().append(
    spreadsheetId=fileId, range=targetRange,
    valueInputOption='USER_ENTERED', insertDataOption=insertDataOption,
    body={"range": targetRange, "majorDimension": "ROWS", "values": dataRows}
  ).execute()
#

import datetime
def insertRs2GoogleSheets(googleSheetsSvc, fileId, targetRange, cur, includeHeaders, insertDataOption) :
  dataRows = []
  if (includeHeaders) :
    thisRow = []
    for colDescr in cur.description:
      thisRow.append(colDescr[0])
    #
    dataRows.append(thisRow)
  #
  for r in cur : ## rs = cur.fetchall()
    # dataRows.append(r)
    thisRow = []
    for x in r :
      v = str(x) if isinstance(x, datetime.date) else x
      thisRow.append(v)
    #
    dataRows.append(thisRow)
  #
  printV("totalRows: " + str(len(dataRows)))
  return insertRows2GoogleSheets(googleSheetsSvc, fileId, targetRange, dataRows, insertDataOption)
#

def exportRs2GoogleSheets(googleSheetsSvc, fileId, gid, targetRange, action, cur) :
  includeHeaders = False;
  insertDataOption = "INSERT_ROWS"
  if (action=="REFRESH") :
    deleteAllRows(googleSheetsSvc, fileId, gid);
    includeHeaders = True;
  elif (action=="OVERWRITE") :
    deleteAllRows(googleSheetsSvc, fileId, gid, True);
    includeHeaders = True;
    insertDataOption = "OVERWRITE"
  #
  return insertRs2GoogleSheets(googleSheetsSvc, fileId, targetRange, cur, includeHeaders, insertDataOption)
#

def getGoogleSheetsTarget(targetUrl) :
  googleSheetsSvc = None;  fileId = "";  gid = 0;  targetSheet = "";
  if actionType.endswith("GoogleSheets") :
    if ( targetUrl.startswith('https://docs.google.com/spreadsheets/') ) :
      m = targetUrl.split("/");  m9=m[-1]
      if ("#" in m9) or ("=" in m9) :
        fileId = m[-2]
        p = m9.find("gid=")
        if (p >= 0) :
          gid = int(m9[p+4:])
        #
      elif (m9=="") :
        fileId = m[-2]
      else : 
        fileId = m9
      #
    else :
      printV(
        "Unsupported targetUrl:\n" + targetUrl + "\n\n"
        + ">targetUrl must be in the below format:\n"
        + "> https://docs.google.com/spreadsheets/...\n"
      );
      quit();
    #

    credentials = getGoogleCredentials()
    googleSheetsSvc = connectGoogleSheets(credentials)
    targetSheet = getWorkSheetTitle(googleSheetsSvc, fileId, gid)
    printV(targetSheet)

    if (targetSheet is None or len(targetSheet) < 1) :
      print("Invalid target!")
      quit()
    #
  #
  return (googleSheetsSvc, fileId, gid, targetSheet)
#

#----------------------------------------------------------------------#

def takeAction(connection_string, sql, src, headObj, headTxt, footTxt) :
  actionType = headObj.get('action', defAction)
  targetUrl = headObj.get('targetUrl', defTarget)
  targetOption = headObj.get('targetOption', defOption)

  googleSheetsSvc = None;  fileId = "";  gid = 0;  target = "";
  if actionType.endswith("GoogleSheets") :
    (googleSheetsSvc, fileId, gid, targetSheet) = getGoogleSheetsTarget(targetUrl)
  #

  cn = connectDB(connection_string);  cur = cn.cursor();  cur.execute(sql)

  if ( actionType=="stdout" ) :

    printV( rs2txt(cur, cur.fetchall(), -1) )

  elif ( actionType.endswith("GoogleSheets") ) :

    printV( exportRs2GoogleSheets(googleSheetsSvc, fileId, gid, targetSheet, targetOption, cur) )

    if ( actionType=="mailGoogleSheets" ) :
      dataTxt = targetUrl
      sendMail(src, headObj, headTxt, dataTxt, footTxt)
    #

  else :

    rs = cur.fetchall();  ## cur.close();  print(rs);
    rowCount = len(rs);  ## print( rowCount )

    if ( headObj.get('sendNoData',False) and rowCount==0 ) :

      print("==No Record Found==\n")

    else :

      contentType='plain'; dataTxt=""; attachment=None;

      if rowCount==0 :
        dataTxt = "\n==No Record Found==\n"
      elif (actionType=="mailHTML") :
        contentType = 'html'
        dataTxt = "<br><br>" + rs2html(cur, rs) + "<br><br>"
      elif (actionType=="mailFile") :
        attachment = src + ".csv";  saveRScsv(cur, rs, attachment, True);
        attachment = [attachment]
        dataTxt = "" 
      else :
        dataTxt = rs2txt(cur, rs, -1)
      #

      sendMail(src, headObj, headTxt, dataTxt, footTxt, contentType, attachment)

    #

  #

  try   : cur.close(); 
  except: pass;
  cn.close()
#

########################################################################

def main(argv) :
  src = ( argv[1] if (len(argv)>1) else "" );  # [ternary operator] value_when_true if condition else value_when_false
  if (src == "/?") :
    print("usage: sql+.py [source [connection_string]]");
    quit();
  #

  if (src=="-") :
    sql = "".join(sys.stdin.readlines())
  else :
    data = getData(src)
    src = data[0];  sql = data[1].strip();
  #

  headObj = {};  headTxt = "";  footTxt = "";

  if sql.startswith("/*"):
    p = sql.index("*/")
    headTxt = sql[2:p]
    try :
      import json; headObj=json.loads(headTxt)
      headTxt = ""
    except:
      headObj = {}
    #
    if 'body' in headObj and len(headObj['body'])>0 : headTxt=headObj['body']
    sql = sql[p+2:].strip()
  #

  #print(src);
  #print(headTxt);
  #print(headObj.get('x'));
  print("\n"+sql+"\n");

  connection_string =  parseConnectionString(headObj['connection_string']) if ('connection_string' in headObj) else getConnectionString(argv, 2)
  print(connection_string);  ## quit();

  takeAction(connection_string, sql, src, headObj, headTxt, footTxt)
#

if __name__ == '__main__':
  main(sys.argv)
#

#__DATA__
# /* {
#   "connection_string": "scott/tiger@127.0.0.1:1521:ORCL",
#   "targetUrl": "https://docs.google.com/spreadsheets/d/fileId/edit#gid=0",
#   "targetOption": "REFRESH|OVERWRITE|INSERT_ROWS",
#   ".action": "mailFile|mailText|stdout|updateGoogleSheets",
#   "subject": "",
#   "sendNoData": false
# } */
#
# select sysdate, a.*, 10000 from dual a where 1=0
#
#__DATA__
#
