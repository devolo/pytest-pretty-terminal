from setuptools import setup

setup(name="pytest-pretty-terminal",
      packages=["pytest_pretty_terminal"],
      description="pytest plugin for generating prettier terminal output",
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      use_scm_version=True,
      url="https://github.com/devolo/pytest-adaptavist",
      author="Stephan Steinberg, Markus Bong, Guido Schmitz",
      author_email="markus.bong@devolo.de, guido.schmitz@devolo.de",
      license="MIT",
      entry_points={"pytest11": ["pretty-terminal = pytest_pretty_terminal"]},
      platforms="any",
      python_requires=">=3.8",
      install_requires=["pytest>=3.4.1"],
      keywords="python pytest adaptavist kanoah tm4j jira test testmanagement report",
      classifiers=[
          "Framework :: Pytest",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: MIT License",
          "Operating System :: OS Independent",
          "Programming Language :: Python",
          "Programming Language :: Python :: 3",
          "Topic :: Software Development :: Quality Assurance",
          "Topic :: Software Development :: Testing",
          "Topic :: Utilities",
          "Topic :: Software Development :: Libraries :: Python Modules"
      ])
