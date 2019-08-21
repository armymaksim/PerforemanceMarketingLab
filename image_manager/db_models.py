import sqlalchemy as sa
from sqlalchemy import Integer, String, DateTime, text

Images = sa.Table(
    'images', sa.MetaData(),
    sa.Column('id', Integer, primary_key=True),
    sa.Column('user_image_name', String),
    sa.Column('original_file_name', String, nullable=False),
    sa.Column('image_md5',
              String,
              nullable=False,
              unique=True,
              index=True),
    sa.Column('file_type', String, nullable=False),
    sa.Column('file_size', Integer, nullable=False),
    sa.Column('exif_vendor', String),
    sa.Column('exif_model', String),
    sa.Column('exif_date', DateTime),
    sa.Column('upload_date',
              DateTime,
              server_default=text('current_timestamp')))
