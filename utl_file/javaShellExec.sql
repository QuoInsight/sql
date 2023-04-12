create or replace and compile java source named apps."xxx_JvCls_HostCommand" as
  import java.io.*;
  public class xxx_JvCls_HostCommand {
    public static String exeCmd(String cmdln) {
      StringBuffer output = new StringBuffer();
      Process p;
      try {
        p = Runtime.getRuntime().exec(cmdln);  p.waitFor();
        BufferedReader reader = new BufferedReader(new InputStreamReader(p.getInputStream()));
        String line = "";  while ((line = reader.readLine())!= null) output.append(line + "\n");
      } catch (Exception e) {
        return e.toString();
      }
      return output.toString();
    }
  }
/

-- DROP FUNCTION apps.XXX_JV_HOSTCOMMAND
CREATE OR REPLACE FUNCTION apps.XXX_JV_HOSTCOMMAND ( p_cmdln IN VARCHAR2 )
  RETURN VARCHAR2 AS LANGUAGE JAVA NAME
   'xxx_JvCls_HostCommand.exeCmd( java.lang.String ) return java.lang.String';
/

DECLARE
  l_directory VARCHAR2(255);

BEGIN
  --select value from v$parameter where name = 'utl_file_dir';

  l_directory := '/usr/tmp';

  Dbms_Output.put_line(
    apps.XXX_JV_HOSTCOMMAND('ls -l '||l_directory)
  );

END;
