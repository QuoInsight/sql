DECLARE
  F utl_file.file_type;
  l_directory VARCHAR2(255);
  l_filename VARCHAR2(255);
  l_txtln VARCHAR2(2000);
BEGIN
  l_directory := '???';
  l_filename := '?????';

  F := utl_file.fopen(l_directory, l_filename, 'w');
  utl_file.put_line(F,'test',FALSE);
  utl_file.fclose(F);
END;

