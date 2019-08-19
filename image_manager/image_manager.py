import os
from _md5 import md5
from datetime import datetime

import PIL
from io import BytesIO

from PIL import Image


class Image_manager():

    def __init__(self,
                 file=BytesIO(),
                 file_size=0,
                 file_type='',
                 original_file_name='',
                 user_image_name=''
                 ) -> None:
        self.file = file
        self.user_image_name = user_image_name
        self.file_size = file_size
        self.file_type = file_type
        self.original_file_name = original_file_name
        self.filename = self.get_file_name()
        self.vendor = None
        self.model = None
        self.exif_date = None
        self.image = None
        self.thumb = None



    def get_file_name(self):
        self.file.seek(0)
        f_data = self.file.read()
        self.file.seek(0)
        self.filename = md5(f_data).hexdigest()

    def get_exif_data(self):
        self.image._getexif()
        exif = self.image._getexif()
        if exif:
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in exif.items()
                if k in PIL.ExifTags.TAGS
            }
        else:
            exif={}
        self.vendor = exif.get('Make', None)
        self.model = exif.get('Model', None)
        self.exif_date = exif.get('DateTimeOriginal', None)
        if self.exif_date:
            self.exif_date = datetime.strptime(self.exif_date,
                      '%Y:%m:%d %H:%M:%S')

    def get_file_path(self, file_name, mimetype='jpg', file_type='source'):
        return '/'.join([self.request.app.upload_path,
                         file_type,
                         file_name[0:3],
                         file_name[3:6],
                         f'{file_name}.{mimetype}']
                        )

    def write_files(self):
        source_path = self.get_file_path(self.filename,
                           mimetype=self.file_type)
        thumb_path = self.get_file_path(self.filename,
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
    def delete_image(self):
        source_path = self.get_file_path(self.image_md5,
                                         mimetype=self.file_type)
        thumb_path = self.get_file_path(self.image_md5,
                                        mimetype=self.file_type,
                                        file_type='thumbs')
        os.unlink(source_path)
        os.unlink(thumb_path)

    def as_dict(self):
        return {
            'name': self.user_image_name,
            'original_file_name': self.original_file_name,
            'image_md5': self.filename,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'exif_vendor': self.vendor,
            'exif_model': self.model,
            'exif_date': self.exif_date,
            'upload_date': datetime.now()
        }