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
    version='1.0.2',
    author='Evgen Kytonin',
    license='MIT',
    keywords=['nlp', 'ukraine', 'address', 'research', 'parsing'],
    url='https://github.com/martinjack/uaddress',
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