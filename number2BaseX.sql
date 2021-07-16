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
    Dbms_Output.put_line(l_base);
    l_str := '';
    WHILE (l_number > 0) LOOP
      l_mod := Mod(l_number, l_base);
      l_str := SubStr(p_basechars, l_mod+1, 1) || l_str;
      l_number := (l_number-l_mod) / l_base;
    END LOOP;
    RETURN l_str;
  END;
