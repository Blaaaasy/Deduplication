import leveldb
import pickle
import time


class Path:
    def __init__(self, name, file_list, path):
        self.name = name                # 路径名
        self.file_list = file_list      # 路径下文件id列表
        self.path = path                # 路径所在的上一级路径id


class File:
    def __init__(self, name, path, size, part_state,
                 part_size, part_count, part_list, mtime):
        self.name = name                # 文件名
        self.path = path                # 文件所在路径id
        self.size = size                # 若为-1是文件夹
        self.part_state = part_state
        self.part_size = part_size
        self.part_count = part_count
        self.part_list = part_list
        self.mtime = mtime


class Chunk:
    def __init__(self, data, file_list, size):
        self.data = data
        self.file_list = file_list
        self.size = size


def initialize(username):
    pathdb = leveldb.LevelDB("./db/users/" + username+"/pathdb")
    filedb = leveldb.LevelDB("./db/users/" + username+"/filedb")
    chunkdb = leveldb.LevelDB("./db/users/" + username+"/chunkdb")
    if not search(pathdb, "home".encode()):
        mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        file = File("home", "root", -1, 0, 0, 0, 0, mtime)
        insert(filedb, "home".encode(), file)
        path = Path("home", [], "root")
        insert(pathdb, "home".encode(), path)
    return [pathdb, filedb, chunkdb]


def userdb_initialize():
    userdb = leveldb.LevelDB("./db/userdb")
    return userdb


def insert(db, key, value):
    db.Put(key, pickle.dumps(value))


def delete(db, key):
    db.Delete(key)


def update(db, key, value):
    db.Put(key, pickle.dumps(value))


def search(db, key):
    try:
        value = db.Get(key)
    except KeyError:
        return False
    else:
        return pickle.loads(value)


def display(db):
    for key, value in db.RangeIter():
        print(key.decode(), pickle.loads(value))


# def get_dir(db, path):
#     content = []
#     for key, value in db.RangeIter():
#         if path.encode() == key:
#             content.append(value.decode())
#     return content


# hello = "hello"
# hello2 = hello.encode()
# world = "world"
# world2 = world.encode()
# db.Put(hello2, world2)
# print(db.Get(hello2).decode())
# display(db)
# print("Insert 3 records.")
# insert(db, '1', '1')
# insert(db, '2', '2')
# insert(db, '3', '3')
# display(db)

# print("Delete the record where sid = 1.")
# delete(db, b'1')
# display(db)

# print("Update the record where sid = 3.")
# update(db, b'3', b"Mark")
# display(db)

# print("Get the name of student whose sid = 3.")
# name = search(db, b'3')
# print(name)

# os.system("rm -rf db")
