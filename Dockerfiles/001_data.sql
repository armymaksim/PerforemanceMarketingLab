

CREATE TABLE image_manager."public"."images" (
    "id" serial NOT NULL ,
    "name" varchar NOT NULL,
    "original_file_name" varchar NOT NULL,
    "image_md5" varchar NOT NULL,
    "file_type" varchar NOT NULL,
    "file_size" int NOT NULL,
    "exif_vendor" varchar ,
    "exif_model" varchar ,
    "exif_date" timestamp ,
    "upload_date" timestamp DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY ("id")
);