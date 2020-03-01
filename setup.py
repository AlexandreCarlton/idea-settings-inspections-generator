from setuptools import setup, find_packages

setup(
    name='inspection_generator',
    description='Generates inspections for IDEA-settings',
    author='Alexandre Carlton',
    packages=find_packages(),
    install_requires=[
        'jinja2',
        'jproperties',
        'lxml'
    ],
    entry_points='''
        [console_scripts]
        generate-inspections=inspection_generator.generate:main
    '''
)
