# pylint: disable=redefined-builtin, invalid-name, global-statement, protected-access, method-hidden
# pylint: enable=too-many-lines

"""A drop-in replacement of fileinput module that supports seek() and read()"""

import io
import os
import sys
from fileinput import hook_compressed, hook_encoded, FileInput

__author__ = "Adrian S.-W. Tam"
__author_email__ = "adrian.sw.tam @ gmail.com"
__version__ = "0.1"
__all__ = ["input", "close", "nextfile", "filename", "lineno", "filelineno",
           "fileno", "isfirstline", "isstdin", "FileSnitch", "hook_compressed",
           "hook_encoded"]

# We use our own _state, so all module functions in fileinput accessing it will
# be duplicated here

_state = None

def input(files=None, inplace=False, backup="", *, mode="r", openhook=None):
    """Return an instance of the FileSnitch class, which can be iterated.

    The parameters are passed to the constructor of the FileSnitch class.
    The returned instance, in addition to being an iterator,
    keeps global state for the functions of this module,.
    """
    global _state
    if _state and _state._file:
        raise RuntimeError("input() already active")
    _state = FileSnitch(files, inplace, backup, mode=mode, openhook=openhook)
    return _state

def close():
    """Close the sequence."""
    global _state
    state = _state
    _state = None
    if state:
        state.close()

def nextfile():
    """
    Close the current file so that the next iteration will read the first
    line from the next file (if any); lines not read from the file will
    not count towards the cumulative line count. The filename is not
    changed until after the first line of the next file has been read.
    Before the first line has been read, this function has no effect;
    it cannot be used to skip the first file. After the last line of the
    last file has been read, this function has no effect.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.nextfile()

def filename():
    """
    Return the name of the file currently being read.
    Before the first line has been read, returns None.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.filename()

def lineno():
    """
    Return the cumulative line number of the line that has just been read.
    Before the first line has been read, returns 0. After the last line
    of the last file has been read, returns the line number of that line.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.lineno()

def filelineno():
    """
    Return the line number in the current file. Before the first line
    has been read, returns 0. After the last line of the last file has
    been read, returns the line number of that line within the file.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.filelineno()

def fileno():
    """
    Return the file number of the current file. When no file is currently
    opened, returns -1.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.fileno()

def isfirstline():
    """
    Returns true the line just read is the first line of its file,
    otherwise returns false.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.isfirstline()

def isstdin():
    """
    Returns true if the last line was read from sys.stdin,
    otherwise returns false.
    """
    if not _state:
        raise RuntimeError("no active input()")
    return _state.isstdin()

class FileSnitch(FileInput):
    """Create a file object out of multipart files with support of seek() and read()"""
    def __init__(self, files=None, inplace=False, backup="", *, mode="rb", openhook=None):
        super().__init__(files=files, inplace=inplace, backup=backup, mode=mode, openhook=openhook)
        # make a backup of the init list of files and get file sizes
        self._init_files = self._files[:]
        # fill in file sizes on the fly
        self._file_bytes = [None] * len(self._init_files)
        self._readsetup()

    def close(self):
        super().close()
        self._init_files = ()
        self._file_bytes = []

    def nextfile(self):
        super().nextfile()
        try:
            del self._read  # restore FileSnitch._read
        except AttributeError:
            pass

    def _readsetup(self):
        # common set up routine
        # called by FileSnitch._readline() and FileSnitch._read()
        # copied from FileInput._readline() except no to actually read from file
        if not self._files:
            return

        self._filename = self._files[0]
        self._files = self._files[1:]
        self._startlineno = self.lineno()
        self._filelineno = 0
        self._file = None
        self._isstdin = False
        self._backupfilename = 0
        if self._filename == '-':
            self._filename = '<stdin>'
            if 'b' in self._mode:
                self._file = getattr(sys.stdin, 'buffer', sys.stdin)
            else:
                self._file = sys.stdin
            self._isstdin = True
        else:
            if self._inplace:
                self._backupfilename = (
                    os.fspath(self._filename) + (self._backup or ".bak"))
                try:
                    os.unlink(self._backupfilename)
                except OSError:
                    pass
                # The next few lines may raise OSError
                os.rename(self._filename, self._backupfilename)
                self._file = open(self._backupfilename, self._mode)
                try:
                    perm = os.fstat(self._file.fileno()).st_mode
                except OSError:
                    self._output = open(self._filename, self._write_mode)
                else:
                    mode = os.O_CREAT | os.O_WRONLY | os.O_TRUNC
                    if hasattr(os, 'O_BINARY'):
                        mode |= os.O_BINARY

                    fd = os.open(self._filename, mode, perm)
                    self._output = os.fdopen(fd, self._write_mode)
                    try:
                        os.chmod(self._filename, perm)
                    except OSError:
                        pass
                self._savestdout = sys.stdout
                sys.stdout = self._output
            else:
                # This may raise OSError
                if self._openhook:
                    self._file = self._openhook(self._filename, self._mode)
                else:
                    self._file = open(self._filename, self._mode)
        # check if we can find the file size
        if self._file_bytes[-1-len(self._files)] is not None:
            pass  # file size already known
        elif self._isstdin:
            self._file_bytes[-1-len(self._files)] = -1
        else:
            try:
                pos = self._file.tell()
                if not self._file.seekable():
                    self._file_bytes[-1-len(self._files)] = -1
                else:
                    self._file.seek(0, io.SEEK_END)
                    self._file_bytes[-1-len(self._files)] = self._file.tell()
                    self._file.seek(pos, io.SEEK_SET)
            except OSError:
                pass
        # mask the class-level read functions with instance-level read functions
        self._readline = self._file.readline  # hide FileInput._readline
        self._read = self._file.read  # hide FileInput._read

    def _readline(self):
        # call the parent _readline(), then check what file I am reading
        self._readsetup()
        return self._readline()

    def _read(self, size):
        # call the parent _read(), then check what file I am reading
        self._readsetup()
        return self._read(size)

    def read(self, size=-1):
        # copy from FileInput.readline(), except replace readline with read
        togo = size
        ret = b'' if 'b' in self._mode else ''
        while True:
            chars = self._read(togo)
            if chars:
                if togo != -1:
                    togo -= len(chars)
                ret += chars
                self._filelineno += sum(1 for c in chars if c == '\n')
            if togo == -1 and self._seq() == len(self._init_files)-1:
                return ret
            if not self._file or togo == 0:
                return ret
            self.nextfile()

    def _seq(self):
        # return the seq num of files in the snitch list, 0 as the first file
        return len(self._init_files) - len(self._files) - 1

    def readall(self):
        return self.read()

    def tell(self):
        """return the current position in bytes from the beginning of the first file"""
        return sum(self._file_bytes[:self._seq()]) + self._file.tell()

    def seek(self, offset, wherence=io.SEEK_SET):
        # Consolidate all wherences ito SEEK_SET
        if not self.seekable():
            raise io.UnsupportedOperation
        pos = self.tell()
        if wherence == io.SEEK_CUR:
            # convert SEEK_CUR to SEEK_SET
            offset = pos + offset
            wherence = io.SEEK_SET
        elif wherence == io.SEEK_END:
            # populate file sizes for all files then convert to SEEK_SET
            while self._file_bytes[-1] is None:
                self._readsetup()
            offset = sum(self._file_bytes) + offset
            wherence = io.SEEK_SET
        elif wherence != io.SEEK_SET:
            raise ValueError("Unknown wherence {}".format(wherence))
        try:
            # check which file we should read
            fileseq, runsum = -1, 0
            for fileseq, bytecount in enumerate(self._file_bytes):
                if runsum + bytecount < offset:
                    runsum += bytecount
                else:
                    break
            # check if we should reopen a different file
            if self._seq() != fileseq:
                self._files = self._init_files[fileseq:]
                self._readsetup()
            # seek on the current file
            self._file.seek(offset-runsum, io.SEEK_SET)
        except OSError:
            self.seek(pos, io.SEEK_SET)

    def seekable(self):
        """tell if the file sequence is seekable, only a guess"""
        return all(x != '-' for x in self._init_files)

    def readable(self):
        return True

    def isatty(self):
        return self.seekable()

def _test():
    import getopt
    inplace = False
    backup = False
    opts, args = getopt.getopt(sys.argv[1:], "ib:")
    for o, a in opts:
        if o == '-i': inplace = True
        if o == '-b': backup = a
    for line in input(args, inplace=inplace, backup=backup):
        if line[-1:] == '\n': line = line[:-1]
        if line[-1:] == '\r': line = line[:-1]
        print("%d: %s[%d]%s %s" % (lineno(), filename(), filelineno(),
                                   isfirstline() and "*" or "", line))
    print("%d: %s[%d]" % (lineno(), filename(), filelineno()))

if __name__ == '__main__':
    _test()
