from collections import defaultdict

import pandas as pd

from bbg.request import Request
from bbg.utils import XmlHelper


class EQSResponse(object):

    def __init__(self, request):
        self.request = request
        self.response_map = defaultdict(dict)

    def on_security_data(self, sid, fieldmap):
        self.response_map[sid].update(fieldmap)

    def as_map(self):
        return self.response_map

    def as_frame(self):
        """ :return: Multi-Index DataFrame """
        data = {sid: pd.Series(data) for sid, data in self.response_map.items()}
        return pd.DataFrame.from_dict(data, orient='index')


class EQSRequest(Request):

    def __init__(self, name, type_='GLOBAL', group='General', asof=None, language=None):
        super(EQSRequest, self).__init__('//blp/refdata')
        self.name = name
        self.group = group
        self.type = type_
        self.asof = asof and pd.to_datetime(asof) or None
        self.language = language

    def __repr__(self):
        fmtargs = dict(clz=self.__class__.__name__,
                       name=self.name,
                       type=self.type,
                       group=self.group,
                       asof=self.asof)
        return '<{clz}({name}, type={type}, group={group}, asof={asof})'.format(**fmtargs)

    def new_response(self):
        self.response = EQSResponse(self)

    def get_bbg_request(self, svc, session):
        # create the bloomberg request object
        request = svc.createRequest('BeqsRequest')
        request.set('screenName', self.name)
        self.type and request.set('screenType', self.type)
        self.group and request.set('Group', self.group)
        overrides = {}
        if self.asof:
            overrides['PiTDate'] = self.asof.strftime('%Y%m%d')
        if self.language:
            overrides['languageId'] = self.language
        overrides and self.apply_overrides(request, overrides)
        return request

    def on_security_node(self, node):
        sid = XmlHelper.get_child_value(node, 'security')
        farr = node.getElement('fieldData')
        fldnames = [str(farr.getElement(_).name()) for _ in range(farr.numElements())]
        fdata = XmlHelper.get_child_values(farr, fldnames)
        self.response.on_security_data(sid, dict(zip(fldnames, fdata)))
        ferrors = XmlHelper.get_field_errors(node)
        ferrors and self.field_errors.extend(ferrors)

    def on_event(self, evt, is_final):
        for msg in XmlHelper.message_iter(evt):
            data = msg.getElement('data')
            for node, error in XmlHelper.security_iter(data.getElement('securityData')):
                if error:
                    self.security_errors.append(error)
                else:
                    self.on_security_node(node)
