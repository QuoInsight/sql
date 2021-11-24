-- [ https://stackoverflow.com/questions/4181128/problem-in-finding-list-of-files-in-directory/40728609 ]
-- create global temporary table XXX_DIR_LIST_TMP ( FILENAME VARCHAR2(255) ) on commit preserve rows;
-- grant ALL on XXX_DIR_LIST_TMP to PUBLIC;

create or replace and compile java source named "XXX_DirList" as
  import java.io.*;
  import java.sql.*;
  public class XXX_DirList {
    public static void getList(String directory) throws SQLException {
      File dir = new File( directory );
      String[] files = dir.list();
      String theFile;
      for (int i = 0; i < files.length; i++) {
        theFile = files[i];
        #sql { INSERT INTO XXX_DIR_LIST_TMP (FILENAME) VALUES ( :theFile ) };
      }
    }
  }
/

CREATE OR REPLACE PROCEDURE XXX_dir_list(
  pi_directory IN VARCHAR2
) AS LANGUAGE JAVA name 'XXX_DirList.getList(java.lang.String)';


exec XXX_dir_list( '???' );

SELECT * FROM XXX_DIR_LIST_TMP