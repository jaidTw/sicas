# sicas

sicas is a SIC/XE assembler written in python, which is also a final project for system programing 2016 course at NTNU.

## About SIC/XE
SIC/XE is a hypothetical computer system introduced in _System Software: An Introduction to Systems Programming_, by Leland Beck.
You may find the specification about it from Google or Wikipedia.

## Usage
```
$ sicas.py [-h] [-o OUTPUT] [-L listing_output] input
```
* `-h`/`--help` : show help meassage.
* `-o OUTPUT`/`--output OUTPUT` : specify output filename to `OUTPUT`.
* `-L listing_output`/`--listing listing_output` : write assembly listing to `listing_output`.

## Features
* One-pass code generation
* support literals
