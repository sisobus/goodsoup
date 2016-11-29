#!/usr/bin/python
#-*- coding:utf-8 -*-
import json
if __name__ == '__main__':
    with open('address.json','r') as fp:
        r = json.loads(fp.read())

    si = [u'경기도']
    gu = [u'용인시 기흥구',u'화성시',u'수원시 영통구',u'수원시 권선구']
    dong = [u'동백동',u'중동',u'반월동',u'광교동',u'망포동',u'태장동',u'곡선동',u'권선동',u'권선1동',u'권선2동']
    ans = []
    for si_item in r:
        if not si_item['name'] in si:
            continue
        ans.append({'name':si_item['name'],'items':[]})
        _gu = []
        for gu_item in si_item['items']:
            if not gu_item['name'] in gu:
                continue
            ans[-1]['items'].append({'name':gu_item['name'],'items':[]})
            for dong_item in gu_item['items']:
                if not dong_item['name'] in dong:
                    continue
                ans[-1]['items'][-1]['items'].append({'name':dong_item['name']})
    with open('20161129.json','w') as fp:
        fp.write(json.dumps(ans))
