import dbfunc
# import uuid
import hashlib

KILOBYTES = 1024
chunksize = KILOBYTES


def deduplicate(chunkdb, file, fileid, size):
    return fsp(chunkdb, file, fileid, size)


def fsp(chunkdb, file, fileid, filesize):
    part_count = 0
    part_list = []
    new_part = 0
    # if filesize < 10*KILOBYTES:
    #     chunksize = KILOBYTES
    # else:
    #     chunksize = filesize // 10 // KILOBYTES*KILOBYTES
    while True:
        flag = 1
        data = file.read(chunksize)
        if not data:
            break
        part_count += 1
        fingerprint = get_fingerprint(data)
        if check_fingerprint(chunkdb, fingerprint, fileid) is True:
            size = len(data)
            new_part += 1
            chunk = dbfunc.Chunk(data, [fileid], size)
            dbfunc.insert(chunkdb, fingerprint.encode(), chunk)
            flag = 0
        part_list.append(fingerprint)

    detail = {'part_state': 1, 'part_size': chunksize,
              'part_count': part_count, 'part_list': part_list,
              'new_part': new_part, 'flag': flag}
    return detail


def get_fingerprint(data):
    m = hashlib.md5()
    m.update(data)
    return m.hexdigest()


def check_fingerprint(chunkdb, fingerprint, fileid):
    res = dbfunc.search(chunkdb, fingerprint.encode())
    if res is False:
        return True
    else:
        res.file_list.append(fileid)
        dbfunc.update(chunkdb, fingerprint.encode(), res)
        return False
