# quantum

#### (De)Activating VENV
In order to __activate__ the virtual env, you should run these 3 commands from inside the `ibm` directory:
1) `python -m venv .venv`
2) `source .venv/bin/activate`
__Tip:__ You can now make sure the virtual env is activated using `which python` or `which pip`.
3) `pip install -r requirements.txt`

In order to __deactivate__, just run:
`deactivate nondestructive`

* If faces error `deactivate: command not found`, use the `deactivate` function from inside `.venv/bin/activate` script.
* Afterwards you can entirely remove the venv by `rm -rf .venv`.
* If still not working, first make sure `$PATH` variable is set to default `bin` folders and then manually unset these variables:
1) unset VIRTUAL_ENV
2) unset VIRTUAL_ENV_PROMPT
3) `export PS1=`[PS1 var without (.venv) prefeix]

#### Build Latex
use this line:
`latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex` so all output files will be collected tp a `build` subfolder.