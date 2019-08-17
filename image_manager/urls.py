import os
from _md5 import md5
from io import BytesIO
import PIL.ExifTags

import aiohttp
from PIL import Image
from aiohttp import web
from datetime import datetime

from aiohttp.web_request import Request

class ImageView(web.View):

    def __init__(self, request: Request) -> None:
        super().__init__(request)
        self.db = self.request.app.db
        self.file = None


    async def get(self):
        data = {key: self.request.query.getone(key) for key in self.request.query.keys()}
        return await self.get_table(**data)

    async def post(self):
        return await self.save_new_image()

    async def delete(self):
        return await self.delete_image()

    async def save_new_image(self):
        data = {key: self.request.query.getone(key) for key in self.request.query.keys()}
        await self.fetch_form_data()
        self.get_file_name()
        if self.exists():
            raise aiohttp.web.HTTPBadRequest('Данное изображение уже существует!!!')
        try:
            self.is_image()
        except IOError:
            raise aiohttp.web.HTTPBadRequest('Загружаемый файл не является изображением!!!')
        self.make_thumb()
        self.get_exif_data()
        self.save_to_db()
        return


    def delete_image(self, id):
        pass

    def get_exif_data(self, image_data):
        self.image._getexif()
        exif = {
            PIL.ExifTags.TAGS[k]: v
            for k, v in .items()
            if k in PIL.ExifTags.TAGS
        }
        self.vendor = None
        self.model = None
        self.exif_date = None


    async def fetch_form_data(self):
        reader = await self.request.multipart()
        field = await reader.next()
        assert field.name == 'name'
        self.user_image_name = await field.read(decode=True)

        field = await reader.next()
        assert field.name == 'image'
        self.original_file_name = field.filename
        # You cannot rely on Content-Length if transfer is chunked.
        self.file_size = 0
        self.file = BytesIO()
        while True:
            chunk = await field.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            self.file_size += len(chunk)
            self.file.write(chunk)

    def exists(self):
    #Не сохранять уже существующие фото.
    # Проверять наличие дубликата файла и выдавать ошибку в случае обнаружения.
        pass

    def is_image(self):
        self.file.seek(0)
        self.image = Image.open(self.file)


    def make_thumb(self):
        index = max(self.image.size)/150
        self.thumb = self.image.resize((
            int(self.image.size[0]//index),
            int(self.image.size[1]//index)
        ))


    def get_file_name(self):
        self.file.seek(0)
        f_data = self.file.read()
        self.file.seek(0)
        self.filename = md5(f_data).hexdigest()

    def get_file_path(self, file_name, file_type='source'):
        return '/'.join([self.request.app.upload_path,
                         file_type,
                         file_name[0:3],
                         file_name[3:6]])

    async def save_to_db(self):
        new_row = {
            'name': self.
            'original_file_name': self.
            'image_md5': self.
            'file_path': self.
            'file_size': self.
            'exif_vendor': self.
            'exif_model': self.
            'exif_date': self.
            'upload_date': self.
        }