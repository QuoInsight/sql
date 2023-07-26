DECLARE
  TYPE t_arr IS TABLE OF VARCHAR2(4000); -- INDEX BY PLS_INTEGER;

  l_timestamp  TIMESTAMP:=SYSTIMESTAMP;

  i            NUMBER := 0;
  fileId       VARCHAR2(255);
  gid          VARCHAR2(255);

  targetUrl    VARCHAR2(2000);
  lastModified DATE;
  data         CLOB;

  /*------------------------------------------------------------------*/

  FUNCTION timediff(p_timestamp0 TIMESTAMP, p_timestamp1 TIMESTAMP:=SYSTIMESTAMP)
  RETURN NUMBER
  AS
    l_date0 DATE:=CAST(p_timestamp0 AS DATE);
    l_date1 DATE:=CAST(p_timestamp1 AS DATE);
    n0 NUMBER;
    n1 NUMBER;
    n  NUMBER;
  BEGIN
    n := round(24*60*60*(l_date1-l_date0));
    IF n <= 1 THEN
      n0 := extract(SECOND FROM p_timestamp0) + 60*extract(MINUTE FROM p_timestamp0);
      n1 := extract(SECOND FROM p_timestamp1) + 60*extract(MINUTE FROM p_timestamp1);
      n  := Round(n1-n0, 2);
    END IF;
    RETURN n;
  END timediff;

  /*------------------------------------------------------------------*/

  FUNCTION split(p_list varchar2, p_del varchar2 := ',')
  RETURN t_arr IS
    i        NUMBER := 0;
    l_idx    pls_integer;
    l_list   varchar2(32767) := p_list;
    l_value  varchar2(32767);
    l_arr    t_arr := t_arr(); /*must initialize if not declared as INDEX BY PLS_INTEGER*/
  BEGIN
    i := 0;
    l_list := p_list;
    LOOP
      i := i + 1;
      l_arr.extend; /*also must extend if not declared as INDEX BY PLS_INTEGER*/
      l_idx := InStr(l_list,p_del);
      IF l_idx > 0 THEN
        l_arr(i) := substr(l_list,1,l_idx-1);
        l_list := substr(l_list,l_idx+length(p_del));
      ELSE
        l_arr(i) := l_list;
        EXIT;
      END IF;
    END LOOP;
    FOR l_idx IN i+1 .. 20 LOOP
      l_arr.extend;
      l_arr(l_idx) := NULL;
    END LOOP;
    RETURN l_arr;
  END split;

  /*------------------------------------------------------------------*/

  FUNCTION getURL(url VARCHAR2)
  RETURN CLOB AS
    http_req   utl_http.req;
    http_resp  utl_http.resp;
    data       VARCHAR2(1024);
    temp_lob   CLOB;
  BEGIN
    dbms_lob.createtemporary(temp_lob, TRUE, dbms_lob.call);
    dbms_lob.open(temp_lob, dbms_lob.lob_readwrite);

    http_req := utl_http.begin_request(url);
    utl_http.set_header(http_req, 'User-Agent', 'Mozilla/4.0');
    http_resp := utl_http.get_response(http_req);

    BEGIN
      LOOP
        utl_http.read_text(http_resp, data, 1024);
        dbms_lob.writeappend(temp_lob, length(data), data);
      END LOOP;
    EXCEPTION
      WHEN utl_http.end_of_body THEN
        dbms_output.put_line('==end read_text==');
      WHEN OTHERS THEN
        dbms_output.put_line('ERR #'||SQLCODE||': '||SQLERRM);
    END;
    utl_http.end_response(http_resp);

    RETURN temp_lob;
  END;

  /*------------------------------------------------------------------*/

  FUNCTION getGoogleDoc(url VARCHAR2)
  RETURN CLOB AS
    proxyUrl VARCHAR2(255):='http://....';
  BEGIN
    RETURN getURL(proxyUrl||'?url='||utl_url.escape(url, true));
  END;

  /*------------------------------------------------------------------*/

  FUNCTION getGoogleDocLastModifiedDate(fileId VARCHAR2)
  /*
    [Gets a file's metadata by ID] https://developers.google.com/drive/v2/reference/files/get
      GET https://www.googleapis.com/drive/v2/files/fileId
  */
  RETURN DATE AS
    data CLOB:=getGoogleDoc('https://www.googleapis.com/drive/v2/files/'||fileId);
    tmpStr VARCHAR2(1024);
  BEGIN
    tmpStr := regexp_substr(data, '"modifiedDate" *: *"(.*)"', 1, 1, 'i');
    tmpStr := regexp_substr(tmpStr, '[^"]+', 1, 3);
    RETURN CAST( to_timestamp(tmpStr, 'yyyy-mm-dd"T"hh24:mi:ss.ff3"Z"') AS DATE );
  END;

  /*------------------------------------------------------------------*/

  procedure println(p_clob in out nocopy clob)
  -- http://stackoverflow.com/questions/11647041/reading-clob-line-by-line-with-pl-sql
  is
    startPos  number;
    endPos    number;
    chunkSize number;
    totalSize number;
    lc_buffer varchar2(32767);
    i         number;
  begin
    if ( dbms_lob.isopen(p_clob) != 1 ) then
      dbms_lob.open(p_clob, 0);
    end if;
    i := 0;
    startPos := 1;
    totalSize := Dbms_Lob.getlength(p_clob);
    loop
      i := i + 1;
      endPos := instr(p_clob, Chr(10), startPos);
      IF endPos=0 THEN endPos:=totalSize; END IF;
      IF endPos > startPos THEN
        chunkSize := (endPos-startPos);
        dbms_lob.read(p_clob, chunkSize, startPos, lc_buffer);
      ELSE
        lc_buffer := NULL;
      END IF;
      dbms_output.put_line(i||':'||lc_buffer);
      startPos := endPos+1;
      EXIT WHEN startPos >= totalSize;
    end loop;
    dbms_output.put_line('Total Lines: '||i);
    if ( dbms_lob.isopen(p_clob) = 1 ) then
      dbms_lob.close(p_clob);
    end if;
  exception
    when others then
       dbms_output.put_line('Error : '||sqlerrm);
  end println;

  /*------------------------------------------------------------------*/

  FUNCTION insertDataIntoTmpTable(p_Data IN OUT NOCOPY CLOB, p_recordSeparator VARCHAR2, p_fieldSeparator VARCHAR2)
  RETURN NUMBER
  AS
    i         number;
    startPos  number;
    endPos    number;
    chunkSize number;
    totalSize number;
    lc_buffer varchar2(32767);
    dataArr   t_arr;
  BEGIN
    if ( dbms_lob.isopen(p_Data) != 1 ) then
      dbms_lob.open(p_Data, 0);
    end if;
    i := 0;
    startPos := 1;
    totalSize := Dbms_Lob.getlength(p_Data);
    loop
      i := i + 1;
      endPos := instr(p_Data, p_recordSeparator, startPos);
      IF endPos=0 THEN endPos:=totalSize; END IF;
      IF endPos > startPos THEN
        chunkSize := (endPos-startPos);
        dbms_lob.read(p_Data, chunkSize, startPos, lc_buffer);
      ELSE
        lc_buffer := NULL;
      END IF;

      dataArr := split(lc_buffer, p_fieldSeparator);
        dataArr(2) := dataArr(8);  -- ColumnH [LineName]
        dataArr(3) := dataArr(22);  -- ColumnV [Average UPH]

      INSERT INTO XX_SHARED_TABLE1_TEMP (
        n_attr1, c_attr1, c_attr2, c_attr3, c_attr4, c_attr5, c_attr6, c_attr7, c_attr8, c_attr9, c_attr10,
        c_attr11, c_attr12, c_attr13, c_attr14, c_attr15, c_attr16, c_attr17, c_attr18, c_attr19, c_attr20
      ) VALUES (
        i, dataArr(1), dataArr(2), dataArr(3), dataArr(4), dataArr(5), dataArr(6), dataArr(7), dataArr(8), dataArr(9), dataArr(10),
        dataArr(11), dataArr(12), dataArr(13), dataArr(14), dataArr(15), dataArr(16), dataArr(17), dataArr(18), dataArr(19), dataArr(20)
      );

      --dbms_output.put_line(i||':'||lc_buffer);

      startPos := endPos+1;
      EXIT WHEN startPos >= totalSize;
    end loop;
    if ( dbms_lob.isopen(p_Data) = 1 ) then
      dbms_lob.close(p_Data);
    end if;
    RETURN i;
  END;


  /*------------------------------------------------------------------*/

BEGIN
  fileId := '1U7C5oaPAMn0kcdrW80I--klw5F8GwS0_Ri69Z4uJHAY';
  gid := '165676135';

  lastModified := getGoogleDocLastModifiedDate(fileId);
  dbms_output.put_line( lastModified );

  targetUrl := 'https://docs.google.com/spreadsheets/d/'||fileId||'/export?gid='||gid||'&format=tsv';
  data := getGoogleDoc(targetUrl);
  i := insertDataIntoTmpTable(data, Chr(10), Chr(9));
  Dbms_Output.put_line('Total Records Loaded: '||i);
END;

