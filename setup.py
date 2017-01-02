from setuptools import setup, find_packages

DESCRIPTION = """
AccessPanel is a module to enhance accessibility though a set of
classes derived from wx.
""".strip()

setup(
    name = "accesspanel",
    version = "0.12",
    packages = find_packages(),
    install_requires = [],
    description = DESCRIPTION,
    author = 'Vincent Le Goff',
    author_email = 'vincent.legoff.srs@gmail.com',
    url = 'https://github.com/vlegoff/accesspanel',
    keywords = ['accessibility'],
)
