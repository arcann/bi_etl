$env:PYTHONPATH=split-path -parent $MyInvocation.MyCommand.Definition
ls Env:\PYTHONPATH