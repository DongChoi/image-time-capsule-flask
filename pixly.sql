

DROP DATABASE IF EXISTS pixly;
CREATE DATABASE pixly;
\connect pixly;

CREATE TABLE images (
    image_key text PRIMARY KEY,
    image_url text NOT NULL
);

CREATE TABLE image_data (
    image_type text NOT NULL,
    image_value text NOT NULL,
    image_key text REFERENCES images(image_key)
);

-- def getmetadata:
--     SELECT location,model,time from photos where id = $1

-- #get metadata from upload-front end




-- def postimage:
--     post logic
--     insert into photos location = url, time ,model

