from yaoqi import *

host='http://m.yaoqi520.cc/'
home='shaonvmanhua/'
http = urllib3.PoolManager()

def make_manka_file(arg_path):
    try:
        os.mkdir(arg_path + 'manka')
    except FileExistsError:
        pass
    os.chdir(arg_path + 'manka')
    return


db = DB()
last, m_id, path, update_flag = parse_arg()
if update_flag or len(sys.argv) == 1:
    update_index(host, home, path, db, http)
    print('Index has been updated.')
if len(sys.argv) == 1:
    exit(0)
dic = get_info_by_id(m_id, db)
if not dic:
    print(f'No comic with id {m_id:d} found')
    exit(0)
dic = dic[0]
if os.access(path + 'manka/' + dic['name'] + '.pdf', os.F_OK):
    print('File exist')
    exit(0)
make_manka_file(path)
page = download_manka(dic, db)
if not page:
    print(f'This comic [{dic["name"]}] has been disabled')
    disable = True
else:disable = False
update_after_download(m_id, path, page, disable, db)
