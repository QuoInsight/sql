DECLARE
  TYPE txtHash IS TABLE OF VARCHAR2(255) INDEX BY VARCHAR2(50);
  headers txtHash;

  data    CLOB;
  l_count NUMBER;

  /*------------------------------------------------------------------*/

  FUNCTION println(p_Data IN OUT NOCOPY CLOB)
  RETURN NUMBER
  AS
    i         number;
    startPos  number;
    endPos    number;
    chunkSize number;
    totalSize number;
    lc_buffer varchar2(32767);
  BEGIN
    -- http://stackoverflow.com/questions/11647041/reading-clob-line-by-line-with-pl-sql
    if ( dbms_lob.isopen(p_Data) != 1 ) then
      dbms_lob.open(p_Data, 0);
    end if;
    i := 0;
    startPos := 1;
    totalSize := Dbms_Lob.getlength(p_Data);
    loop
      i := i + 1;
      endPos := instr(p_Data, Chr(10), startPos);
      IF endPos=0 THEN endPos:=totalSize+1; END IF;
      IF endPos > startPos THEN
        chunkSize := (endPos-startPos);
        dbms_lob.read(p_Data, chunkSize, startPos, lc_buffer);
      ELSE
        lc_buffer := NULL;
      END IF;

      dbms_output.put_line(SubStr(lc_buffer,1,240));

      startPos := endPos+1;
      EXIT WHEN startPos >= totalSize;
    end loop;
    if ( dbms_lob.isopen(p_Data) = 1 ) then
      dbms_lob.close(p_Data);
    end if;
    RETURN i;
  END;

  /*------------------------------------------------------------------*/

  PROCEDURE write_lob(l IN OUT NOCOPY CLOB, v VARCHAR2) AS
  BEGIN
    --IF ( dbms_lob.isopen(l) != 1 ) THEN
    --  dbms_lob.createtemporary(l, TRUE, dbms_lob.call);
    --  dbms_lob.open(l, dbms_lob.lob_readwrite);
    --END IF;
    dbms_lob.writeappend(l, length(v), v);
  END;

  /*------------------------------------------------------------------*/

  FUNCTION wget3(
   url VARCHAR2, method VARCHAR2 DEFAULT 'GET',
   headers txtHash, data CLOB, timeout NUMBER DEFAULT 0
  ) RETURN CLOB AS
    httpReq    utl_http.req;
    headerName VARCHAR2(240);
    startPos  NUMBER:=1;
    chunkSize NUMBER:=1024;
    totalSize number;
    lc_buffer varchar2(32767);

    httpResp   utl_http.resp;
    respTxt    VARCHAR2(1024);
    tempLob    CLOB;
  BEGIN
    dbms_lob.createtemporary(tempLob, TRUE, dbms_lob.call);
    dbms_lob.open(tempLob, dbms_lob.lob_readwrite);

    -- utl_http.set_wallet(<wallet_path>, <wallet_password>);
    utl_http.set_response_error_check(false); -- do not raise an exception when get_response returns a status codes of 4xx or 5xx
    utl_http.set_persistent_conn_support(false);

    httpReq := utl_http.begin_request(url, method);
    utl_http.set_header(httpReq, 'User-Agent', 'Mozilla/4.0');
    utl_http.set_header(httpReq, 'Content-Length', Nvl(LengthB(data),0));

    headerName := headers.FIRST;
    WHILE headerName IS NOT NULL LOOP
      utl_http.set_header(httpReq, headerName, headers(headerName));
      headerName := headers.NEXT(headerName);
    END LOOP;

    WHILE startPos < DBMS_LOB.getlength(data) LOOP
      DBMS_LOB.READ(data, chunkSize, startPos, lc_buffer);
      utl_http.write_text(httpReq, lc_buffer);
      startPos := startPos + chunkSize;
    END LOOP;

    httpResp := utl_http.get_response(httpReq);
    IF (httpResp.status_code <> UTL_HTTP.HTTP_OK) THEN
      dbms_output.put_line('responseCode: '||httpResp.status_code);
    END IF;

    BEGIN
      LOOP
        utl_http.read_text(httpResp, respTxt, 1024);
        dbms_lob.writeappend(tempLob, length(respTxt), respTxt);
      END LOOP;
    EXCEPTION
      WHEN utl_http.end_of_body THEN
        dbms_output.put_line('==end read_text==');
      WHEN OTHERS THEN
        dbms_output.put_line('ERR #'||SQLCODE||': '||SQLERRM);
    END;
    utl_http.end_response(httpResp);

    RETURN tempLob;
  END;

  /*------------------------------------------------------------------*/

BEGIN
  headers('Content-Type') := 'application/x-www-form-urlencoded';
  headers('TEST') := 'TEST12';

  dbms_lob.createtemporary(data, TRUE, dbms_lob.call);
  dbms_lob.open(data, dbms_lob.lob_readwrite);

  write_lob(data, 'A=1&B=2');

  data := wget3('https://www.google.com', 'POST', headers, data, 0);
  l_count := println(data);

  --dbms_lob.freetemporary(data);
END;
