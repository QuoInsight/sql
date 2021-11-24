DECLARE

  -- [ https://community.oracle.com/tech/developers/discussion/4202231/how-can-i-allow-this-procedure-to-attach-to-email-pdf-file-in-the-directory-pdf-file-that-is-32 ]
  PROCEDURE mail_attach_binary (
        recipients     VARCHAR2,
        subject        VARCHAR2,
        message        VARCHAR2,
        att_file_loc   VARCHAR2,
        att_filename   VARCHAR2
    ) AS
        v_bfile               BFILE;
        destoffset            INTEGER := 1;
        warning               INTEGER;
        v_mail_conn           utl_smtp.connection;
        v_smtp_server         CONSTANT VARCHAR2(256) := '????';
        v_smtp_server_port    NUMBER := 25;
        v_sender_email        CONSTANT VARCHAR2(256) := '????';
        l_boundary            CONSTANT VARCHAR2(256) := '7D81B75CCC90D2974F7A1CBD';
        v_length              INTEGER :=0;
        v_raw                 RAW(57);
        v_buffer_size         INTEGER := 57;  -- The buffer size must be 57 for utl_encode to work

    BEGIN
        v_mail_conn := utl_smtp.open_connection(v_smtp_server, v_smtp_server_port);
        utl_smtp.helo(v_mail_conn, v_smtp_server);
        utl_smtp.mail(v_mail_conn, v_sender_email);
        utl_smtp.rcpt(v_mail_conn, recipients);
        utl_smtp.open_data(v_mail_conn);
        utl_smtp.write_data(v_mail_conn, 'Date: '|| TO_CHAR(SYSDATE, 'DD-MON-YYYY HH24:MI:SS')|| utl_tcp.crlf);
        utl_smtp.write_data(v_mail_conn, 'To: '|| recipients|| utl_tcp.crlf);
        utl_smtp.write_data(v_mail_conn, 'From: '|| v_sender_email|| utl_tcp.crlf);
        utl_smtp.write_data(v_mail_conn, 'Subject: '|| subject|| utl_tcp.crlf);

        UTL_SMTP.WRITE_RAW_DATA(v_mail_conn, UTL_RAW.CAST_TO_RAW(
          'Content-Transfer-Encoding: 7bit' || UTL_TCP.CRLF
        ||'Content-Type: multipart/mixed;boundary="'||l_boundary||'"' || UTL_TCP.CRLF
        ||'Mime-Version: 1.0' || UTL_TCP.CRLF
        ||'--'|| l_boundary || UTL_TCP.CRLF
        ||'Content-Transfer-Encoding: binary' || UTL_TCP.CRLF
        ||'Content-Type: text/plain' || UTL_TCP.CRLF
        ||UTL_TCP.CRLF
        ||message || UTL_TCP.CRLF
        ));

        -- Content of attachment
        utl_smtp.write_data(v_mail_conn, '--'|| l_boundary || UTL_TCP.CRLF);
        utl_smtp.write_data(v_mail_conn, 'Content-Type'||':'||'application/octet-stream'|| utl_tcp.crlf);
        utl_smtp.write_data(v_mail_conn, 'Content-Disposition: attachment; filename="' || att_filename || '"' || utl_tcp.crlf);
        utl_smtp.write_data(v_mail_conn, 'Content-Transfer-Encoding: base64' || utl_tcp.crlf);
        utl_smtp.write_data(v_mail_conn, utl_tcp.crlf);

        --Get the file to attach to the e-mail
         v_bfile := bfilename(att_file_loc, att_filename);
         dbms_lob.fileopen(v_bfile, dbms_lob.file_readonly);

        -- Get the size of the file to be attached
        v_length := dbms_lob.getlength(v_bfile);
        Dbms_Output.put_line('file size: '||v_length||' byte(s)');

        -- Send the email byte chunks to UTL_SMTP
        WHILE destoffset < v_length LOOP
          --Dbms_Output.put_line('destoffset: ' || destoffset); -- warning: buffer overflow !!
          -- !! The buffer size must be 57 for utl_encode to work !! total ~11s for 4MB !!
          dbms_lob.read(v_bfile, v_buffer_size, destoffset, v_raw);
          utl_smtp.write_raw_data(v_mail_conn, utl_encode.base64_encode(v_raw));
          destoffset := destoffset + v_buffer_size;
        END LOOP;
        utl_smtp.write_data(v_mail_conn, utl_tcp.crlf
           || '--' || l_boundary || utl_tcp.crlf
           || '--' || utl_tcp.crlf
        );

        --close SMTP connection and LOB file
        DBMS_LOB.filecloseall;
        dbms_lob.fileclose(v_bfile);
        utl_smtp.close_data(v_mail_conn);
        utl_smtp.quit(v_mail_conn);
    END mail_attach_binary;

BEGIN

   mail_attach_binary(
     recipients => '????',
     subject => 'test',  message => 'file attached',
     att_file_loc => '???', att_filename => '???'
   );

   Dbms_Output.put_line('OK');
END;
