from setuptools import setup

setup(name="pytest-pretty-terminal",
      packages=["pytest_pretty_terminal"],
      description="pytest plugin for generating test execution results within Jira Test Management (tm4j)",
      long_description=open("README.md").read(),
      long_description_content_type="text/markdown",
      version="1.0.0",
      url="https://github.com/devolo/pytest-adaptavist",
      author="Stephan Steinberg, Markus Bong, Guido Schmitz",
      author_email="stephan.steinberg@devolo.de",
      license="MIT",
      entry_points={"pytest11": ["pretty-terminal = pytest_pretty_terminal"]},
      platforms="any",
      python_requires=">=3.6",
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
