DECLARE
  l_directory VARCHAR2(255);
  l_filename VARCHAR2(255);

  v_fexists      BOOLEAN;
  v_file_length  NUMBER;
  v_block_size   BINARY_INTEGER;

  l_bfile BFILE;
  l_blob   BLOB;

  l_dest_offset INTEGER := 1;
  l_src_offset  INTEGER := 1;

BEGIN
  l_directory := '???';
  l_filename := '?????';

  -- select * from all_directories where directory_name like '??%'

  UTL_FILE.FGETATTR(l_directory, l_filename, v_fexists, v_file_length, v_block_size);
  DBMS_OUTPUT.PUT_LINE (v_file_length || ' byte(s)');

  l_bfile := BFILENAME(l_directory, l_filename);
  --DBMS_LOB.fileopen(l_bfile, DBMS_LOB.file_readonly);
  -- !! PLS-00564: lob arguments are not permitted in calls to remote server !!
  DBMS_LOB.OPEN(l_bfile, DBMS_LOB.LOB_READONLY);

  DBMS_LOB.CREATETEMPORARY(
    lob_loc => l_blob,
    cache   => TRUE,
    dur     => dbms_lob.session
  );
  DBMS_LOB.OPEN(l_blob, DBMS_LOB.LOB_READWRITE);

  DBMS_LOB.loadblobfromfile (  -- loadfromfile deprecated.
    dest_lob    => l_blob,
    src_bfile   => l_bfile,
    amount      => DBMS_LOB.lobmaxsize,
    dest_offset => l_dest_offset,
    src_offset  => l_src_offset
  );
  DBMS_LOB.fileclose(l_bfile);

  DBMS_OUTPUT.PUT_LINE (Length(l_blob) || ' byte(s)');
  DBMS_LOB.fileclose(l_bfile);

END;