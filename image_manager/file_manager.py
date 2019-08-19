import os
from _md5 import md5
from datetime import datetime

import PIL
from PIL import Image, ExifTags


class Image_manager():

    __slots__ = (
        'file',
        'user_image_name',
        'file_size',
        'file_type',
        'original_file_name',
        'image_md5',
        'vendor',
        'model',
        'exif_date',
        'image',
        'thumb',
        'id',
        'upload_date',
        'upload_path'
    )
    def __init__(self, **kwargs) -> None:
        self.file = kwargs.get('file', None)
        self.user_image_name = kwargs.get('user_image_name', None)
        self.file_size = kwargs.get('file_size', 0)
        self.file_type = kwargs.get('file_type')
        self.original_file_name = kwargs.get('original_file_name')
        self.image_md5 = kwargs.get('image_md5', None)
        print(self.image_md5)
        if not self.image_md5:
            if not self.file:
                raise Exception('Невозможно инициализировать инстанс - недостаточно данных')
            else:
                self.image_md5 = self.get_file_name()
        print(self.image_md5)
        self.vendor = kwargs.get('vendor', None)
        self.model = kwargs.get('model', None)
        self.exif_date = kwargs.get('exif_date', None)
        self.image = None
        self.thumb = None
        self.id = kwargs.get('id', None)
        self.upload_date = kwargs.get('upload_date') or datetime.now()



    def get_file_name(self):
        self.file.seek(0)
        f_data = self.file.read()
        self.file.seek(0)
        return md5(f_data).hexdigest()

    def get_exif_data(self):
        self.image._getexif()
        exif = self.image._getexif()
        if exif:
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in exif.items()
                if k in ExifTags.TAGS
            }
        else:
            exif = {}
        self.vendor = exif.get('Make', None)
        self.model = exif.get('Model', None)
        self.exif_date = exif.get('DateTimeOriginal', None)
        if self.exif_date:
            self.exif_date = datetime.strptime(self.exif_date,
                      '%Y:%m:%d %H:%M:%S')

    def get_file_path(self, file_name, upload_path, mimetype='jpg', file_type='source'):
        return '/'.join([upload_path,
                         file_type,
                         file_name[0:3],
                         file_name[3:6],
                         f'{file_name}.{mimetype}']
                        )

    def write_files(self, upload_path):
        source_path = self.get_file_path(self.image_md5,
                                         upload_path,
                                         mimetype=self.file_type)
        thumb_path = self.get_file_path(self.image_md5,
                                        upload_path,
                                        mimetype=self.file_type,
                                        file_type='thumbs')
        self.check_or_create_dirs(source_path)
        self.check_or_create_dirs(thumb_path)
        self.image.save(source_path)
        self.thumb.save(thumb_path)

    def check_or_create_dirs(self, source_path):
        base_path = os.path.dirname(source_path)
        if os.path.exists(base_path):
            return
        else:
            os.makedirs(base_path, mode=0o710)

    def load_image(self):
        self.file.seek(0)
        self.image = Image.open(self.file)


    def make_thumb(self):
        index = max(self.image.size)/150
        self.thumb = self.image.resize((
            int(self.image.size[0]//index),
            int(self.image.size[1]//index)
        ))

    def delete_image(self, upload_path):
        source_path = self.get_file_path(self.image_md5,
                                         upload_path,
                                         mimetype=self.file_type)
        thumb_path = self.get_file_path(self.image_md5,
                                        upload_path,
                                        mimetype=self.file_type,
                                        file_type='thumbs')
        os.unlink(source_path)
        os.unlink(thumb_path)

    def as_dict(self):
        return {
            'name': self.user_image_name,
            'original_file_name': self.original_file_name,
            'image_md5': self.image_md5,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'exif_vendor': self.vendor,
            'exif_model': self.model,
            'exif_date': self.exif_date,
            'upload_date': self.upload_date or datetime.now()
        }

    def serialize(self):
        tmp = self.as_dict()
        format_date = lambda x: x.strftime('%Y-%m-%d %H:%M') if x else ''
        tmp['upload_date'] = format_date(tmp['upload_date'])
        tmp['exif_date'] = format_date(tmp['exif_date'])
        tmp['prview_url'] = self.get_file_path(tmp['image_md5'],
                                               '/upload',
                                               mimetype=tmp['file_type'],
                                               file_type='thumbs')
        return tmp

    @classmethod
    def init_from_db_row(cls, row):
        return cls(**{k:v for k, v in row.items() if k in cls.__slots__})


