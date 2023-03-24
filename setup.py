from setuptools import setup, find_packages
import os


def parse_requirements(file):
    return sorted(set(
        line.partition('#')[0].strip()
        for line in open(os.path.join(os.path.dirname(__file__), file))
    ) - set(''))


setup(
	name='SARRA-Py',
	python_requires='>=3.8,<3.10',
	description='SARRA-Py',
	version = '0.0.1',
	author='Jérémy LAVARENNE (@codename5281)',
	packages=find_packages(where='src'),
	install_requires=parse_requirements('requirements.txt'),
	package_dir={'': 'src'}
	)