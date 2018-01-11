import tempfile
import zlib
from io import BytesIO
from itertools import chain, repeat, takewhile
from typing import Iterator, Iterable
from contextlib import suppress

from fn import F
from django.conf import settings
from django.core.files import uploadhandler, uploadedfile


CHUNKSIZE = 16 * 2**10  # 16KB
GZIP_SIGNATURE = b'\x1f\x8b\x08'
GZIP_OFFSETS = [zlib.MAX_WBITS, -zlib.MAX_WBITS, zlib.MAX_WBITS | 16]


class FileSizeLimitReached(RuntimeError):
    pass


# TODO consider adding more compression formats
def stream(handle: BytesIO) -> Iterator[bytes]:
    """
    Yield chunks (decompressed, if necessary) of CHUNKSIZE bytes
    :param handle: a file-like byte stream with `.read(size)`
    :return:
    :raises zlib.error: failed to decompress a gzipped stream (most likely,
    none of the header offsets worked).
    """
    def chunk(handle_: BytesIO) -> Iterator[bytes]:
        return takewhile(bool, (handle_.read(CHUNKSIZE) for _ in repeat(None)))

    def decompress(head_: bytes, handle_: BytesIO) -> Iterator[bytes]:
        # try several most common offsets
        offsets = [zlib.MAX_WBITS, -zlib.MAX_WBITS, zlib.MAX_WBITS | 16]
        for offset in offsets:
            with suppress(zlib.error):
                dec = zlib.decompressobj(offset)
                first = dec.decompress(head_)
                return (F(chunk) >> (map, dec.decompress) >> (chain, [first]) >>
                        (filter, bool))(handle_)
        raise zlib.error('failed decompression')

    head: bytes = handle.read(CHUNKSIZE)
    iscompressed = head.startswith(GZIP_SIGNATURE)
    return decompress(head, handle) if iscompressed else chunk(handle)


class SizeLimitedUploadedFile(uploadedfile.UploadedFile):
    """
    A file uploaded to a temporary location (i.e. stream-to-disk).
    """
    def __init__(self, name, content_type, size, charset, content_type_extra=None):
        def genext(fname: str) -> str:
            _, *ext = fname.split('.', 1)
            return f'.{".".join([settings.UPLOAD_EXT_SUFFIX, *ext])}'

        file = tempfile.NamedTemporaryFile(
            buffering=settings.FILE_UPLOAD_MAX_MEMORY_SIZE, delete=False,
            suffix=genext(name), dir=settings.FILE_UPLOAD_TEMP_DIR
        )
        super().__init__(file, file.name, content_type, 0, charset, content_type_extra)
        self.error = None

    def write(self, chunk: bytes) -> int:
        """
        :param chunk: bytes to write
        :return: the number of bytes written
        :raises FileSizeLimitReached: if file size reached
        """
        newsize = self.size + len(chunk)
        if newsize <= settings.FILE_UPLOAD_MAX_MEMORY_SIZE:
            self.file.write(chunk)
            self.size = newsize
            return len(chunk)
        self.error = 'submission size limit exceeded'
        raise FileSizeLimitReached

    def writelines(self, chunks: Iterable[bytes]):
        """
        :param chunks: bytes to write
        :raises FileSizeLimitReached: if file size reached
        """
        for chunk in chunks:
            self.write(chunk)


class FileUploadHandler(uploadhandler.FileUploadHandler):
    """
    File upload handler to stream uploads into memory (used for small files).
    """

    def new_file(self, *args, **kwargs):
        """
        Create the file object to append to as data are coming in.
        """
        super().new_file(*args, **kwargs)
        self.file = SizeLimitedUploadedFile(
            self.file_name, self.content_type, 0,
            self.charset, self.content_type_extra
        )

    def receive_data_chunk(self, raw_data, start):
        if self.file.error is None:
            with suppress(FileSizeLimitReached):
                self.file.write(raw_data)

    def file_complete(self, file_size):
        self.file.seek(0)
        return self.file


if __name__ == '__main__':
    raise RuntimeError
