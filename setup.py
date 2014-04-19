from setuptools import setup, find_packages

requires = [
    'applepushnotification==0.1.1',
    'werkzeug>=0.9.4',
    'gevent>=1.0',
    'grequests'
]

setup(
    name='pulsus',
    version='0.1.0',
    author="Raymond Penners",
    author_email="raymond.penners@intenct.nl",
    packages=find_packages(),
    install_requires=requires,
    zip_safe=False,
)
