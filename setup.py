from setuptools import setup, find_packages

setup(name='apple_search_ads',
      version='0.2.5',
      description='Python wrapper for Apple Search Ads APIs',
      url='https://github.com/aovlexus/apple-searchads-api',
      author='Luca Giacomel forked by Aleksnadr Usov',
      author_email='lg@bendingspoons.com, aovlexus@gmail.com',
      license='MIT',
      packages=find_packages(),
      install_requires=[
          "python-decouple",
          "pandas",
          "requests",
          "tqdm",
      ],
      zip_safe=False)
