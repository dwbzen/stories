from setuptools import find_packages, setup
import os

ROOT_DIR = os.path.dirname(__file__)
SOURCE_DIR = os.path.join(ROOT_DIR)

#
# the README file content is the long description
#
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

requirements = [
]

setup(
    name="stories",
    version="0.1",
    author="Donald Bacon",
    author_email="dwbzen@gmail.com",
    description="Stories Game game engine and server",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dwbzen/stories.git",
    packages=find_packages(exclude=["tests","docs"]),
    data_files=[('resources', ['resources/gameParameters.json', 'resources/story_cards_template.json' ]
                 )],
    install_requires=requirements,
    license="MIT",
    namespace_packages=[],
    include_package_data=False,
    zip_safe=False,
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
		"Intended Audience :: Developers",
        "Environment :: Console",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3.10",
    ],
    python_requires='>=3.10',
    keywords="Stories Game",
    maintainer='Donald Bacon',
    maintainer_email='dwbzen@gmail.com'
)
