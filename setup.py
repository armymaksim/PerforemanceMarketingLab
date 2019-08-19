from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='image_manager',
    version='0.0.1',
    install_requires=['cchardet',
                      'aiodns',
                      'aiohttp',
                      'asyncpg',
                      'asyncpgsa',
                      'Pillow',
                      'jinja2',
                      'sqlalchemy'
                      ],
    include_package_data=True,
    packages=find_packages(),
    long_description=open(join(dirname(__file__), 'README.md')).read(),
    url='https://github.com/armymaksim/VoltMobi',
    license=open(join(dirname(__file__), 'LICENSE')).read(),
    author='army.maksim',
    author_email='army.maksim@gmail.com',
    description='Web service Image_manager',
    entry_points={
       'console_scripts':
           ['run_image_manager = image_manager.server:run']
       },
)