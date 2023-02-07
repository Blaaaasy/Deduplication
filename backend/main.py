
# import os
# import cgi
# import cgitb
# import json
from flask import Flask, request, render_template, send_file

import uifunc
import dbfunc
import uuid
app = Flask(__name__, static_url_path='')

userdb = dbfunc.userdb_initialize()
pathdb = None
filedb = None
chunkdb = None
PATH = "home"

# cgitb.enable()
# form = cgi.FieldStorage()
# ID = form.getvalue("ID")
# NAME = form.getvalue("NAME")
# result = {"ID": ID, "NAME": NAME}
# # todo something

# print("Content-Type: application/json\n\n")
# print(json.dumps(result))


# def test(params):
#     ID = params.getvalue("ID")
#     NAME = params.getvalue("NAME")
#     result = {"ID": ID, "NAME": NAME}
#     return result

@app.route('/upload', methods=['POST'])
def upload():
    file = request.files['file']
    filename = request.form.get("name")
    global PATH
    res = uifunc.new_file(pathdb, filedb, chunkdb, filename, file, PATH)
    file.close()
    return res


@app.route('/getfile', methods=['GET'])
def getfile():
    global PATH
    if PATH == 'home':
        dir = dbfunc.search(pathdb, PATH.encode())
    else:
        new_path = uuid.UUID(PATH)
        dir = dbfunc.search(pathdb, new_path.bytes)
    pathname = dir.name
    filelist = dir.file_list
    path = dir.path
    files = []
    for item in filelist:
        file = dbfunc.search(filedb, item.bytes)
        files.append({
            "fileid": item,
            "filename": file.name,
            "filepath": file.path,
            "filesize": file.size,
            "partstate": file.part_state,
            "partsize": file.part_size,
            "partcount": file.part_count,
            "partlist": file.part_list,
            "mtime": file.mtime
        })
    res = {
        "pathname": pathname,
        "files": files,
        "path": path
    }
    return res


@app.route('/newdir', methods=['POST'])
def newdir():
    global PATH
    dirname = request.form.get("dirname")
    print(dirname)
    print(type(dirname))
    uifunc.new_dir(pathdb, filedb, dirname, PATH)
    return "success"


@app.route('/openfolder', methods=['GET'])
def openfolder():
    global PATH
    newpath = request.args.get("pathid")
    PATH = newpath
    return "success"


@app.route('/back', methods=["GET"])
def back():
    global PATH
    if PATH == 'home':
        return "success"
    path = uuid.UUID(PATH)
    dir = dbfunc.search(pathdb, path.bytes)
    PATH = dir.path
    return "success"


@app.route('/getfullpathname', methods=["GET"])
def getfullpathname():
    global PATH
    if PATH == 'home':
        return '/home'
    path = uuid.UUID(PATH)
    res = ''
    while True:
        dir = dbfunc.search(pathdb, path.bytes)
        res = '/' + dir.name + res
        path = dir.path
        if path == 'home':
            res = '/home' + res
            break
        else:
            path = uuid.UUID(path)

    return res


@app.route('/delete', methods=["POST"])
def delete():
    fileid = request.form.get('fileid')
    fileid = uuid.UUID(fileid)
    uifunc.del_file(pathdb, filedb, chunkdb, fileid)
    return 'success'


@app.route('/download', methods=["GET"])
def download():
    fileid = request.args.get("fileid")
    uifunc.get_file(filedb, chunkdb, fileid)

    return 'success'


@app.route('/getrelationship', methods=["GET"])
def getrelationship():
    relationship = {
        "filenodes": {
        },
        "chunknodes": {
        },
        "edges": {
        }
    }
    relationship = uifunc.file_relationship(pathdb, filedb, chunkdb,
                                            'home', relationship, 1)
    return relationship


@app.route('/login', methods=["POST"])
def login():
    global USERNAME
    USERNAME = str(request.form.get('name'))
    password = str(request.form.get('password'))
    code = 1 if dbfunc.search(userdb, USERNAME.encode()) == password else 0
    if code:
        global pathdb, filedb, chunkdb
        dblist = dbfunc.initialize(USERNAME)
        pathdb = dblist[0]
        filedb = dblist[1]
        chunkdb = dblist[2]

        token = str(uuid.uuid4())
        return {'code': code, 'token': token}
    else:
        return {'code': code, 'msg': "用户名或密码错误"}


@app.route('/register', methods=["POST"])
def register():
    username = str(request.form.get('name'))
    password = str(request.form.get('password'))
    code = 0 if dbfunc.search(userdb, username.encode()) else 1
    if code:

        dbfunc.insert(userdb, username.encode(), password)
        return {'code': code, 'msg': "注册成功"}
    else:
        return {'code': code, 'msg': "用户名重复，注册失败"}


@app.route('/getsize', methods=["GET"])
def getsize():
    pathid = request.args.get("pathid")
    pathid = uuid.UUID(pathid)
    size = uifunc.get_dir_size(pathdb, filedb, pathid)
    return size


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8081)

# db = dbfunc.initialize('pathdb')

# # files1 = dbfunc.Path(1, ['1', '2', '3'], 1)
# # files2 = dbfunc.Path(2, ['4', '5', '6'], 2)
# # dbfunc.insert(db, '1', files1)
# # dbfunc.insert(db, '1', files2)

# # dbfunc.display(db)
# # print(files1.file_name_list)
# # tmp = dbfunc.pickle.dumps(files1)
# # print(dbfunc.pickle.loads(tmp).file_name_list)

# dbfunc.insert(db, '1', 1)
# print(dbfunc.search(db, '1'))
# try:
#     dbfunc.search(db, '2')
# except KeyError:
#     print("no")

# os.system("rm -rf pathdb")
