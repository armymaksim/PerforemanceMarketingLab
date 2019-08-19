# VoltMobi
Тестовое задание
create table images
(
	id serial not null
		constraint images_pkey
			primary key,
	user_image_name varchar not null,
	original_file_name varchar not null,
	image_md5 varchar not null,
	file_type varchar not null,
	file_size integer not null,
	exif_vendor varchar,
	exif_model varchar,
	exif_date timestamp,
	upload_date timestamp default CURRENT_TIMESTAMP
)
;

create unique index images_image_md5_uindex
	on images (image_md5)
;

