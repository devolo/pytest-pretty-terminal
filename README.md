# pytest-pretty-terminal

This [pytest](http://pytest.org) plugin makes the terminal output prettier and more verbose. Beside a bit formatting you will see the doc string and the parametrization of a test case printed to the terminal. Live logging is enabled by default.

## System requirements

Defining the system requirements with exact versions typically is difficult. But there is a tested environment:

* Linux
* Python 3.8.12
* pip 21.2.4
* pytest 5.2.0

Other versions and even other operating systems might work. Feel free to tell us about your experience.

## Versioning

In our versioning we follow [Semantic Versioning](https://semver.org/).

## Installing for usage

The Python Package Index takes care for you. Just use pip.

```bash
python -m pip install pytest-pretty-terminal
```

## Installing for development

First, you need to get the sources.

```bash
git clone git@github.com:devolo/pytest-pretty-terminal.git
```

Then you need to take care of the requirements.

```bash
cd pytest-pretty-terminal
python setup.py install
```

## Usage

To activate the pretty output, you have to start pytest with the pretty option. Otherwise, the plugin is skipped.

```bash
pytest --pretty
```

## Compatibility with other pytest plugins

This plugin should not interfere with other plugins. In case of using [pytest-xdist](https://github.com/pytest-dev/pytest-xdist), you will lose live logging, as xdist uses stdin/stdout for communicating with its workers.
