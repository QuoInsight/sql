-- [ https://oracle-base.com/articles/9i/export-blob-9i ]
-- open the BLOB, read chunks into a buffer and write them to a file.
-- SELECT filename, Length(input_blob), Length(decrypted_clob) FROM xxpct.MSI_DECRYPT_TEST_TAB
DECLARE
  l_directory VARCHAR2(255) := '???';
  l_filename  VARCHAR2(255) := '?????';
  l_file      UTL_FILE.FILE_TYPE;
  l_buffer    RAW(32767);
  l_amount    BINARY_INTEGER := 32767;
  l_pos       INTEGER := 1;
  l_blob      BLOB;
  l_blob_len  INTEGER;

  v_fexists      BOOLEAN;
  v_file_length  NUMBER;
  v_block_size   BINARY_INTEGER;

BEGIN
  -- Get LOB locator
  SELECT input_blob INTO l_blob
  FROM TEST_TAB
  WHERE  filename=l_filename;

  l_blob_len := DBMS_LOB.getlength(l_blob);
  Dbms_Output.put_line('l_blob_len: '||l_blob_len);

  -- Open the destination file.
  l_file := UTL_FILE.fopen(l_directory, l_filename, 'wb', max_linesize=>32767);
  -- Read chunks of the BLOB and write them to the file
  -- until complete.
  WHILE l_pos <= l_blob_len LOOP
    DBMS_LOB.read(l_blob, l_amount, l_pos, l_buffer);
    UTL_FILE.put_raw(l_file, l_buffer, TRUE);
    l_pos := l_pos + l_amount;
  END LOOP;
  -- Close the file.
  UTL_FILE.fclose(l_file);

  UTL_FILE.FGETATTR(l_directory, l_filename, v_fexists, v_file_length, v_block_size);
  DBMS_OUTPUT.PUT_LINE ('file size: ' || v_file_length || ' byte(s)');
END;