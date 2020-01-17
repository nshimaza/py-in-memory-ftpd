import logging
import os
import io

from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer
from pyftpdlib.filesystems import FilesystemError

in_memory_folder = {
    'dummy1': b'hello, world',
    'dummy2': b'hello, in memory ftp server',
}

class FakeFileIO(io.BytesIO):
    def __init__(self, folder, name, content=b''):
        self._folder = folder
        self._name = name
        io.BytesIO.__init__(self, content)

    def close(self):
        self._folder[self._name] = io.BytesIO.getvalue(self)
        io.BytesIO.close(self)

    def name(self):
        return self.name

class InMemoryFilesystem:
    def __init__(self, root, cmd_channel):
        self.folder = in_memory_folder
        self.cmd_channel = cmd_channel

    @property
    def root(self):
        return '/'

    @root.setter
    def root(self, path):
        pass

    @property
    def cwd(self):
        return '/'

    @cwd.setter
    def cwd(self, path):
        pass

    def chdir(self, path):
        pass
    
    def listdir(self, path):
        return list(self.folder.keys())

    def ftp2fs(self, ftppath):
        return ftppath

    def fs2ftp(self, fspath):
        return fspath


    def validpath(self, path):
        if path == '/':
            return True
        return (path == os.path.basename(path))

    def open(self, filename, mode):
        if 'w' in mode:
            return FakeFileIO(self.folder, filename)
        if 'r' in mode:
            v = self.folder.get(filename)
            if v == None:
                raise FilesystemError("file not found")
            f = FakeFileIO(self.folder, filename, v)
            return FakeFileIO(self.folder, filename, v)

    def isdir(self, path):
        return True if path == '/' else False

    def format_list(self, path, listing, ignore_err=True):
        for basename in listing:
            size = len(self.folder[basename])
            line = "-rw-rw-rw- 1 root root %8s Jan 1 00:00 %s\r\n" % (size, basename)
            yield line.encode('utf8', self.cmd_channel.unicode_errors)

def main():
    # Instantiate a dummy authorizer for managing 'virtual' users
    authorizer = DummyAuthorizer()

    # Define a new user having full r/w permissions and a read-only
    # anonymous user
    authorizer.add_user('user', '123', '.', perm='elradfmwMT')
    authorizer.add_anonymous(os.getcwd())

    # Instantiate FTP handler class
    handler = FTPHandler
    handler.authorizer = authorizer
    handler.abstracted_fs = InMemoryFilesystem

    # Define a customized banner (string returned when client connects)
    handler.banner = "pyftpdlib based ftpd ready."

    # Specify a masquerade address and the range of ports to use for
    # passive connections.  Decomment in case you're behind a NAT.
    #handler.masquerade_address = '151.25.42.11'
    #handler.passive_ports = range(60000, 65535)

    # Instantiate FTP server class and listen on 0.0.0.0:2121
    address = ('', 2121)
    server = FTPServer(address, handler)

    # set a limit for connections
    server.max_cons = 256
    server.max_cons_per_ip = 5

    logging.basicConfig(level=logging.DEBUG)

    # start ftp server
    server.serve_forever()

if __name__ == '__main__':
    main()