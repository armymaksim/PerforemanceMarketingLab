from setuptools import setup, find_packages
from os.path import join, dirname

setup(
    name='universal_worker_web',
    version='0.3.1',
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
    url='https://gitlab.skytracking.ru/STDM_Components/universal_worker_web',
    license='TBD',
    author='mkozlov',
    author_email='mkozlov@skytracking.ru',
    description='Web wrapper for instance',
    entry_points={
       'console_scripts':
           ['universal_worker_web = universal_worker_web.run_ws:run']
       },
)