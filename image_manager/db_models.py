import sqlalchemy as sa
from sqlalchemy import Integer, String, DateTime, text

Images = sa.Table(
        'images', sa.MetaData(),
        sa.Column('id', Integer, primary_key=True),
        sa.Column('name', String, nullable=False),
        sa.Column('original_file_name', String, nullable=False),
        sa.Column('image_md5', String, nullable=False, unique=True, index=True),
        sa.Column('file_path', String, nullable=False),
        sa.Column('file_size', Integer, nullable=False),
        sa.Column('exif_vendor', String, nullable=False),
        sa.Column('exif_model', String, nullable=False),
        sa.Column('exif_date', DateTime, server_default=text('current_timestamp')),
        sa.Column('upload_date', DateTime, server_default=text('current_timestamp'))
    )