import psycopg2

connection = psycopg2.connect(
    dbname="postgres",  
    user="postgres",  
    password="1Q2w3E4r",
    host="localhost",
    port="5432",
)

cursor = connection.cursor()

sql_script = """
CREATE TABLE IF NOT EXISTS phonebook (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50),
    surname VARCHAR(50),
    phone VARCHAR(20)
);

CREATE OR REPLACE FUNCTION search_phonebook(pattern TEXT)
RETURNS SETOF phonebook AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM phonebook
    WHERE name ILIKE '%' || pattern || '%'
       OR surname ILIKE '%' || pattern || '%'
       OR phone ILIKE '%' || pattern || '%';
END;
$$ LANGUAGE plpgsql;


CREATE OR REPLACE PROCEDURE upsert_user(
    p_name VARCHAR,
    p_surname VARCHAR,
    p_phone VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM phonebook WHERE name = p_name AND surname = p_surname) THEN
        UPDATE phonebook
        SET phone = p_phone
        WHERE name = p_name AND surname = p_surname;
    ELSE
        INSERT INTO phonebook (name, surname, phone)
        VALUES (p_name, p_surname, p_phone);
    END IF;
END;
$$;


CREATE OR REPLACE PROCEDURE insert_many_users(
    p_names TEXT[],
    p_surnames TEXT[],
    p_phones TEXT[]
)
LANGUAGE plpgsql AS $$
DECLARE
    i INT;
    v_name TEXT;
    v_surname TEXT;
    v_phone TEXT;
BEGIN
    CREATE TEMP TABLE IF NOT EXISTS temp_invalid_phones (
        name TEXT,
        surname TEXT,
        phone TEXT
    ) ON COMMIT DROP;
    
    TRUNCATE temp_invalid_phones;

    FOR i IN 1..array_length(p_phones, 1) LOOP
        v_name := p_names[i];
        v_surname := p_surnames[i];
        v_phone := p_phones[i];
        IF v_phone ~ '^\+?[0-9]{6,15}$' THEN
            INSERT INTO phonebook (name, surname, phone) 
            VALUES (v_name, v_surname, v_phone);
        ELSE
            INSERT INTO temp_invalid_phones (name, surname, phone) 
            VALUES (v_name, v_surname, v_phone);
        END IF;
    END LOOP;
END;
$$;

CREATE OR REPLACE FUNCTION get_phonebook_paginated(p_limit INT, p_offset INT)
RETURNS SETOF phonebook AS $$
BEGIN
    RETURN QUERY
    SELECT *
    FROM phonebook
    ORDER BY id
    LIMIT p_limit OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE PROCEDURE delete_phonebook_data(
    p_search_val VARCHAR
)
LANGUAGE plpgsql AS $$
BEGIN
    DELETE FROM phonebook
    WHERE name = p_search_val 
       OR surname = p_search_val 
       OR phone = p_search_val;
END;
$$;
"""

try:
  cursor.execute(sql_script)
  connection.commit()
  print("успех"
  )
except Exception as e:
  print("Произошла ошибка при выполнении:", e)
finally:
  cursor.close()
  connection.close()