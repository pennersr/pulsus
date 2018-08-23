import io

from setuptools import find_packages, setup


requires = [
    'werkzeug>=0.14.1',
    'gevent>=1.3.6',
    'requests>=2.19.1',
    'six>=1.11.0'
]

long_description = io.open('README.rst', encoding='utf-8').read()

setup(
    name='pulsus',
    version='1.1.0',
    author="Raymond Penners",
    author_email="raymond.penners@intenct.nl",
    description='Push Notification Service handling Apple Push'
    ' Notification Service (APNS), and Google Cloud Messaging (GCM).',
    long_description=long_description,
    url='https://github.com/pennersr/pulsus',
    keywords='push notifications apns gcm',
    packages=find_packages(),
    install_requires=requires,
    zip_safe=False,
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Environment :: Web Environment',
        'Topic :: Internet',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6'
    ],
)
