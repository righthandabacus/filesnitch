# FileSnitch

[![PyPi Version](https://img.shields.io/pypi/v/filesnitch.svg)](https://pypi.python.org/pypi/filesnitch/)
[![PyPi Licence](https://img.shields.io/pypi/l/filesnitch.svg)](https://pypi.python.org/pypi/filesnitch/)
[![PyPi Python Versions](https://img.shields.io/pypi/pyversions/filesnitch.svg)](https://pypi.python.org/pypi/filesnitch/)
[![PyPi Downloads](http://pepy.tech/badge/filesnitch)](http://pepy.tech/project/filesnitch)

This is a module allows you to concatenate multiple files on the fly and
present as a single read-only file object.

## Introduction

In Python Standard Libarary, there is a module `fileinput` which provides
similar function but useful only for text input, supporting only the
`readline()` function. That module does not support rewinding as well.

This module, `filesnitch` allows one to `seek()` and `read()` files. A typical
use case is a multipart zip file. For example, we have multiple files:
`foo.zip.001`, `foo.zip.002`, `foo.zip.003`. To extract some file from it, we
should combine them with the following shell command

    cat foo.zip.001 foo.zip.002 foo.zip.003 > foo.zip

Afterwards we can use it, for example using `zipfile` module in Python

```python
import zipfile
with zipfile.ZipFile("foo.zip") as zipfp:
    for zipinfo in zipfp.infolist():
        print("File {} size {}".format(zipinfo.filename, zipinfo.file_size))
```

With this module, we can avoid creating a combined file but use the chunks directly:

```python
import zipfile
import filesnitch

with filesnitch.input(files=["foo.zip.001", "foo.zip.002", "foo.zip.003"]) as bigfile:
    with zipfile.ZipFile(bigfile) as zipfp:
        for zipinfo in zipfp.infolist():
            print("File {} size {}".format(zipinfo.filename, zipinfo.file_size))
```

Generally, multiple files can be concatenated as a file object and use in
everywhere that a read-only file object is expected.

## Getting the latest code

To get the latest code using git, simply type:

    git clone git://github.com/righthandabacus/filesnitch.git

## Install

You can use pip to install joblib:

    pip install filesnitch

from any directory or:

    python setup.py install

from the source directory.

## Dependencies

`filesnitch` has no dependencies besides standard Python libraries. Python 3 required.

## Examples

Create a file object of multiple files, tell the total file size, and read the last 20 bytes:

```python
import io
import filesnitch

filenames = ["foo.zip.001", "foo.zip.002", "foo.zip.003"]
fileobj = filesnitch.FileSnitch(filenames)  # by default in binary mode
fileobj.seek(0, io.SEEK_END)
filesize = fileobj.tell()
fileobj.seek(-20, io.SEEK_END)
lastbytes = fileobj.read(20)
print("Total file size {}. Last 20 bytes:\n{}".format(filesize, repr(lastbytes))
```

Above we use the standard function `seek()` and `tell()` to move within the
concatenated file as if the file object is a standard
[`io.IOBase`](https://docs.python.org/3/library/io.html#i-o-base-classes). The
`read()` call accepts the size argument for the number of bytes to read. If no
size argument provided, it will read until EOF.


Read all files in one shot as a large blob:

```python
import io
import filesnitch

filenames = ["foo.zip.001", "foo.zip.002", "foo.zip.003"]
with filesnitch.FileSnitch(filenames) as fileobj:
    blob = fileobj.readall()
```

The `readall()` call is same as `read()` without argument, both will read until
EOF. `FileSnitch` class can be used as a context manager.

We can also pass in file objects into `FileSnitch()` as long as those file
objects supports seek and read correctly. An example is as follows: The
`diabetic-retinopathy-detection.zip` file is a 83GB zip file from
[Kaggle](https://www.kaggle.com/c/diabetic-retinopathy-detection/data) (with
correct tools, we can download it using the command `kaggle competitions
download -c diabetic-retinopathy-detection`). In it, there are seven files,
named `test.zip.001` to `test.zip.007`, that are parts of a zip file of images.
To extract one image from it without deflating any zip file onto disk, we can
do the following:

```python
import zipfile
import filesnitch

# this call to zipfile needs `allowZip64=True` because of the size is huge
with zipfile.ZipFile("diabetic-retinopathy-detection.zip", allowZip64=True) as zip83G:
    # open each file inside the 83GB zip file, then snitch them up as one file object
    zipparts = [zip83G.open(f, mode="r") for f in [
        "test.zip.001",
        "test.zip.002",
        "test.zip.003",
        "test.zip.004",
        "test.zip.005",
        "test.zip.006",
        "test.zip.007",
    ]]
    with filesnitch.input(files=zipparts, mode='rb') as testzip:
        # use the snitched file as another zip file, then read a file inside it
        with zipfile.ZipFile(testzip) as zfp:
            with zfp.open("test/10000_right.jpeg", mode="r") as fp:
                with open("10000_right.jpeg", "wb") as outfp:
                    outfp.write(fp.read())
```
