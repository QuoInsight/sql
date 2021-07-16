  FUNCTION number2BaseX (
    p_number NUMBER, p_basechars VARCHAR2 DEFAULT '0123456789BCDFGHJKLMNPQRSTVWXZ'
  ) RETURN VARCHAR2 IS
    l_number NUMBER;
    l_base NUMBER;
    l_mod NUMBER;
    l_p NUMBER;
    l_str VARCHAR2(240);
  BEGIN
    l_number := p_number;
    l_base := Length(p_basechars);
    --Dbms_Output.put_line(l_base);
    IF l_number=0 THEN
      RETURN SubStr(p_basechars, 1, 1);
    END IF;
    l_str := '';
    WHILE (l_number > 0) LOOP
      l_mod := Mod(l_number, l_base);
      l_str := SubStr(p_basechars, l_mod+1, 1) || l_str;
      l_number := (l_number-l_mod) / l_base;
    END LOOP;
    RETURN l_str;
  END;

  FUNCTION encBase16 (
    p_number NUMBER
  ) RETURN VARCHAR2 IS
    l_basechars VARCHAR2(16) DEFAULT '0123456789ABCDEF';
    l_numericPlaces NUMBER;
    l_skipStart NUMBER;
    l_skipEnd NUMBER;
    l_str VARCHAR2(240);
  BEGIN
    l_numericPlaces := 2;
    l_skipStart := Power(10,l_numericPlaces);
    l_skipEnd := 10*Power(16,l_numericPlaces-1);
    Dbms_Output.put_line('skipped number: '||l_skipStart||'..'||(l_skipEnd-1));
    Dbms_Output.put_line('skipped base16: ..'||number2BaseX(l_skipEnd-1,l_basechars));
    IF p_number>=0 AND p_number<l_skipStart THEN
      l_str := To_Char(p_number);
    ELSE
      l_str := number2BaseX(p_number-l_skipStart+l_skipEnd, l_basechars);
    END IF;
    IF Length(l_str)<l_numericPlaces THEN
      l_str := LPad(l_str,l_numericPlaces,'0');
    END IF;
    RETURN l_str;
  END;

