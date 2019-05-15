  var testMode = false;
  var adminMail = "QuoInsight@gmail.com";

  //var WShell = new ActiveXObject("WScript.Shell");  var ProcEnv = WShell.Environment("PROCESS");
  var ProcEnv = WScript.CreateObject("WScript.Shell").Environment("PROCESS");
  if ( ProcEnv("ORACLE_ADOCONN") + ProcEnv("ORACLE_SID") == "" ) {
    ProcEnv("ORACLE_HOME") = "C:\\oracle\\ora92";
    ProcEnv("PATH") = ProcEnv("ORACLE_HOME") + "\\bin;" + ProcEnv("PATH");
    ProcEnv("TNS_ADMIN") = ProcEnv("ORACLE_HOME") + "\\network\\ADMIN";
    ProcEnv("ORACLE_ADOCONN") = "Provider=MSDAORA;Data Source=(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host="
                              + "127.0.0.1)(Port="
                              + "1521))(CONNECT_DATA=(SID="
                              + "ORCL)));User ID="
                              + "scott;Password="
                              + "tiger"
                              ;
  }

  var src="", connection_string="";

  var argv = WScript.Arguments;
  src = (argv.length==0) ? "" : argv(0);
  if (src == "/?") {
    WScript.Echo("usage: sql+.js [source [connection_string]]");
    WScript.Quit();
  }

  connection_string = getConnectionString(argv, ProcEnv);
  //WScript.Echo(connection_string);

  var cn, sql="", actionType="stdout", headObj={}, headTxt="", dataTxt="", footTxt="", rs, attachment="";
  cn = WScript.CreateObject("ADODB.Connection");

  if ( src!="" && src!="." && !WScript.CreateObject("Scripting.FileSystemObject").FileExists(src) ) {

    cn.Open(connection_string);
    WScript.Echo(src);
    sql1 = "select SQL_STATEMENT_TEXT from apps.ALR_ALERTS where ALERT_NAME='" + src + "'";
    rs = cn.Execute(sql1);
    if (rs.EOF) {
      WScript.Echo("Not found in apps.ALR_ALERTS. Abort!");
      WScript.Quit();
    } else {
      sql = "" + rs(0);
      var s1=sql.toLowerCase(), p1=s1.indexOf("into",0);
      if (p1 > 1) {
        var p2=s1.indexOf("from",p1);
        if (p2 > p1) {
          sql = sql.substr(0, p1-1) + sql.substr(p2-1, sql.length);
        }
      }
    }

  } else {

    var data = getData(src);
    src = data[0];  sql = data[1];
    WScript.Echo(src);

    sql = sql.replace(/^\s+/,'').replace(/\s+$/,''); if ( sql.substring(0,2)=="/*" ) {
      var p = sql.indexOf("*/",3);
      headTxt = sql.substr(2, p-2) + "\n";
      headObj = parseJsonStr(headTxt);
      if (headObj.body && headObj.body.length>0) {
        headTxt = headObj.body;
      }
      sql = sql.substr(p+2, sql.length);
    }

    if (headObj.connection_string) connection_string = parseConnectionString(headObj.connection_string);
    cn.Open(connection_string);

  }

  WScript.Echo(sql + "\n");  rs = cn.Execute(sql);

  if ( headObj.action ) {
    actionType = headObj.action;
  } else if ( headObj.subject && headObj.to ) {
    actionType = "mailFile";
  }

  if ( actionType=="stdout" ) {

    WScript.Echo( rs2txt(rs, -1) );

  } else if ( rs.EOF && typeof(headObj.sendNoData)!="undefined" && !headObj.sendNoData ) {

    WScript.Echo( "==No Record Found==" );

  } else {

    var msgsubj="", msgbody="";

    if (headObj.subject && headObj.subject.length>0) {
      msgsubj = headObj.subject;
    } else {
      var p = src.lastIndexOf("\\");  if (p > 0) src = src.substr(p+1, src.length);
        p = src.lastIndexOf("."); if (p > 1) src = src.substr(0, p);
      msgsubj = src;
    }

    dataTxt = ( actionType=="mailFile" ) ? "" : rs2txt(rs, -1);
    msgbody = headTxt + dataTxt + footTxt + "\n\n[source: \\\\" + ProcEnv("COMPUTERNAME") + "\\cronjobs\\Oracle.Alert]";

    if ( actionType=="mailFile" ) {
      attachment = src + ".csv";  saveRScsv(rs, attachment, true);
      sendMail(headObj.to, headObj.cc, msgsubj, msgbody, attachment);
    } else {
      sendMail(headObj.to, headObj.cc, msgsubj, msgbody);
    }

  }

  WScript.Quit();

  //////////////////////////////////////////////////////////////////////

  function parseJsonStr(jsonStr) {
    var jsonObj = {};  try {
      eval("jsonObj = " + jsonStr);  // jsonObj = JSON.parse(jsonStr);
    } catch(e) {
      jsonObj.body = jsonStr;
    }
    return jsonObj;
  }

  //////////////////////////////////////////////////////////////////////

  function getConnectionString(argv, ProcEnv) {
    if (argv.length > 1) {
      return parseConnectionString(argv(1));
    } else if ( ProcEnv("ORACLE_ADOCONN")!="" ) {
      return ProcEnv("ORACLE_ADOCONN");
    } else {
      return "Provider=MSDAORA;Data Source=" + ProcEnv("ORACLE_SID") 
           + ";User ID=" + ProcEnv("ORACLE_UID") + ";Password=" + ProcEnv("ORACLE_PWD");
    }
    return "";
  }

  //////////////////////////////////////////////////////////////////////

  function parseConnectionString(connection_string) {
    var regEx = /(\S+)\/(\S+)@(\S+):(\S+):(\S+)/;
    var match = regEx.exec(connection_string); // "scott/tiger@127.0.0.1:1521:ORCL"
    if ( match != null ) {
      if ( match.length==6 ) {
        connection_string = "Provider=MSDAORA;Data Source="
                          + "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host="
                          + match[3] + ")(Port="
                          + match[4] + "))(CONNECT_DATA=(SID="
                          + match[5] + ")));User ID="
                          + match[1] + ";Password="
                          + match[2];
      }
    }
    return connection_string;
  }

  //////////////////////////////////////////////////////////////////////

  // [ https://stackoverflow.com/questions/202605/repeat-string-javascript ]
  function repeat(pattern, count) {
    if (count < 1) return '';
    var result = '';
    while (count > 1) {
      if (count & 1) result += pattern;
      count >>= 1, pattern += pattern;
    }
    return result + pattern;
  }

  function pad(str, n, c) {
    str = (typeof(str)=="undefined" || str==null) ? "" : "" + str;
    var absN = Math.abs(n);
    var i = absN - str.length;
    if (n==0) {
      return "";
    } else if (i==0) {
      return str;
    } else if (i < 0) {
      if (n > 0) {
        return str.substring(0, absN);
      } else {
        return str.substring(str.length-absN);
      }
    } else if (i > 0) {
      if (n > 0) {
        return repeat(c, i) + str;
      } else {
        return str + repeat(c, i);
      }
    }
  }

  //////////////////////////////////////////////////////////////////////

  function rs2txt(rs, lineMaxWidth) {
    var data={}, colMaxWidth={}, lineWidth, maxCol, maxRow, x, i, v, l, txt;
    if (!rs.BOF) rs.MoveFirst();
    if (rs.BOF && rs.EOF) {
      return "\n==No Record Found==\n";
    }

    maxCol = rs.Fields.Count - 1;
    for (var x=0; x<=maxCol; x++) {
      data["-1,"+x] = "" + rs.Fields.Item(x).Name;
      colMaxWidth[x] = 1;
    }
    i = 0;
    while (! rs.EOF) {
      i++;
      for (var x=0; x<=maxCol; x++) {
        v = "" + ( (rs.Fields.Item(x).Value==null) ? "" : rs.Fields.Item(x).Value );
        data[i+","+x] = v;
        l = v.length; // rs.Fields.Item(x).ActualSize
        if (l > colMaxWidth[x]) colMaxWidth[x] = l;
      }
      rs.MoveNext();
    }
    maxRow = i;

    lineWidth = -1;
    for (var x=0; x<=maxCol; x++) {
      lineWidth = lineWidth + colMaxWidth[x] + 1;
      if (rs.Fields.Item(x).Type==200) colMaxWidth[x] = -colMaxWidth[x];
    }

    txt = "";
    for (var i=-1; i<=maxCol; i++) {
      v = (i==0) ? "-" : " ";
      l = "";
      for (var x=0; x<=maxCol; x++) {
        if (x > 0) l += " ";
        l += pad(data[i+","+x], colMaxWidth[x], v);
      }
      if (lineMaxWidth > 0 && lineWidth > lineMaxWidth) l = l.substr(0,lineMaxWidth) + "<";
      txt = txt + l + "\n";
    }
    if (lineMaxWidth > 0 && lineWidth > lineMaxWidth) {
      txt = txt + "\n[warning: long lines (w=" + lineWidth + ") truncated (w=" + lineMaxWidth + ")]\n";
    }

    lineMaxWidth = lineWidth;
    return txt;
  }

  //////////////////////////////////////////////////////////////////////

  function addEmailDomain(p_mail_list, p_domain) {
    var mail_list, tmpArr, addr;
    if (! p_domain) p_domain = "@gmail.com";
    mail_list = p_mail_list;
    tmpArr = p_mail_list.split(",");
    if (tmpArr.length >= 1) {
      mail_list = "";
      for (var i=0, l=tmpArr.length; i<l; ++i) {
        var addr = tmpArr[i];
        if (addr.length > 0) {
          if ( addr.indexOf("@")==-1 ) addr+=p_domain;
          mail_list += "," + addr;
        }
      }
    }
    if (mail_list.substr(0,1)==",") mail_list = mail_list.substr(1,mail_list.length);
    return mail_list;
  }

  //////////////////////////////////////////////////////////////////////

  function sendMail0(maillist, cclist, msgsubj, msgbody) {
    var objCDOMail, attach;

    if (! maillist) maillist="";
    if (! cclist) cclist="";
    if (! msgsubj) msgsubj="";

    objCDOMail = WScript.CreateObject("CDONTS.NewMail");
    with (objCDOMail) {
      BodyFormat = 1; // HTML=0 TXT=1
      MailFormat = 1; // MIME=0 TXT=1 [must be MIME if BodyFormat is HTML]

      From = ProcEnv("COMPUTERNAME") + "@gmail.com";
      To = (maillist) ? maillist : "";
      Cc = (cclist) ? cclist : "";
      Bcc = adminMail;
      Subject = msgsubj;
      Body = msgbody;
      for (var i=4, l=arguments.length; i<l; ++i) {
        //WScript.Echo("arguments[" + i + "]: " + arguments[i] );
        Attachfile( arguments[i] );
      }
      if (testMode) {
        To = adminMail;
        Cc = "";
        Bcc = "";
        Subject = "[TEST] " + msgsubj;
        Body = maillist + "\n\n" + msgbody;
      }
      Send();
      WScript.Echo("SENT - " + msgsubj);
    }
  }

  //////////////////////////////////////////////////////////////////////

  function sendMail(maillist, cclist, msgsubj, msgbody) {
    var cdoConfig, sch, cdoMessage, attach;

    if (! maillist) maillist="";
    if (! cclist) cclist="";
    if (! msgsubj) msgsubj="";

    cdoConfig = WScript.CreateObject("CDO.Configuration");
      sch = "http://schemas.microsoft.com/cdo/configuration/";
      cdoConfig.Fields.Item(sch + "sendusing") = 2;
      cdoConfig.Fields.Item(sch + "smtpserver") = "127.0.0.1";
      cdoConfig.Fields.Update();

    cdoMessage = WScript.CreateObject("CDO.Message");
    with (cdoMessage) {
      Configuration = cdoConfig;
      From = ProcEnv("COMPUTERNAME") + "@gmail.com";
      To = (maillist) ? maillist : "";
      Cc = (cclist) ? cclist : "";
      Bcc = adminMail;
      Subject = msgsubj;
      TextBody = msgbody;
      for (var i=4, l=arguments.length; i<l; ++i) {
        //WScript.Echo("arguments[" + i + "]: " + arguments[i] );
        AddAttachment( arguments[i] );
      }
      if (testMode) {
        To = adminMail;
        Cc = "";
        Bcc = "";
        Subject = "[TEST] " + msgsubj;
        TextBody = maillist + "\n\n" + msgbody;
      }
      Send();
      WScript.Echo("SENT - " + msgsubj);
    }
  }

  //////////////////////////////////////////////////////////////////////

  function quoteCSV(typ, val) {
    var v = "" + val;
    if ( v.length>0 && (v.indexOf(',')>-1 || v.indexOf('"')>-1 || v.indexOf("\n")>-1) ) {
      v = '"' + v.replace('"','""') + '"';
    } else if (typ==135) {
      var d = new Date(val);
      v = d.getFullYear() + "-" + (d.getMonth()+1) + "-" + d.getDate()
        + " " + d.getHours() + ":" + d.getMinutes() + ":" + d.getSeconds();
    } else if (typ==129 || typ==200 || typ==201 || typ==202) {
      //v = '="' + v + '"';
      v = '"' + v.replace('"','""') + '"';
    }
//WScript.Echo("**" + typ + "**" + v);
    return v;
  }

  //////////////////////////////////////////////////////////////////////

  function saveRScsv(rs, filename, overwrite) {
    var fso, f, x, i;
    var ForReading = 1, ForWriting = 2, ForAppending = 3;

    fso = WScript.CreateObject("Scripting.FileSystemObject");
    if ( filename.length > 0 && fso.FileExists(filename) ) {
      (overwrite) ? fso.DeleteFile(filename) : filename = "";
    }
    if ( filename.length == 0 ) {
      filename = fso.GetTempName();
      filename = replace(filename,".tmp", ".csv");
    }
    f = fso.OpenTextFile(filename, 8, true, false);

    if (rs.BOF && rs.EOF) {
      f.Write("No Data\n");
      f.Close();  f=null;
      return;
    }

    for (var x=0; x < rs.Fields.Count; x++) {
      if (x > 0) f.Write(",");
      f.Write( quoteCSV(200, rs.Fields.Item(x).Name) );
    }
    f.Write("\n");
    var i = 0;
    while ( ! rs.EOF ) {
      i++;
      WScript.StdOut.Write(i + "..");
      for (var x=0; x < rs.Fields.Count; x++) {
        if (x > 0) f.Write(",");
        f.Write( quoteCSV(rs.Fields.Item(x).Type, rs.Fields.Item(x).Value) );
      }
      f.Write("\n");
      rs.MoveNext();
    }
    WScript.StdOut.WriteLine("Done!");
    f.Close();  f=null;
  }

  //////////////////////////////////////////////////////////////////////

  function getData(src) {
    var fn, f, startData, ln, txt;
    if (src.length == 0) {
      fn = WScript.ScriptFullName;
    } else if (src.substr(0,1) == ".") {
      fn = WScript.ScriptFullName;
      fn = fn.substr(0, fn.lastIndexOf(".")) + src;
    } else {
      fn = src;
    }
    f = WScript.CreateObject("Scripting.FileSystemObject").OpenTextFile(fn, 1);
    if (src.length > 0) {
      txt = f.ReadAll();
    } else {
      txt = "";
      startData = 0;
      while ( ! f.AtEndOfStream ) {
        ln = f.ReadLine();
        if ( ln.indexOf("//__DATA__")==0 ) {
          startData++;
        } else if ( (startData % 2)==1 && ln.length>0 ) {
          txt += ln.substr(2, ln.length-2) + "\n";
        }
      }
    }
    f.Close();

    return [fn, txt];
  }

  //////////////////////////////////////////////////////////////////////

//__DATA__
// /* {
//   "connection_string": "scott/tiger@127.0.0.1:1521:ORCL",
//   "action": "mailFile|mailText|stdout", "subject": "", "sendNoData": false
// } */
// select sysdate, a.*, 10000 from dual a where 1=0
//
//__DATA__
//
