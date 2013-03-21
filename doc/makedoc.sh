#!/bin/sh
rm biosignalml.*.rst
sphinx-apidoc -T  -o . ../biosignalml

make clean html
