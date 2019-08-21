import os
from _md5 import md5
from datetime import datetime
from PIL import Image, ExifTags


class ImageManager:
    """Класс работы с изображениями и вводом-выводом
    """
    __slots__ = (
        'file',
        'user_image_name',
        'file_size',
        'file_type',
        'original_file_name',
        'image_md5',
        'exif_vendor',
        'exif_model',
        'exif_date',
        'image',
        'thumb',
        'id',
        'upload_date',
        'upload_path'
    )

    def __init__(self, **kwargs) -> None:
        """
        Иницыализируем класс управления изображением
        Минимальный набор данных - данные строки из БД
        Или
                {
                    'file': file: BytesIO,
                    'file_size': file_size: int,
                    'file_type': file_type: str,
                    'original_file_name': original_file_name,
                }

        :param kwargs:
        """
        self.file = kwargs.get('file', None)
        self.user_image_name = kwargs.get('user_image_name', None)
        self.file_size = kwargs.get('file_size', 0)
        self.file_type = kwargs.get('file_type')
        self.original_file_name = kwargs.get('original_file_name')
        self.image_md5 = kwargs.get('image_md5', None)
        if not self.image_md5:
            if not self.file:
                raise Exception('Невозможно инициализировать инстанс'
                                ' - недостаточно данных')
            else:
                self.image_md5 = self.get_file_name()
        self.exif_vendor = kwargs.get('exif_vendor', None)
        self.exif_model = kwargs.get('exif_model', None)
        self.exif_date = kwargs.get('exif_date', None)
        self.image = None
        self.thumb = None
        self.id = kwargs.get('id', None)
        self.upload_date = kwargs.get('upload_date') or datetime.now()

    def get_file_name(self):
        """Формируем системное имя файла из md5 суммы самого файла
        :return: str
        """
        self.file.seek(0)
        f_data = self.file.read()
        self.file.seek(0)
        return md5(f_data).hexdigest()

    def get_exif_data(self):
        """Пробуем получить данные exif

        :return: None
        """
        # Мой не лучший вариант
        # exif = self.image._getexif()
        # if exif:
        #     exif = {
        #         ExifTags.TAGS[k]: v
        #         for k, v in exif.items()
        #         if k in ExifTags.TAGS
        #     }
        # else:
        #     exif = {}
        exif = self.image.info.get('parsed_exif', {})
        self.exif_vendor = exif.get('Make', None)
        self.exif_model = exif.get('Model', None)
        self.exif_date = exif.get('DateTimeOriginal', None)
        if self.exif_date:
            self.exif_date = datetime.strptime(
                self.exif_date,
                '%Y:%m:%d %H:%M:%S'
            )

    def get_file_path(
            self,
            file_name,
            upload_path,
            mimetype='jpg',
            file_type='source'
    ):
        """
            Формируем путь до файла
        :param file_name: md5 сумма файла
        :param upload_path: Корневой каталог для загрузки файлов
        :param mimetype: расширение файла
        :param file_type: ТИп изображения 'source|thumbs'
        :return:
        """
        return '/'.join([upload_path,
                         file_type,
                         file_name[0:3],
                         file_name[3:6],
                         f'{file_name}.{mimetype}']
                        )

    def write_files(self, upload_path) -> None:
        """
            Запись фалов на диск
        :param upload_path:  Корневой каталог для загрузки файлов
        :return: None
        """
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
        """
        Создание промежуточных каталогов для хранения файлов
        :param source_path:
        :return:
        """
        base_path = os.path.dirname(source_path)
        if os.path.exists(base_path):
            return
        else:
            os.makedirs(base_path, mode=0o766)

    def load_image(self):
        """
        Превращаем набор байт в изображение и
        тут же проверяем, что это изображение.
        :return:
        """
        self.file.seek(0)
        self.image = Image.open(self.file)

    def make_thumb(self) -> None:
        """
        Создаем уменьшенную копию изображения
        :return:
        """
        index = max(self.image.size)/150
        self.thumb = self.image.resize((
            int(self.image.size[0]//index),
            int(self.image.size[1]//index)
        ))

    def delete_image(self, upload_path):
        """
        Удаляем изображение с диска
        :param upload_path:
        :return:
        """
        source_path = self.get_file_path(self.image_md5,
                                         upload_path,
                                         mimetype=self.file_type)
        thumb_path = self.get_file_path(self.image_md5,
                                        upload_path,
                                        mimetype=self.file_type,
                                        file_type='thumbs')
        os.unlink(source_path)
        os.unlink(thumb_path)

    def as_dict(self) -> dict:
        """
        Сериализуем для записи в БД
        :return: dict
        """
        return {
            'user_image_name': self.user_image_name,
            'original_file_name': self.original_file_name,
            'image_md5': self.image_md5,
            'file_type': self.file_type,
            'file_size': self.file_size,
            'exif_vendor': self.exif_vendor,
            'exif_model': self.exif_model,
            'exif_date': self.exif_date,
            'upload_date': self.upload_date or datetime.now()
        }

    def serialize(self) -> dict:
        """
        Сериализуем для формирования HTML
        :return: dict
        """
        tmp = {
            key: getattr(self, key, '')
            for key in self.__slots__
            if getattr(self, key, '')
        }

        def format_date(x: datetime) -> str:
            if x:
                return x.strftime('%Y-%m-%d %H:%M')
            return ''

        tmp['upload_date'] = format_date(tmp['upload_date'])
        tmp['exif_date'] = format_date(tmp.get('exif_date', None))
        tmp['prview_url'] = self.get_file_path(tmp['image_md5'],
                                               '/upload',
                                               mimetype=tmp['file_type'],
                                               file_type='thumbs')
        return tmp

    @classmethod
    def init_from_db_row(cls, row):
        """
            Инициализируем класс на основе данных БД
        :param row: строка из БД
        :return:
        """
        return cls(**{k: v for k, v in row.items() if k in cls.__slots__})
