from setuptools import setup, find_packages

requires = [
    'applepushnotification==0.1.1',
    'gevent==0.13.7'
]

setup(
    name='pulsus',
    version='0.0.0',
    author="Raymond Penners",
    author_email="raymond.penners@intenct.nl",
    packages=find_packages(),
    install_requires=requires,
    zip_safe=False,
)
