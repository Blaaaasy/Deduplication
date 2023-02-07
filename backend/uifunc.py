import dbfunc
import func
import uuid
import time

CLIPBRD = ''


def refresh(pathdb, path):
    directory = dbfunc.search(pathdb, path)
    if directory is False:
        print('KeyError')
    else:
        return directory.file_list


def edit_dirname(pathdb, filedb, dirid, name):
    file = dbfunc.search(filedb, dirid)
    if file is False:
        print('KeyError')
    else:
        file.name = name
    dbfunc.update(filedb, dirid, file)
    path = dbfunc.search(pathdb, dirid)
    if path is False:
        print('KeyError')
    else:
        path.name = name
    dbfunc.update(pathdb, dirid, path)


def new_dir(pathdb, filedb, name, path):
    dirid = uuid.uuid4()
    mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

    if path == 'home':
        file = dbfunc.File(name, path, -1, 0, 0, 0, 0, mtime)
        dbfunc.insert(filedb, dirid.bytes, file)
        newpath = dbfunc.Path(name, [], path)
        dbfunc.insert(pathdb, dirid.bytes, newpath)
        oldpath = dbfunc.search(pathdb, path.encode())
        oldpath.file_list.append(dirid)
        dbfunc.update(pathdb, path.encode(), oldpath)
    else:
        file = dbfunc.File(name, path, -1, 0, 0, 0, 0, mtime)
        dbfunc.insert(filedb, dirid.bytes, file)
        newpath = dbfunc.Path(name, [], path)
        path = uuid.UUID(path)
        dbfunc.insert(pathdb, dirid.bytes, newpath)
        oldpath = dbfunc.search(pathdb, path.bytes)
        oldpath.file_list.append(dirid)
        dbfunc.update(pathdb, path.bytes, oldpath)


def del_file(pathdb, filedb, chunkdb, fileid):
    file = dbfunc.search(filedb, fileid.bytes)
    if file is False:
        print('KeyError')
    elif file.size == -1:
        path = dbfunc.search(pathdb, fileid.bytes)
        if path is False:
            print('KeyError')
        else:
            for item in path.file_list:         # 递归
                del_file(pathdb, filedb, chunkdb, item)

            pathid = dbfunc.search(pathdb, fileid.bytes).path
            if pathid == "home":
                path = dbfunc.search(pathdb, pathid.encode())
                path.file_list.remove(fileid)
                dbfunc.update(pathdb, pathid.encode(), path)
            else:
                path = dbfunc.search(pathdb, pathid.bytes)
                path.file_list.remove(fileid)
                dbfunc.update(pathdb, pathid.bytes, path)

            dbfunc.delete(filedb, fileid.bytes)
            dbfunc.delete(pathdb, fileid.bytes)
    else:
        file = dbfunc.search(filedb, fileid.bytes)
        pathid = file.path
        if pathid == "home":
            path = dbfunc.search(pathdb, pathid.encode())
            path.file_list.remove(fileid)
            dbfunc.update(pathdb, pathid.encode(), path)
        else:
            path = dbfunc.search(pathdb, pathid.bytes)
            path.file_list.remove(fileid)
            dbfunc.update(pathdb, pathid.bytes, path)
        # 目录文件列表更新

        chunks = file.part_list
        for item in chunks:
            chunk = dbfunc.search(chunkdb, item.encode())
            chunk.file_list.remove(fileid)
            if len(chunk.file_list) == 0:
                dbfunc.delete(chunkdb, item.encode())
        # 分块更新

        dbfunc.delete(filedb, fileid.bytes)


def copy_dir(dirid):
    global CLIPBRD
    CLIPBRD = dirid


def paste_dir(pathdb, filedb, newpath):
    global CLIPBRD
    if CLIPBRD != '':
        dirid = CLIPBRD
        file = dbfunc.search(filedb, dirid)
        if file is False:
            print('KeyError')
        else:
            oldpath = dbfunc.search(pathdb, file.path)
            if oldpath is False:
                print('KeyError')
            else:
                oldpath.file_list.remove(dirid)
                dbfunc.update(pathdb, file.path, oldpath)
                file.path = newpath
                dbfunc.update(filedb, dirid, file)
                path = dbfunc.search(pathdb, newpath)
                if path is False:
                    print('KeyError')
                else:
                    path.file_list.append(dirid)
                    dbfunc.update(pathdb, newpath, path)
                    directory = dbfunc.search(pathdb, dirid)
                    if directory is False:
                        print('KeyError')
                    else:
                        directory.path = newpath
                        dbfunc.update(pathdb, dirid, directory)


def open_dir(pathdb, dirid):
    refresh(pathdb, dirid)


def get_dir_size(pathdb, filedb, dirid):
    size = 0
    path = dbfunc.search(pathdb, dirid.bytes)
    if path is False:
        print('KeyError')
    else:
        for item in path.file_list:         # 递归
            file = dbfunc.search(filedb, item.bytes)
            if file is False:
                print('KeyError')
            elif file.size == -1:
                s = get_dir_size(pathdb, filedb, item.bytes)
                size += s
            else:
                s = get_file_size(filedb, item.bytes)
                if s is False:
                    print('KeyError')
                else:
                    size += get_file_size(filedb, item.bytes)
        return size


def get_file_size(filedb, fileid):
    file = dbfunc.search(filedb, fileid)
    if file is False:
        print('KeyError')
        return False
    else:
        size = file.size
        return size


def edit_filename(filedb, fileid, newname):
    file = dbfunc.search(filedb, fileid)
    if file is False:
        print('KeyError')
    else:
        file.name = newname
        dbfunc.update(filedb, fileid, file)


# updated
def new_file(pathdb, filedb, chunkdb, filename, file, path):     # 涉及重复数据删除
    fileid = uuid.uuid4()
    size = get_size(file)
    file.seek(0)
    detail = func.deduplicate(chunkdb, file, fileid, size)
    mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    if path == 'home':
        pathinfo = dbfunc.search(pathdb, path.encode())
        newfile = dbfunc.File(filename, path, size,
                              detail['part_state'], detail['part_size'],
                              detail['part_count'], detail['part_list'], mtime)
        pathinfo.file_list.append(fileid)
        dbfunc.update(pathdb, path.encode(), pathinfo)
    else:
        path = uuid.UUID(path)
        newfile = dbfunc.File(filename, path, size,
                              detail['part_state'], detail['part_size'],
                              detail['part_count'], detail['part_list'], mtime)
        pathinfo = dbfunc.search(pathdb, path.bytes)
        pathinfo.file_list.append(fileid)
        dbfunc.update(pathdb, path.bytes, pathinfo)

    dbfunc.insert(filedb, fileid.bytes, newfile)
    res = {
        'count': detail['part_count'], 'new_part': detail['new_part'],
        'size': size, 'flag': detail['flag'], 'part_size': detail['part_size']
    }
    return res


def get_size(file):
    file.seek(0, 2)
    size = file.tell()
    print(size)
    return size


def copy_file(fileid):
    global CLIPBRD
    CLIPBRD = fileid


def paste_file(pathdb, filedb, newpath):
    global CLIPBRD
    if CLIPBRD != '':
        fileid = CLIPBRD
        file = dbfunc.search(filedb, fileid)
        if file is False:
            print('KeyError')
        else:
            oldpath = dbfunc.search(pathdb, file.path)
            if oldpath is False:
                print('KeyError')
            else:
                oldpath.file_list.remove(fileid)
                dbfunc.update(pathdb, file.path, oldpath)
                file.path = newpath
                dbfunc.update(filedb, fileid, file)
                path = dbfunc.search(pathdb, newpath)
                if path is False:
                    print('KeyError')
                else:
                    path.file_list.append(fileid)
                    dbfunc.update(pathdb, newpath, path)


def open_file(filename):
    pass


def get_file_detail(filedb, fileid):
    file = dbfunc.search(filedb, fileid)
    if file is False:
        print('KeyError')
    else:
        detail = {'name': file.name, 'path': file.path, 'size': file.size,
                  'part_state': file.part_state, 'part_size': file.part_size,
                  'part_count': file.part_count, 'mtime': file.mtime}
        return detail


def get_file(filedb, chunkdb, fileid):
    fileid = uuid.UUID(fileid)
    file = dbfunc.search(filedb, fileid.bytes)
    chunks = file.part_list
    res = b''
    for item in chunks:
        chunk = dbfunc.search(chunkdb, item.encode())
        res = res + chunk.data
    r = open("../download/" + file.name, "wb")
    r.write(res)
    r.close()


def file_relationship(pathdb, filedb, chunkdb, pathid, relationship, count):
    if pathid == 'home':
        path = dbfunc.search(pathdb, pathid.encode())
    else:
        path = dbfunc.search(pathdb, pathid.bytes)
    for item in path.file_list:
        file = dbfunc.search(filedb, item.bytes)
        if file.size == -1:
            file_relationship(pathdb, filedb, chunkdb,
                              item, relationship, count)
        else:
            relationship['filenodes'].update(
                {
                    str(item): {'name': file.name,
                                'size': file.size,
                                'part_state': '定长分块' if file.part_state else '变长分块',
                                'part_count': file.part_count, 'mtime': file.mtime}
                }
            )
            for chunkfp in file.part_list:
                chunkrelationship = chunk_relationship(
                    chunkdb, item, chunkfp, relationship, count)
                relationship = chunkrelationship[0]
                count = chunkrelationship[1]
    return relationship


def chunk_relationship(chunkdb, fileid, chunkfp, relationship, count):
    chunk = dbfunc.search(chunkdb, chunkfp.encode())
    relationship['edges'].update(
        {
            count: {
                'src': fileid,
                'dst': chunkfp,
            }
        }
    )
    relationship['chunknodes'].update(
        {
            chunkfp: {
                'size': chunk.size
            }
        }
    )

    count += 1
    return (relationship, count)
