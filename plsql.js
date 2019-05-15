
  var WshShell=null, ProcEnv=null, argv=null, src="";
  var regEx, match;
  var data=null, plsql="", connection_string="", cn=null;

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
                              + "tiger" ;
  }

  var argv = WScript.Arguments;
  src = (argv.length==0) ? "" : argv(0);
  if (src == "/?") {
    WScript.Echo("usage: plsql.js [source [connection_string]]");
    WScript.Quit();
  } else if (argv.length > 1) {
    connection_string = argv(1);
    regEx = /(\S+)\/(\S+)@(\S+):(\S+):(\S+)/;
    match = regEx.exec(connection_string); // "scott/tiger@127.0.0.1:1521:ORCL"
    if ( match != null ) {
      if ( match.length==6 ) {
        connection_string = "Provider=MSDAORA;Data Source="
                          + "(DESCRIPTION=(ADDRESS=(PROTOCOL=TCP)(Host="
                          + match[3] + ")(Port="
                          + match[4] + "))(CONNECT_DATA=(SID="
                          + match[5] + ")));User ID="
                          + match[1] + ";Password="
                          + match[2] ;
      }
    }
  } else if ( ProcEnv("ORACLE_ADOCONN")!="" ) {
    connection_string = ProcEnv("ORACLE_ADOCONN");
  } else{
    connection_string = "Provider=MSDAORA;Data Source=" + ProcEnv("ORACLE_SID") 
                      + ";User ID=" + ProcEnv("ORACLE_UID") + ";Password=" + ProcEnv("ORACLE_PWD");
  }

  data = getData(src);  src = data[0];  plsql = data[1];

  cn = WScript.CreateObject("ADODB.Connection");
  cn.Open(connection_string);

  WScript.StdOut.Write( runDbmsOutput(cn, plsql) );

  cn.Close();  cn=null;
  WScript.Quit();

  //////////////////////////////////////////////////////////////////////

  function runDbmsOutput(cn, plsql) {
    var buffer_size  = 20000;  // max=1000000 min=2000 dflt=20000 [ORA-20000: ORU-10027: buffer overflow, limit of 20000 bytes]
    var plsql2="", adocmd=null;

    if ( !isObj(cn) ) {  //  [ && TypeName(cn)="Connection" ]
      return "runDbmsOutput: Database connection not initialized!";
    } else if ( cn.State != 1 ) {
      return "runDbmsOutput: Database connection not ready!";
    } else if ( !( String(cn.Provider).indexOf("OraOLEDB.Oracle")==0 || String(cn.Provider).indexOf("MSDAORA")==0 ) ) {
      return "runDbmsOutput: Not supported!";
    }

    /*
     if we have at least one bind variable in the PL/SQL block
     when using MSDAORA, we must start with "BEGIN ..." instead of "DECLARE ..."
     that will avoid Err: Microsoft OLE DB Provider for Oracle: ORA-01008: not all variables bound
    
     "ORA-20000: ORU-10027: buffer overflow, limit of 2000 bytes" is a generic error message
     the actual limit being overflowed will be different from what shown by the error message !!
     actual buffer limit setting via Dbms_Output.Enable() is usually not honoured !!
    */
    plsql2 = "BEGIN\n"
           + " EXECUTE IMMEDIATE 'ALTER SESSION SET NLS_DATE_FORMAT=\"DD-MON-YYYY HH24:MI:SS\"';\n"
           + " Dbms_Output.Enable(" + buffer_size + ");\n"
           + " DECLARE\n"
           + "  function DumpDbmsOutput return long as\n"
           + "   l_line varchar2(255);\n"
           + "   l_endbuf number:=0;\n"
           + "   l_buffer long; /*max=32760*/\n"
           + "   i number:=0;\n"
           + "  begin\n"
           + "   while l_endbuf<>1 loop\n"
           + "    /*exit when length(l_buffer)+255 > 32767;*/\n"
           + "    dbms_output.get_line(l_line, l_endbuf);\n"
           + "    i := i + 1; -- l_line := i||': '||l_line;\n"
           + "    l_buffer := l_buffer || l_line || chr(10);\n"
           + "   end loop;\n"
           + "   return l_buffer;\n"
           + "  end ;\n"
           + " BEGIN\n"
           + "  /*--Start of Actual Codes [Line# 20+n]--*/\n"
           +    plsql    + "\n"
           + "  /*--End of Actual Codes--*/\n"
           + "  Raise_Application_Error(-20001, 'Completed');\n"
           + " EXCEPTION WHEN OTHERS THEN\n"
           + "  dbms_output.put_line(SQLERRM);\n"
           + "  ? := DumpDbmsOutput();\n"
           + " END;\n"
           + "END;" ;

    adocmd = WScript.CreateObject("ADODB.Command");
    with (adocmd) {
      ActiveConnection = cn;
      CommandType      = 1; // adCmdText 
      CommandText      = plsql2;
      Parameters.Append( CreateParameter("", 201, 2, buffer_size) ); // adLongVarChar instead of adVarChar
    }

    try {
      adocmd.Execute();
      return adocmd(0);
    } catch(err) {
      return "runDbmsOutput Err#" + err.number + ": " + err.description;
    }
  }

  //////////////////////////////////////////////////////////////////////

  function isObj(obj) {
    return (typeof(obj) === "object" && obj !== null);
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
//
// dbms_output.put_line('Line# 22: '||sysdate);
//
//__DATA__
//
