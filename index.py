# -*- coding=utf-8 -*-
import os, re, pyodbc, datetime, decimal, cdecimal, shutil, sqlite3
from flask import Flask, request, session, g, redirect, url_for, \
     abort, render_template, flash, json
from contextlib import closing
from datetime import date
from time import strftime, localtime
import calendar, xlsxwriter
import numpy as np
from Crypto.Cipher import AES
from grid_config import *

# configuration
DEBUG = True
SECRET_KEY = 'i938jy89610XKP9Q128dxu0O5PLMKSU6'
os.environ["DBDATE"] = "Y4MD-"
defaultpass = '000000'

# create our little application :)
app = Flask(__name__)
app.config.from_object(__name__)

def connect_db():
    db = pyodbc.connect("DSN=Infdrv1", autocommit=True)
    db_local = sqlite3.connect('db.sqlite')
    db_local.text_factory = str
    db_local.isolation_level = None # autocommit mode
    return db, db_local


@app.before_request
def before_request():
    g.db, g.db_local = connect_db()


@app.teardown_request
def teardown_request(exception):
    db = getattr(g, 'db', None)
    db_local = getattr(g, 'db_local', None)
    if db is not None:
        db.close()
    if db_local is not None:
        db_local.close()


@app.route('/')
def main():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('main.html')


# def gen_userkey():
#     lib = "1234567890_qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
#     sample = np.random.choice(list(lib), 10)
#     key = ""
#     for s in sample:
#         key += s
#     return key


@app.route('/export_data', methods=['GET'])
def export_data():
    # import pdb; pdb.set_trace()
    if session['exportdata'] == 0:
        return json.dumps({'status':'error', 'message':u'无导出权限'})
    # currentSQL = session['currentSQL']
    cur = g.db_local.cursor()
    sql = "select sqlstm from currentsql where usercode=?"
    cur.execute(sql, [session['usercode']])
    row = cur.fetchone()
    currentSQL = row[0].decode('utf8')
    result = getRecords(g.db, currentSQL, session['currentREQ'], has_limit=False)
    return json.dumps(result)


# @app.route('/delete_xls', methods=['GET'])
# def delete_xls():
#     os.remove(session['xlsname'])
#     return 'success'


def clear_userdir(usercode):
    userdir = os.path.join('static', usercode)
    if os.path.exists(userdir):
        for file in os.listdir(userdir):
            os.remove(os.path.join(userdir, file))
    else:
        os.mkdir(userdir)
    # open('tmp.txt', a)
    # if os.path.isfile('static/tmp'):
    #     os.remove('static/tmp')


@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    enc_obj = AES.new(SECRET_KEY[:16], AES.MODE_CBC, SECRET_KEY[16:])
    # import pdb; pdb.set_trace()
    if request.method == 'POST':
        cur = g.db_local.cursor()
        sql = "select password, username, comcode, comname, riskcode, validstatus, exportdata from users where usercode=?"
        # usercode = request.form['username'].encode('utf8')
        usercode = request.form['username']
        cur.execute(sql, [usercode])
        row = cur.fetchone()
        if row and row[5] == 0:
            error = u'尚无使用该系统权限'
        elif row and row[0] == enc_obj.encrypt(clip_psw(request.form['password'])):
            clear_userdir(usercode)
            session['password'] = row[0]
            session['logged_in'] = True
            session['username'] = row[1]
            session['comcode'] = json.loads(row[2])
            session['comname'] = row[3]
            session['usercode'] = usercode
            session['riskcode'] = json.loads(row[4])
            session['exportdata'] = row[6]
            # session['userkey'] = gen_userkey()
            logintime = strftime("%Y-%m-%d %H:%M:%S", localtime())
            cur.execute('update users set lastlogin=? where usercode=?',[logintime, usercode])
            return redirect(url_for('main'))
        else:
            error = u"密码错误"
    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    clear_userdir(session['usercode'])
    session.pop('logged_in', None)
    return redirect(url_for('login'))


@app.route('/setup_grid', methods=['GET', 'POST'])
def setup_grid():
    grid = {}
    cur = g.db.cursor()
    menu_item = request.form['menu_item']
    try:
        lev1menu, lev2menu = menu_item.split('>')
    except Exception, e:
        return json.dumps(grid)
    # import pdb; pdb.set_trace()
    if lev1menu == u'后台管理' and lev2menu == u'SQL语句管理':
        grid = sql_manage_grid
    elif lev1menu == u'后台管理' and lev2menu == u'用户管理':
        grid = user_manage_grid
    elif lev1menu == u'后台管理' and lev2menu == u'变量说明':
        grid = help_popup
    elif lev1menu == u'工具菜单' and lev2menu == u'修改信息':
        grid = singleuser_manage_grid
    else:
        try:
            cur.execute("select stm from sqlstm where lev1menu=? and lev2menu=?", [lev1menu.encode('utf8'), lev2menu.encode('utf8')])
            row = cur.fetchone()
            raw_sql = row[0].decode('utf8')
            # remove comments
            raw_sql = re.sub('---*.+$', '', raw_sql, flags=re.M)
            columns = parse_columns(raw_sql)
            searches = parse_searches(raw_sql)
            grid = {
                'uitype':'grid',
                'name':'grid',
                'show':{'toolbar':True, 'toolbarSave':True, 'footer':True, 'searchAll':False},
                'multiSearch':True,
                'url':'/show_data/'+menu_item,
                'columns':columns,
                'searches':searches
            }
        except Exception, e:
            pass
    return json.dumps(grid)


@app.route('/show_data/<menu_item>', methods=['POST'])
def show_data(menu_item):
    # import pdb; pdb.set_trace()
    sql = None
    result = {}
    cur = g.db.cursor()
    req = json.loads(request.form['request'])
    try:
        lev1menu, lev2menu = menu_item.split('>')
        cur.execute('select stm from sqlstm where lev1menu=? and lev2menu=?', [lev1menu.encode('utf8'), lev2menu.encode('utf8')])
        row = cur.fetchone()
        raw_sql = row[0].decode('utf8')

        # remove comments
        sql_s = re.sub('---*.+$', '', raw_sql, flags=re.M)
        session['currentLEV'] = lev2menu
        # session['currentSQL'] = sql_s
        # import pdb; pdb.set_trace()
        cur = g.db_local.cursor()
        sql = "insert or replace into currentsql(usercode, sqlstm) values(?,?)"
        cur.execute(sql, [session['usercode'], sql_s.encode('utf8')])

        session['currentREQ'] = req
        result = getRecords(g.db, sql_s, req)
    except:
        pass
    return json.dumps(result, ensure_ascii=False)


def get_days():
    today = date.today()
    currentyear = strftime("%Y")
    currentmonth = strftime("%m")
    pastyear = str(int(strftime("%Y"))-1)
    pastmonth = str(int(strftime("%m"))-1).rjust(2, '0')
    if pastmonth == '00':
        pastmonth = '12'

    nc = "'" + currentyear + "0101" + "'"
    nm = "'" + currentyear + "1231" + "'"
    yc = "'" + currentyear + currentmonth + "01" + "'"
    ym = "'" + currentyear + currentmonth + str(calendar.mdays[today.month]) + "'"
    dt = "'" + strftime("%Y%m%d") + "'"

    qnc = "'" + pastyear + "0101" + "'"
    qnm = "'" + pastyear + "1231" + "'"
    qyc = "'" + pastyear + currentmonth + "01" + "'"
    qym = "'" + pastyear + currentmonth + str(calendar.mdays[today.month]) + "'"
    qdt = "'" + pastyear + strftime("%m%d") + "'"

    syc = "'" + currentyear + pastmonth + "01" + "'"
    sym = "'" + currentyear + pastmonth + str(calendar.mdays[int(pastmonth)]) + "'"
    return nc,nm,yc,ym,dt,qnc,qnm,qyc,qym,qdt,syc,sym


def parse_date(sql):
    nc,nm,yc,ym,dt,qnc,qnm,qyc,qym,qdt,syc,sym = get_days()
    sql = re.sub('qnianchu', qnc, sql)
    sql = re.sub('qnianmo', qnm, sql)
    sql = re.sub('qyuechu', qyc, sql)
    sql = re.sub('qyuemo', qym, sql)
    sql = re.sub('qdangtian', qdt, sql)
    sql = re.sub('syuechu', syc, sql)
    sql = re.sub('syuemo', sym, sql)

    sql = re.sub('nianchu', nc, sql)
    sql = re.sub('nianmo', nm, sql)
    sql = re.sub('yuechu', yc, sql)
    sql = re.sub('yuemo', ym, sql)
    sql = re.sub('dangtian', dt, sql)
    return sql


def parse_comcode_riskcode(sql):
    # comcode_yueshu or A.comcode_yueshu
    # riskcode_yueshu or A.riskcode_yueshu
    for type in ['comcode', 'riskcode']:
        ptn = '\s([a-zA-Z]+\.?)'+type+'_yueshu\s?'
        fnd = re.search(ptn, sql)
        if not fnd:
            continue
        head = fnd.groups()[0]
        code = session[type]
        if len(code) == 0:
            sql = re.sub(ptn, '', sql)
        else:
            rpl = " ("
            for k, v in code.items():
                tmp1 = "'%s'," * len(v)
                tmp1 = tmp1[:-1] % tuple(v)
                tmp2 = type + "[1, %s]" % (k,)
                rpl += head + tmp2 + " in (" + tmp1 + ") or "
            rpl = rpl[:-3] + ') '
            sql = re.sub(ptn, rpl, sql)
        sql = re.sub('and\s*$|or\s*$', '', sql, flags=re.I)
    return sql


def parse_columns(sql):
    sel = re.findall('\[s\s?(.*?)\](.+?)\[/s\]', sql)
    columns = []
    for s in sel:
        c = {}
        c['field'] = s[1].lower()
        c['size'] = '100px'
        if len(s[0]) == 0:
            c['caption'] = s[1]
        else:
            extra = re.findall('(\w+?)\s*?=\s*?"(.+?)"',s[0])
            for e in extra:
                c[e[0]] = e[1]
        columns.append(c)
    return columns


def parse_searches(sql):
    # import pdb; pdb.set_trace()
    sel = re.findall('\[w\s?(.*?)\](.+?)\[/w\]', sql)
    searches = []
    for s in sel:
        c = {}
        flag = 0
        for search in searches:
            if search['field'] == s[1]:
                flag = 1
        if flag == 1:
            continue
        c['field'] = s[1]
        if len(s[0]) == 0:
            c['caption'] = s[1].strip()
        else:
            extra = re.findall('(\w+?)\s*?=\s*?"(.*?)"',s[0])
            for e in extra:
                c[e[0]] = e[1]
        searches.append(c)
    return searches


def parse_where(sql):
    today = date.today()
    # import pdb; pdb.set_trace()
    sel = re.findall('\[w\s?(.*?)\](.+?)\[/w\]', sql)
    for s in sel:
        extra = re.findall('(\w+?)\s*?=\s*?"(.*?)"',s[0])
        for e in extra:
            if e[0] == 'cond':
                val = e[1]
                if len(val.strip()) == 0:
                    return False
                nc,nm,yc,ym,dt,qnc,qnm,qyc,qym,qdt,syc,sym = get_days()
                val = val.replace('qnianchu', qnc)
                val = val.replace('qnianmo', qnm)
                val = val.replace('qyuechu', qyc)
                val = val.replace('qyuemo', qym)
                val = val.replace('qdangtian', qdt)
                val = val.replace('syuechu', syc)
                val = val.replace('syuemo', sym)

                val = val.replace('nianchu', nc)
                val = val.replace('nianmo', nm)
                val = val.replace('yuechu', yc)
                val = val.replace('yuemo', ym)
                val = val.replace('dangtian', dt)

                cond = s[1].strip() + ' ' + val
                break
        sql = re.sub('\[w.*?\]'+s[1]+'\[/w\]', cond, sql)
    return sql


@app.route('/show_sqlstm', methods=['GET', 'POST'])
def show_sqlstm():
    cur = g.db.cursor()
    req = json.loads(request.form.get('request'))
    if req['cmd'] == 'get':
        sql = "select id, lev1menu, lev2menu, menuno, stm from sqlstm order by lev1menu, menuno"
        cur.execute(sql)
        # import pdb; pdb.set_trace()
        rows = cur.fetchall()
        if rows:
            obj = {'status':'success','total':len(rows)}
            records = []
            for row in rows:
                records.append({'recid':row[0], 'lev1menu':row[1], 'lev2menu':row[2], 'menuno':row[3], 'stm':row[4]})
            obj['records'] = records
        else:
            obj = {'status':'error','message':'无记录'}
    elif req['cmd'] == 'delete':
        sql = "delete from sqlstm where id=?"
        try:
            cur.execute(sql, req['selected'])
            obj = {'status':'success'}
        except:
            obj = {'status':'error','message':'delete error'}
    else:
        obj = {'status':'error','message':'unknown cmd'}
    return json.dumps(obj)


@app.route('/show_user', methods=['GET', 'POST'])
def show_user():
    cur = g.db_local.cursor()
    req = json.loads(request.form.get('request'))
    if req['cmd'] == 'get':
        sql = "select usercode, username, comname, comcode, riskcode, exportdata, validstatus, lastlogin from users order by username"
        cur.execute(sql)
        # import pdb; pdb.set_trace()
        rows = cur.fetchall()
        if rows:
            obj = {'status':'success','total':len(rows)}
            records = []
            for row in rows:
                tmp1 = json.loads(row[3])
                comcode = code2str(tmp1)
                tmp2 = json.loads(row[4])
                riskcode = code2str(tmp2)
                tmp3 = row[7]
                if tmp3 is None:
                    lastlogin = ''
                else:
                    # lastlogin = tmp3.strftime('%Y-%m-%d %H:%M:%S')
                    lastlogin = tmp3

                records.append({'usercode':row[0], 'username':row[1], 'comname':row[2], 'comcode':comcode, 'riskcode':riskcode,
                                'exportdata':row[5], 'validstatus':row[6], 'lastlogin':lastlogin})
            obj['records'] = records
        else:
            obj = {'status':'error','message':'无记录'}
    elif req['cmd'] == 'delete':
        sql = "delete from users where usercode=?"
        try:
            cur.execute(sql, req['selected'])
            obj = {'status':'success'}
        except:
            obj = {'status':'error','message':'delete error'}
    else:
        obj = {'status':'error','message':'unknown cmd'}
    return json.dumps(obj)


@app.route('/show_singleuser', methods=['GET', 'POST'])
def show_singleuser():
    cur = g.db_local.cursor()
    req = json.loads(request.form.get('request'))
    if req['cmd'] == 'get':
        sql = "select usercode, username, comname, lastlogin from users where usercode=?"
        # cur.execute(sql, [session['usercode'].encode('utf8')])
        cur.execute(sql, [session['usercode']])
        # import pdb; pdb.set_trace()
        row = cur.fetchone()
        if row:
            obj = {'status':'success','total':1}
            records = []
            if row[3] is None:
                lastlogin = ''
            else:
                # lastlogin = row[3].strftime('%Y-%m-%d %H:%M:%S')
                lastlogin = row[3]

            records.append({'usercode':row[0], 'username':row[1], 'comname':row[2], 'lastlogin':lastlogin})
            obj['records'] = records
        else:
            obj = {'status':'error','message':'无记录'}
    else:
        obj = {'status':'error','message':'unknown cmd'}
    return json.dumps(obj)


@app.route('/manage_sqlstm', methods=['GET', 'POST'])
def manage_sqlstm():
    cur = g.db.cursor()
    # import pdb; pdb.set_trace()
    req = json.loads(request.form.get('request'))
    if req['recid'] == 0:# insert new record
        sql = "insert into sqlstm(lev1menu, lev2menu, menuno, stm) values(?,?,?,?)"
        try:
            cur.execute(sql, [req['record']['lev1menu'].encode('utf8'), req['record']['lev2menu'].encode('utf8'),
                                req['record']['menuno'], pyodbc.Binary(req['record']['stm'].encode('utf8'))])
            obj = {'status':'success'}
        except:
            obj = {'status':'error', 'message':'insert error'}
    else:
        sql = "update sqlstm set lev1menu=?, lev2menu=?, menuno=?, stm=? where id=?"
        try:
            cur.execute(sql, [req['record']['lev1menu'].encode('utf8'), req['record']['lev2menu'].encode('utf8'),
                req['record']['menuno'], pyodbc.Binary(req['record']['stm'].encode('utf8')), req['record']['recid']])
            obj = {'status':'success'}
        except:
            obj = {'status':'error', 'message':'update error'}
    return json.dumps(obj)


@app.route('/manage_user', methods=['GET', 'POST'])
def manage_user():
    cur = g.db_local.cursor()
    enc_obj = AES.new(SECRET_KEY[:16], AES.MODE_CBC, SECRET_KEY[16:])
    # import pdb; pdb.set_trace()
    req = json.loads(request.form.get('request'))
    # usercode = req['record']['usercode'].encode('utf8')
    # username = req['record']['username'].encode('utf8')
    # comcode = pyodbc.Binary(json.dumps(str2code(req['record']['comcode'].encode('utf8'))))
    # comname = req['record']['comname'].encode('utf8')
    # riskcode = json.dumps(str2code(req['record']['riskcode'].encode('utf8')))
    # exportdata = req['record']['exportdata'].encode('utf8')
    # validstatus = req['record']['validstatus'].encode('utf8')
    # psw = req['record']['password'].encode('utf8')
    usercode = req['record']['usercode']
    username = req['record']['username']
    comcode = json.dumps(str2code(req['record']['comcode']))
    comname = req['record']['comname']
    riskcode = json.dumps(str2code(req['record']['riskcode']))
    exportdata = req['record']['exportdata']
    validstatus = req['record']['validstatus']
    psw = req['record']['password']

    if req['recid'] == 0:# insert new record
        if psw == '':
            password = enc_obj.encrypt(clip_psw(defaultpass))
        else:
            password = enc_obj.encrypt(clip_psw(psw))

        sql = "insert into users(usercode, username, comcode, comname, password, riskcode, exportdata, validstatus) values(?,?,?,?,?,?,?,?)"
        try:
            # cur.execute(sql, [usercode, username, comcode, comname, pyodbc.Binary(password), riskcode, exportdata, validstatus])
            cur.execute(sql, [usercode, username, comcode, comname, password, riskcode, exportdata, validstatus])
            obj = {'status':'success'}
        except:
            obj = {'status':'error', 'message':'insert error'}
    else:
        if psw == '':
            sql = "update users set usercode=?, username=?, comcode=?, comname=?, riskcode=?, exportdata=?, validstatus=? where usercode=?"
            try:
                cur.execute(sql, [usercode, username, comcode, comname, riskcode, exportdata, validstatus, req['record']['recid']])
                obj = {'status':'success'}
            except Exception, e:
                obj = {'status':'error', 'message':'update error '+str(e)}
        else:
            # import pdb; pdb.set_trace();
            password = enc_obj.encrypt(clip_psw(psw))
            sql = "update users set usercode=?, username=?, comcode=?, comname=?, password=?, riskcode=?, exportdata=?, validstatus=? where usercode=?"
            try:
                # cur.execute(sql, [usercode, username, comcode, comname, pyodbc.Binary(password), riskcode, exportdata, validstatus, req['record']['recid']])
                cur.execute(sql, [usercode, username, comcode, comname, password, riskcode, exportdata, validstatus, req['record']['recid']])
                obj = {'status':'success'}
            except Exception, e:
                obj = {'status':'error', 'message':'update error '+str(e)}
    return json.dumps(obj)


def clip_psw(psw):
    if len(psw) <= 16:
        return psw.ljust(16)
    else:
        return psw[:16]


@app.route('/manage_singleuser', methods=['GET', 'POST'])
def manage_singleuser():
    cur = g.db_local.cursor()
    # import pdb; pdb.set_trace()
    # req = json.loads(request.form.get('request'))
    # username = req['record']['username'].encode('utf8')
    # comname = req['record']['comname'].encode('utf8')
    # oldpsw = req['record']['oldpassword'].encode('utf8')
    # newpsw = req['record']['newpassword'].encode('utf8')
    req = json.loads(request.form.get('request'))
    username = req['record']['username']
    comname = req['record']['comname']
    oldpsw = req['record']['oldpassword']
    newpsw = req['record']['newpassword']

    if req['recid'] == 0:# insert new record
        obj = {'status':'error', 'message':u'无权限创建用户'}
    elif oldpsw == '' and newpsw == '':
        sql = "update users set username=?, comname=? where usercode=?"
        try:
            cur.execute(sql, [username, comname, req['record']['recid']])
            obj = {'status':'success'}
        except Exception, e:
            obj = {'status':'error', 'message':'update error '+str(e)}
    elif oldpsw == '':
        obj = {'status':'error', 'message':u'请填写原密码'}
    elif newpsw == '':
        obj = {'status':'error', 'message':u'请填写新密码'}
    else:
        enc_obj = AES.new(SECRET_KEY[:16], AES.MODE_CBC, SECRET_KEY[16:])
        checkpsw = enc_obj.encrypt(clip_psw(oldpsw))
        if session['password'] == checkpsw:
            enc_obj = AES.new(SECRET_KEY[:16], AES.MODE_CBC, SECRET_KEY[16:])
            password = enc_obj.encrypt(clip_psw(newpsw))
            sql = "update users set username=?, comname=?, password=? where usercode=?"
            try:
                # cur.execute(sql, [username, comname, pyodbc.Binary(password), req['record']['recid']])
                cur.execute(sql, [username, comname, password, req['record']['recid']])
                obj = {'status':'success'}
            except Exception, e:
                obj = {'status':'error', 'message':'update error '+str(e)}
        else:
            obj = {'status':'error', 'message':u'原密码不正确'}
    return json.dumps(obj)


@app.route('/gen_toolbar')
def gen_toolbar():
    cur = g.db.cursor()
    cur.execute("select lev1menu, menuno, lev2menu from sqlstm")
    rows = cur.fetchall()

    menu = {}
    for r in rows:
        if r[0] in menu:
            menu[r[0]].append([r[1], r[2]])
        else:
            menu[r[0]] = [[r[1], r[2]]]

    items = [
        { 'type': 'html', 'id': 'toolbar_logo', 'html': '<img src="/static/logo_s.png" style="height:80%"/>'},
        {'type':'break'},
        { 'type': 'menu', 'id': '工具菜单', 'text': u'工具菜单', 'icon': 'fa-wrench', 'items': [
                { 'text': u'修改信息', 'icon': 'fa-star' }
            ]}
    ]
    for m,mi in menu.iteritems():
        items.append({'type':'break'})
        submenu = []
        mi.sort()
        for mii in mi:
            submenu.append({'text':mii[1]})
        items.append({'type':'menu', 'id':m, 'text': m, 'icon': 'fa-table','items':submenu})
    if session['usercode'] == 'admin':
        items.append({'type':'spacer'})
        items.append({ 'type': 'menu', 'id': '后台管理', 'text': '后台管理', 'icon': 'fa-table',
                        'items': [{'text': 'SQL语句管理'}, {'text':'用户管理'}, {'text':'变量说明'}]})
    obj = {'name':'toolbar','items':items}
    return json.dumps(obj)


def code2str(code):
    s = []
    for k, v in code.items():
        s += v
    return ",".join(s)

def str2code(s):
    tmp_a = re.split(u'[,，]', s)
    tmp_a = [re.sub('[^A-Z0-9]', '', item) for item in tmp_a]
    tmp_b = {}
    for item in tmp_a:
        item_len = len(item)
        if item_len != 0:
            if item_len in tmp_b:
                tmp_b[item_len].append(item)
            else:
                tmp_b[item_len] = [item]
    return tmp_b


def data_parser(row):
    #import pdb; pdb.set_trace()
    new_row = []
    for item in row:
        if isinstance(item, datetime.datetime):
            try:
                new_row.append(item.strftime('%Y-%m-%d'))
            except Exception, e:
                if isinstance(e, ValueError):
                    new_row.append('')
                else:
                    new_row.append(str(item))

        elif isinstance(item, datetime.date):
            try:
                new_row.append(item.strftime('%Y-%m-%d'))
            except Exception, e:
                if isinstance(e, ValueError):
                    new_row.append('')
                else:
                    new_row.append(str(item))

        elif isinstance(item, decimal.Decimal):
            new_row.append(float(item))
        elif isinstance(item, cdecimal.Decimal):
            new_row.append(float(item))
        elif isinstance(item, int):
            new_row.append(item)
        elif isinstance(item, str):
            new_row.append(item.decode('gb18030', errors='ignore'))
        elif item is None:
            new_row.append('')
        else:
            # import pdb; pdb.set_trace()
            new_row.append(item)

    return new_row


def parse_like(sql):
    likes = re.findall('\slike\s+[\'\"].+?[\'\"]', sql)
    if len(likes) > 0:
        first_like = re.search(likes[0], sql)
        qmark_before = len(re.findall('\?', sql[ : first_like.start()]))
        last_like = re.search(likes[-1], sql)
        qmark_after = len(re.findall('\?', sql[last_like.end() : ]))
        vals = []
        rep = " like '%'||?||'%' "
        for s in likes:
            cont = s.strip().split(' ')
            for c in cont:
                if c == 'like': continue
                val = re.sub('[\'\"\%]', '', c)
                vals.append(val.encode('gb18030'))
            sql = re.sub(s, rep, sql)
        return qmark_before, qmark_after, vals, sql
    else:
        return None,


def gen_titledict(sql_s):
    sql = sql_s.replace('\n', ' ')
    # 2-step approach
    ptn1 = re.compile('\[s(.*?)\](.+?)\[/s\]')
    ptn2 = re.compile('caption\s*=\s*\"(.+?)\"')

    fd1 = re.findall(ptn1, sql)
    titledict = {}
    for item in fd1:
        fd2 = re.search(ptn2, item[0])
        if fd2:
            titledict[item[1]] = fd2.groups()[0]
        else:
            titledict[item[1]] = item[1]
    return titledict


def getRecords(db, sql_s, request, has_limit=True):
    #import pdb; pdb.set_trace()
    sql_components = { 'params': [], 'sort': [] }
    search_array = request.get('search', [])
    for search in search_array:
        operator = "="
        field    = search['field']  # TODO: protect from sql injection!!!
        type_    = search['type']
        if type(search['value']) is list:
            value = search['value']
        else:
            value = [search['value']]
        for v in value:
            if isinstance(v, int) or isinstance(v, float):
                sql_components['params'].append(v)
            else:
                sql_components['params'].append(v.encode('gb18030'))

        op = search['operator'].lower()
        if op == "begins":
            operator = "LIKE ?||'%'"
        elif op == "ends":
            operator = "LIKE '%'||?"
        elif op == "contains":
            operator = "LIKE '%'||?||'%'"
        elif op == "is":
            # operator = "= LOWER(?)"
            operator = "= ?"
        elif op == "between":
            # value    = value[0]
            operator = "BETWEEN ? AND ?"
        elif op == "in":
            # value    = value[0]
            operator = "IN (%s)" % ','.join(['?'] * len(value))
        elif op == "not in":
            # value    = value[0]
            operator = "not IN (%s)" % ','.join(['?'] * len(value))
        elif op == "less":
            operator = "<= ?"
        elif op == "more":
            operator = ">= ?"
        sql_s = re.sub('\[w.*?\]'+field+'\[/w\]', "%s %s" % (field, operator), sql_s)

    sql_s = parse_where(sql_s)

    if not sql_s: # 如果没有指定查询条件，则不返回任何信息
        data = {}
        data['records'] = []
        data['total'] = 0
        data['status'] = 'success'
        return data


    # import pdb; pdb.set_trace();
    # 生成对照表
    titledict = gen_titledict(sql_s)
    sql_s = re.sub('\[/?s.*?\]', '', sql_s)

    sql = [] # build sql list; execute one by one
    for sq in sql_s.split(';'):
        sq = sq.replace('\n', ' ').strip()
        sq = parse_date(sq)
        sq = parse_comcode_riskcode(sq)
        if len(sq) > 0:
            sql.append(sq)

    sort_array = request.get('sort', [])
    for sort in sort_array:
        field = sort['field']      # TODO: protect from sql injection!!!
        if field == 'recid': continue
        dir_  = sort['direction']  # TODO: protect from sql injection!!!
        sql_components['sort'].append(field+' '+dir_)

    # connector = ' %s ' % request.get('searchLogic','AND')  # TODO: protect from sql injection!!!
    # where = connector.join(sql_components['where'])
    # if not where:
    #     where = '1=1'
    sort = ",".join(sql_components['sort'])
    if not sort:
        sort = '1'

    limit  = request.get('limit', 100)
    offset = request.get('offset', 0)
    # import pdb; pdb.set_trace()
    # count records
    csql = sql[-1]
    csql = re.sub('\s+from\s+', ' from ', csql, flags=re.IGNORECASE)
    csql = csql[:6] + ' count(*) '+ csql[csql.rindex('from'):] # 'from' should be in lower case
    if has_limit:
        sql[-1] = re.sub('^select\s|^SELECT\s', 'select skip %s limit %s ' % (offset, limit), sql[-1])
    sql[-1] = sql[-1] + " order by %s" % (sort)

    data = {}
    try:
        cursor = db.cursor()
        data['records'] = []
        #import pdb; pdb.set_trace()
        for _sql in sql[:-1]:
            combo = parse_like(_sql)
            if combo[0] is None:
                qmark_num = len(re.findall('\?', _sql))
                params_ = []
                for i in xrange(qmark_num):
                    params_.append(sql_components['params'].pop(0))
                cursor.execute(_sql.encode('utf8'), params_)
            else:
                params_ = []
                for i in xrange(combo[0]):
                    params_.append(sql_components['params'].pop(0))
                params_.extend(combo[2])
                for i in xrange(combo[1]):
                    params_.append(sql_components['params'].pop(0))
                cursor.execute(combo[3].encode('utf8'), params_)

        combo = parse_like(sql[-1])
        if combo[0] is None:
            cursor.execute(sql[-1].encode('utf8'),sql_components['params'])
        else:
            params_ = []
            for i in xrange(combo[0]):
                params_.append(sql_components['params'].pop(0))
            params_.extend(combo[2])
            for i in xrange(combo[1]):
                params_.append(sql_components['params'].pop(0))
            cursor.execute(combo[3].encode('utf8'), params_)
            
        #import pdb; pdb.set_trace()
        rows = cursor.fetchall()
        columns = [ d[0] for d in cursor.description ]

        if not has_limit:
            #import pdb; pdb.set_trace()
            xlsname = os.path.join('static', session['usercode'], "%s_%s.xlsx" % (session['currentLEV'], strftime("%Y.%m.%d %H%M%S", localtime()))) # 导出文件名
            wb = xlsxwriter.Workbook(xlsname)
            ws = wb.add_worksheet()

            #xlsname = os.path.join('static', session['usercode'], "%s_%s.xls" % (session['currentLEV'], strftime("%Y%m%d%H%M%S", localtime()))) # 导出文件名
            #wb = xlwt.Workbook()
            #ws = wb.add_sheet('sheet1')

            for i in xrange(len(columns)):
                if columns[i] in titledict:
                    ws.write(0, i, titledict[columns[i]])
                else:
                    ws.write(0, i, columns[i])

            for i in xrange(len(rows)):
                new_row = data_parser(rows[i])
                for j in xrange(len(columns)):
                    ws.write(i+1, j, new_row[j])

            session['xlsname'] = xlsname

            #wb.save(xlsname)
            wb.close()

            data['xlsname'] = xlsname
            data['status'] = 'success'
            return data

        if combo[0] is None:
            cursor.execute(csql.encode('utf8'),sql_components['params'])
        else:
            params_ = []
            for i in xrange(combo[0]):
                params_.append(sql_components['params'].pop(0))
            params_.extend(combo[2])
            for i in xrange(combo[1]):
                params_.append(sql_components['params'].pop(0))
            rep = " like '%'||?||'%' "
            csql = re.sub('\slike\s+[\'\"].+?[\'\"]\s?', rep, csql)
            cursor.execute(csql.encode('utf8'), params_)

        data['total'] = int(cursor.fetchone()[0])
        for row in rows:
            record = zip(columns, data_parser(row))
            data['records'].append( dict(record) )
        data['status'] = 'success'
    except Exception, e:
        data['status'] = 'error'
        data['message'] = '%s\n\n%s' % (str(e), sql)
    return data


if __name__ == '__main__':
    app.run(host='0.0.0.0')
