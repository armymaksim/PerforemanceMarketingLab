import os
import aiohttp
import asyncpgsa
import PIL.ExifTags
from _md5 import md5
from PIL import Image
from io import BytesIO
from aiohttp import web
from datetime import datetime
from aiohttp.web_request import Request
from aiohttp.web_response import Response
from sqlalchemy import text, func, select
from image_manager.db_models import Images



class ImageView(web.View):

    def __init__(self, request: Request) -> None:
        super().__init__(request)
        self.file = None
        self.vendor = None
        self.model = None
        self.exif_date = None
        self.user_image_name = None
        self.original_file_name = None
        self.file_size = None
        self.image = None
        self.thumb = None
        self.filename = None
        self.file_type = None


    async def get(self):
        data = {key: self.request.query.getone(key) for key in self.request.query.keys()}
        return await self.render_page()

    async def post(self):
        return await self.save_new_image()

    async def delete(self):
        return await self.delete_image()

    async def save_new_image(self):
        data = {key: self.request.query.getone(key) for key in self.request.query.keys()}
        await self.fetch_form_data()
        self.get_file_name()
        if await self.exists():
            raise aiohttp.web.HTTPBadRequest(reason='Данное изображение уже существует!!!')
        try:
            self.is_image()
        except IOError:
            raise aiohttp.web.HTTPBadRequest(reason='Загружаемый файл не является изображением!!!')
        self.make_thumb()
        self.get_exif_data()
        await self.save_to_db()
        self.write_files()

        return await self.render_page()


    async def delete_image(self):
        data = await self.request.json()
        try:
            id = int(data['id'])
        except:
            return Response(body='Неверный идентификатор', status=400, headers={'Content-Type':'text/html'})
        query = Images.select().where(Images.c.id==id)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            res = await conn.fetchrow(query_string, *params)
        if not res:
            return Response(body='Изображение не найдено', status=404, headers={'Content-Type': 'text/html'})
        source_path = self.get_file_path(res.get('image_md5'),
                                         mimetype=res.get('file_type'))
        thumb_path = self.get_file_path(res.get('image_md5'),
                                        mimetype=res.get('file_type'),
                                         file_type='thumbs')
        os.unlink(source_path)
        os.unlink(thumb_path)
        query = Images.delete().where(Images.c.id == id)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            res = await conn.fetchrow(query_string, *params)
        return Response(body='OK', status=200, headers={'Content-Type':'text/html'})

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



    async def fetch_form_data(self):
        reader = await self.request.multipart()
        field = await reader.next()
        assert field.name == 'name'
        user_image_name = await field.read(decode=True)
        self.user_image_name = user_image_name.decode()
        field = await reader.next()
        assert field.name == 'file'
        self.original_file_name = field.filename
        self.file_type = field.filename.split('.')[-1]

        # You cannot rely on Content-Length if transfer is chunked.
        self.file_size = 0
        self.file = BytesIO()
        while True:
            chunk = await field.read_chunk()  # 8192 bytes by default.
            if not chunk:
                break
            self.file_size += len(chunk)
            self.file.write(chunk)

    async def exists(self):
        query = select([func.count(text('*'))]).select_from(Images.select().where(Images.c.image_md5==self.filename).alias())
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            if await conn.fetchval(query_string, *params)>0:
                raise aiohttp.web.HTTPConflict(reason='Данное изображение уже существует!!!')
        return False

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

    def get_file_path(self, file_name, mimetype='jpg', file_type='source'):
        return '/'.join([self.request.app.upload_path,
                         file_type,
                         file_name[0:3],
                         file_name[3:6],
                         f'{file_name}.{mimetype}']
                        )

    async def save_to_db(self):
        new_row = {
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
        for key, val in new_row.items():
            col = getattr(Images.c, key, None)
            if col is not None:
                if col.type.python_type!=type(val) and val:
                    new_row[key] = col.type.python_type(val)
        res = None
        query = Images.insert().values(**new_row)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            res = await conn.fetchrow(query_string, *params)


    async def render_page(self,
                          limit=30,
                          offset=0,
                          order='desc',
                          by='upload_date'):
        orderby = getattr(Images.c, by, None)
        if orderby is None:
            orderby = Images.c.upload_date
        sort = orderby.desc()
        if order != 'desc':
            sort = orderby.asc()
        query = Images.select()\
            .order_by(sort)\
            .limit(limit)\
            .offset(limit*offset)
        query_string, params = asyncpgsa.compile_query(query)
        res = []
        async with self.request.app.db.acquire() as conn:
            for row in await conn.fetch(query_string, *params):
                tmp = dict(row.items())
                tmp['exif_date']=tmp['exif_date'].strftime('%Y-%m-%d %H:%M') if tmp['exif_date'] else ''
                tmp['upload_date']=tmp['upload_date'].strftime('%Y-%m-%d %H:%M') if tmp['upload_date'] else ''
                tmp['prview_url']= self.get_file_path(tmp['image_md5'],
                                                      mimetype=tmp['file_type'],
                                                      file_type='thumbs')
                res.append(tmp)


        template = self.request.app.jinja.get_template('index.html')
        data = await template.render_async(res=res)
        return Response(body=data, status=200, headers={'Content-Type':'text/html'})

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

