from setuptools import setup, find_packages

setup(name='search_ads',
      version='0.2.2',
      description='Python wrapper for Apple Search Ads APIs',
      url='https://github.com/BendingSpoons/searchads-api',
      author='Luca Giacomel',
      author_email='lg@bendingspoons.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          "python-decouple",
          "pandas",
          "requests",
          "tqdm",
      ],
      zip_safe=False)
