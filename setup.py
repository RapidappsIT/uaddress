try:
    from setuptools import setup
except ImportError:
    raise ImportError(
        "setuptools module required, please go to "
        "https://pypi.python.org/pypi/setuptools and follow the instructions "
        "for installing setuptools"
    )

setup(
    name='uaddress',
    packages=['uaddress'],
    description='Ukrainian address parser',
    version='1.0.4',
    author='Evgen Kytonin',
    author_email='killfess@gmail.com',
    license='MIT',
    keywords=['nlp', 'ukraine', 'address', 'research', 'parsing'],
    url='https://github.com/RapidappsIT/uaddress',
    package_data={'uaddress': ['uaddr.crfsuite']},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering',
        'Topic :: Scientific/Engineering :: Information Analysis'
    ]
)