import asyncpgsa
from io import BytesIO
from aiohttp import web
from aiohttp.web_response import Response
from sqlalchemy import text, func, select
from image_manager.db_models import Images
from image_manager.file_manager import Image_manager


class ImageView(web.View):
    """ Класс содержит в себе обработчики запросов типа GET, POST, DELETE
    и ряд вспомогательных функций
    """
    async def get(self):
        """
        Обработчик запросов типа GET
        Рендерит страницу и возвращает пользователю
        :return: Response
        """
        return await self.render_page()

    async def post(self):
        """
                Обработчик запросов типа POST
                Запрос должен содержать данные формы типа multipart/form-data
                Берет на себя обработку входных данных
                Проверяет тип файла
                Проверяет существование изображения
                Создает тумбы картинки
                Сохраняет изображения
                Сохраняет данные о изображении в БД
                :return: Response
                """
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
        """
        На вход принимает запрос,содержащий в себе JSON-объект вида
        {"id":<int id>}, где <int id> - идентификатор изображения в БД
        Проверяет существование записи в БД
        Удаляет запись в БД
        Удаляет картинки из хранилища
        :return: Response
        """
        data = await self.request.json()
        try:
            id = int(data['id'])
        except:
            return Response(body='Неверный идентификатор', status=400, headers={'Content-Type': 'text/html'})
        query = Images.select().where(Images.c.id == id)
        query_string, params = asyncpgsa.compile_query(query)
        try:
            async with self.request.app.db.acquire() as conn:
                res = await conn.fetchrow(query_string, *params)
        except:
            return Response(body='Ошибка при получении записи из БД', status=500, headers={'Content-Type': 'text/html'})
        if not res:
            return Response(body='Изображение не найдено', status=404, headers={'Content-Type': 'text/html'})
        img = Image_manager.init_from_db_row(res)
        query = Images.delete().where(Images.c.id == id)
        query_string, params = asyncpgsa.compile_query(query)
        try:
            async with self.request.app.db.acquire() as conn:
                await conn.fetchrow(query_string, *params)
        except:
            return Response(body='Ошибка при удалении записи в БД', status=500, headers={'Content-Type': 'text/html'})
        try:
            img.delete_image(self.request.app.upload_path)
        except:
            return Response(body='Ошибка при удалении файла', status=500, headers={'Content-Type': 'text/html'})
        return Response(body='OK', status=200, headers={'Content-Type': 'text/html'})

    def fetch_query_data(self) -> dict:
        """
        Выборка параметров пагинации из запроса (limit, offset)
        все остальное отбрасываем.
        Параметры сортировки можно реализовать здесь же.
        :return: dict
        """
        legal_keys = ['limit', 'offset']
        data = None
        try:
            data = {key: int(self.request.query.getone(key, 0))
                for key in self.request.query.keys()
                if key in legal_keys}
        finally:
            if not data:
                data = dict(zip(legal_keys, [30, 0]))
        return data


    async def fetch_form_data(self):
        """
            Функция разбора данных формы
            Возврящает первичную информацию о
            загружаемом файле и сам файл
        :return: dict
        """
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
            'file': file,
            'file_size': file_size,
            'file_type': file_type,
            'original_file_name': original_file_name,
            'user_image_name': user_image_name
        }
        return res

    async def exists(self, filename):
        """
        Про веряет наличие записей о файле в БД
        :param filename: Имя файла (md5_sum от содержимого файла)
        :return: bool
        """
        query = select([func.count(text('*'))])\
            .select_from(Images.select()\
            .where(Images.c.image_md5==filename)\
            .alias())
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            if await conn.fetchval(query_string, *params)>0:
                return True
        return False

    async def save_to_db(self, image_object: dict) -> None:
        """
        Создает новую запись в БД
        :param image_object: словарь с описанием нового изображения
        :return: None
        """
        for key, val in image_object.items():
            col = getattr(Images.c, key, None)
            if col is not None:
                if col.type.python_type!=type(val) and val:
                    image_object[key] = col.type.python_type(val)
        res = None
        query = Images.insert().values(**image_object)
        query_string, params = asyncpgsa.compile_query(query)
        async with self.request.app.db.acquire() as conn:
            await conn.fetchrow(query_string, *params)


    async def render_page(self, reason=''):
        """
        Получет список изображений из БД и формирует html код страницы

        :param reason: Текстовое описание причины ошибки
        :return: Response
        """
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





