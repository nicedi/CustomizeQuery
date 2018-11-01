# -*- coding=utf-8 -*-
sql_manage_grid = {
    'uitype':'layout',
    'layout': {
        'name': 'layout',
        'padding': 4,
        'panels': [
            { 'type': 'left', 'size': '50%', 'resizable': 'true', 'minSize': 300 },
            { 'type': 'main', 'minSize': 300 }
        ]
    },
    'grid': {
        'name': 'grid',
        'url':'/show_sqlstm',
        'show': {
            'toolbar'            : 'true',
            'toolbarDelete'    : 'true'
        },
        'columns': [
            { 'field': 'lev1menu', 'caption': '菜单名', 'size': '25%', 'sortable': 'true' },
            { 'field': 'lev2menu', 'caption': '菜单项名', 'size': '25%' },
            { 'field': 'menuno', 'caption': '菜单内顺序', 'size': '25%' },
            { 'field': 'stm', 'caption': '查询语句', 'size': '25%' }
        ],
        'onClick': 'undefined'
    },
    'form': {
        'header': '编辑查询语句',
        'name': 'form',
        'url':'/manage_sqlstm',
        'fields': [
            { 'name': 'lev1menu', 'type': 'text', 'required':'true', 'html': { 'caption': '菜单名', 'attr': 'size="40"' }},
            { 'name': 'lev2menu', 'type': 'text', 'required': 'true', 'html': { 'caption': '菜单项名', 'attr': 'size="40"' }},
            { 'name': 'menuno', 'type': 'int', 'required': 'true', 'html': { 'caption': '菜单内顺序', 'attr': 'size="40"' }},
            { 'name': 'stm', 'type': 'textarea', 'required': 'true', 'html': { 'caption': '查询语句', 'attr':'style="width: 500px; height: 900px"' } }
        ],
        'actions': {
            'Reset': 'undefined',
            'Save': 'undefined'
        }
    }
}

user_manage_grid = {
    'uitype':'layout',
    'layout': {
        'name': 'layout',
        'padding': 4,
        'panels': [
            { 'type': 'left', 'size': '50%', 'resizable': 'true', 'minSize': 300 },
            { 'type': 'main', 'minSize': 300 }
        ]
    },
    'grid': {
        'name': 'grid',
        'url':'/show_user',
        'recid':'usercode',
        'show': {
            'toolbar'            : 'true',
            'toolbarDelete'    : 'false'
        },
        'columns': [
            { 'field': 'usercode', 'caption': '用户代码', 'size': '12.5%', 'sortable': 'true' },
            { 'field': 'username', 'caption': '用户姓名', 'size': '12.5%' },
            { 'field': 'comname', 'caption': '公司名', 'size': '12.5%' },
            { 'field': 'comcode', 'caption': '公司代码', 'size': '12.5%' },
            { 'field': 'riskcode', 'caption': '险种代码', 'size': '12.5%' },
            { 'field': 'exportdata', 'caption': '可否导出数据', 'size': '12.5%' },
            { 'field': 'validstatus', 'caption': '账号是否有效', 'size': '12.5%' },
            { 'field': 'lastlogin', 'caption': '上次登录时间', 'size': '12.5%' }
        ],
        'onClick': 'undefined'
    },
    'form': {
        'header': '编辑用户信息',
        'name': 'form',
        'url':'/manage_user',
        'fields': [
            { 'name': 'usercode', 'type': 'text', 'required':'true', 'html': { 'caption': '用户代码', 'attr': 'size="40"' }},
            { 'name': 'username', 'type': 'text', 'required': 'true', 'html': { 'caption': '用户姓名', 'attr': 'size="40"' }},
            { 'name': 'comname', 'type': 'text', 'required': 'true', 'html': { 'caption': '公司名', 'attr': 'size="40"' }},
            { 'name': 'comcode', 'type': 'textarea', 'required': 'true', 'html': { 'caption': '公司代码(逗号分隔)', 'attr':'style="width: 400px; height: 200px"' } },
            { 'name': 'riskcode', 'type': 'textarea', 'html': { 'caption': '险种代码(逗号分隔)', 'attr':'style="width: 400px; height: 100px"' } },
            { 'name': 'exportdata', 'type': 'text', 'required':'true', 'html': { 'caption': '可否导出数据(0或1)', 'attr': 'size="40"' }},
            { 'name': 'validstatus', 'type': 'text', 'required': 'true', 'html': { 'caption': '账号是否有效(0或1)', 'attr': 'size="40"' }},
            { 'name': 'password', 'type': 'text', 'html': { 'caption': '留空则不修改密码', 'attr': 'size="40"' }}
        ],
        'actions': {
            'Reset': 'undefined',
            'Save': 'undefined'
        }
    }
}

singleuser_manage_grid = {
    'uitype':'layout',
    'layout': {
        'name': 'layout',
        'padding': 4,
        'panels': [
            { 'type': 'left', 'size': '50%', 'resizable': 'true', 'minSize': 300 },
            { 'type': 'main', 'minSize': 300 }
        ]
    },
    'grid': {
        'name': 'grid',
        'url':'/show_singleuser',
        'recid':'usercode',
        'show': {
            'toolbar'            : 'true',
            'toolbarDelete'    : 'false'
        },
        'columns': [
            { 'field': 'username', 'caption': '用户姓名', 'size': '33%' },
            { 'field': 'comname', 'caption': '公司名', 'size': '33%' },
            { 'field': 'lastlogin', 'caption': '上次登录时间', 'size': '33%' }
        ],
        'onClick': 'undefined'
    },
    'form': {
        'header': '编辑用户信息',
        'name': 'form',
        'url':'/manage_singleuser',
        'fields': [
            { 'name': 'username', 'type': 'text', 'required': 'true', 'html': { 'caption': '用户姓名', 'attr': 'size="40"' }},
            { 'name': 'comname', 'type': 'text', 'required': 'true', 'html': { 'caption': '公司名', 'attr': 'size="40"' }},
            { 'name': 'oldpassword', 'type': 'password', 'html': { 'caption': '原密码(留空则不修改)', 'attr': 'size="40"' }},
            { 'name': 'newpassword', 'type': 'password', 'html': { 'caption': '新密码(留空则不修改)', 'attr': 'size="40"' }}
        ],
        'actions': {
            'Reset': 'undefined',
            'Save': 'undefined'
        }
    }
}

help_popup = {
    'uitype':'popup',
    'title':u'变量说明',
    'body':'<div>'+
            '<strong>日期变量:</strong>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;nianchu:年初</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;nianmo:年末</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;yuechu:月初</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;yuemo:月末</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;syuechu:上月初</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;syuemo:上月末</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;dangtian:当天</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;qnianchu:去年初</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;qnianmo:去年末</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;qyuechu:去年同时期月初</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;qyuemo:去年同时期月末</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;qdangtian:去年当天</p>'+
            '<strong>其它变量:</strong>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;comcode_yueshu:根据用户所属公司码生成comcode[1, x] in (xxxxxx)这种条件。</p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;使用中直接写 a.comcode_yueshu（表有别名时）或comcode_yueshu即可</p>'+
            '<p></p>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;riskcode_yueshu:险种代码约束条件。用法同上</p>'+
            '<strong>自定义SQL语句说明:</strong>'+
            '<p>&nbsp;&nbsp;&nbsp;&nbsp;当查询条件由用户指定时，可将SQL语句中对应查询字段的cond属性留空。</p>'+
            '</div>',
    'width':'500',
    'height':'600'
}
