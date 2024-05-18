from setuptools import setup, find_packages

setup(
  name="onboard",
  version="0.1.0",
  description="A simple tool to onboard user accounts over ssh",
  url="https://github.com/ais-ucla/onboard",
  author="Christopher Milan",
  author_email="chrismilan@ucla.edu",
  packages=find_packages(include=['onboard', 'onboard.*']),
  entry_points={
    "console_scripts": [
      "onboard=onboard:onboard",
      "onboardd=onboard:daemon",
      "onboardctl=onboard:onboardctl"
    ],
  },
  data_files=[('lib/systemd/system', ['onboard.service'])],
)

