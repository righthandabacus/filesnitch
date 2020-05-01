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

## API

FileSnitch class derived from [FileInput
class](https://docs.python.org/3/library/fileinput.html) and the methods
filename(), fileno(), lineno(), filelineno(), isfirstline(), isstdin(),
nextfile() and close() are same as the parent class. Contrary to FileInput,
files opened by FileSnitch by default are in mode `'rb'` instead of `'r'`.
Random access and readline() should not be mixed and it is not suggested to use
readline() call with FileSnitch.

### `FileSnitch.read(size=-1)`

Read the specified number of bytes/characters or until the end of the
concatenated file. Calling `read()` with no argument or with `size=-1` will
read until the concatenated file is exhaustted. Depends on the mode that the
files are opened, it returns a `str` or `bytes` object.

### `FileSnitch.readall()`

Same as `read(size=-1)`. It read from the current position until the end of the
concatenated file.

### `FileSnitch.tell()`

Returns the current position, in number of bytes from the beginning of the
concatenated file.

### `FileSnitch.seek(offset, wherence=io.SEEK_SET)`

Reset the current position in the concatenated file. It has the same syntax as
the `seek()` function in other [file
object](https://docs.python.org/3/tutorial/inputoutput.html#methods-of-file-objects).

### `FileSnitch.seekable()`

Returns a boolean for whether the concatenated file is seekable. It is a best
effort guess for whether all the component files are seekable.

### `FileSnitch.readable()`

Always returns `True`.

### `FileSnitch.isatty()`

Same as `FileSnitch.seekable()`
