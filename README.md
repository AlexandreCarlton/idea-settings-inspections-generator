# idea-settings-inspection-generator

This is a small package used to generate Inspections support for IntelliJ IDEA
in [idea-settings](https://github.com/AlexandreCarlton/idea-settings).

To run this, create a [virtualenv](https://virtualenv.pypa.io/en/latest/), drop
into it and install this package:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

Then, run from the checkout of IDEA-settings:
```bash
generate-inspections
```
