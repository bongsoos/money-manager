from setuptools import setup, find_packages
import money_manager

NAME = "money_manager"
DESCRIPTION = "Money manager software"
LONG_DESCRIPTION = "Money manager software"
AUTHOR = "Bongsoo Suh"
AUTHOR_EMAIL = "bongsoo.suh@gmail.com"
LICENSE = "MIT"
URL = "https://github.com/bongsoos/money-manager/"
REQUIREMENTS = "requirements.txt"

setup(name=NAME,
      version=money_manager.__version__,
      description=DESCRIPTION,
      long_description=LONG_DESCRIPTION,
      author=AUTHOR,
      author_email=AUTHOR_EMAIL,
      license=LICENSE,
      url=URL,
      packages=find_packages(),
      install_requires=[i.strip() for i in open(REQUIREMENTS).readlines()],
      zip_safe=False)

