import aiohttp
import asyncpgsa
from io import BytesIO
from aiohttp import web
from aiohttp.web_response import Response
from sqlalchemy import text, func, select
from image_manager.db_models import Images
from image_manager.file_manager import Image_manager


class ImageView(web.View):

    async def get(self):
        return await self.render_page()

    async def post(self):
        form_data = await self.fetch_form_data()
        IM = Image_manager(**form_data)
        if await self.exists(IM.image_md5):
            return await self.render_page(reason='Данное изображение уже существует!!!')
        try:
            IM.load_image()
        except IOError:
            return await self.render_page(reason='Загружаемый файл не является изображением!!!')
        IM.make_thumb()
        IM.get_exif_data()
        try:
            IM.write_files(self.request.app.upload_path)
        except:
            return await self.render_page(reason=' Не удалось сохранить файл')
        try:
            await self.save_to_db(IM.as_dict())
        except:
            IM.delete_image(self.request.app.upload_path)
            return await self.render_page(reason=' Не удалось сохранить запись в БД')
        raise web.HTTPFound('/')

    async def delete(self):
        data = await self.request.json()
        try:
            id = int(data['id'])
        except:
            return Response(body='Неверный идентификатор', status=400, headers={'Content-Type': 'text/html'})
        query = Images.select().where(Images.c.id == id)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            res = await conn.fetchrow(query_string, *params)
        if not res:
            return Response(body='Изображение не найдено', status=404, headers={'Content-Type': 'text/html'})
        img = Image_manager.init_from_db_row(res)
        query = Images.delete().where(Images.c.id == id)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            res = await conn.fetchrow(query_string, *params)
        img.delete_image(self.request.app.upload_path)
        return Response(body='OK', status=200, headers={'Content-Type': 'text/html'})

    def fetch_query_data(self) -> dict:
        """
        Выборка параметров пагинации из запроса (limit, offset)/
        все остальное отбрасываем.
        Параметры сортировки можно реализовать здесь же.
        :return: dict
        """
        legal_keys = ['limit', 'offset']
        try:
            data = {key: int(self.request.query.getone(key, 0))
                for key in self.request.query.keys()
                if key in legal_keys}
        finally:
            if not data:
                data = dict(zip(legal_keys, [30, 0]))

        return data


    async def fetch_form_data(self):
        original_file_name = None
        file_type = None
        user_image_name=None
        file_size = 0
        file = BytesIO()
        reader = await self.request.multipart()
        while True:
            field = await reader.next()
            if field is None:
                break
            if field.name == 'name':
                user_image_name = await field.read(decode=True)
                user_image_name = user_image_name.decode()
            elif field.name == 'file':
                original_file_name = field.filename
                file_type = field.filename.split('.')[-1]
                while True:
                    chunk = await field.read_chunk()  # 8192 bytes by default.
                    if not chunk:
                        break
                    file_size += len(chunk)
                    file.write(chunk)
            else:
                continue
        assert file and file_size and file_type
        res = {
            'file':file,
            'file_size':file_size,
            'file_type':file_type,
            'original_file_name':original_file_name,
            'user_image_name':user_image_name
        }
        return res

    async def exists(self, filename):
        query = select([func.count(text('*'))]).select_from(Images.select().where(Images.c.image_md5==filename).alias())
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            if await conn.fetchval(query_string, *params)>0:
                return True
        return False

    async def save_to_db(self, image_object):
        for key, val in image_object.items():
            col = getattr(Images.c, key, None)
            if col is not None:
                if col.type.python_type!=type(val) and val:
                    image_object[key] = col.type.python_type(val)
        res = None
        query = Images.insert().values(**image_object)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            res = await conn.fetchrow(query_string, *params)


    async def render_page(self, reason=None):
        l_o = self.fetch_query_data()
        limit = l_o.get('limit')
        offset = l_o.get('offset')
        order = 'desc',
        by = 'upload_date'
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
                tmp = Image_manager.init_from_db_row(row)
                res.append(tmp.serialize())
        template = self.request.app.jinja.get_template('index.html')
        data = await template.render_async(res=res, reason=reason)
        return Response(body=data, status=200, headers={'Content-Type':'text/html'})





