from collections import defaultdict

import pandas as pd

from bbg.request import Request
from bbg.utils import XmlHelper


class ReferenceDataResponse(object):

    def __init__(self, request):
        self.request = request
        self.response_map = defaultdict(dict)

    def on_security_data(self, sid, field_map):
        self.response_map[sid].update(field_map)

    def as_map(self):
        return self.response_map

    def as_frame(self):
        """ :return: Multi-Index DataFrame """
        data = {sid: pd.Series(data) for sid, data in self.response_map.items()}
        frame = pd.DataFrame.from_dict(data, orient='index')
        # layer in any missing fields just in case
        frame = frame.reindex_axis(self.request.fields, axis=1)
        return frame


class ReferenceDataRequest(Request):

    def __init__(self, sids, fields, ignore_security_error=0, ignore_field_error=0, return_formatted_value=None,
                 use_utc_time=None, **overrides):
        """
        response_type: (frame, map) how to return the results
        """
        Request.__init__(self, '//blp/refdata', ignore_security_error=ignore_security_error,
                         ignore_field_error=ignore_field_error)
        self.is_single_sid = isinstance(sids, str)
        self.is_single_field = isinstance(fields, str)
        self.sids = isinstance(sids, str) and [sids] or sids
        self.fields = isinstance(fields, str) and [fields] or fields
        self.return_formatted_value = return_formatted_value
        self.use_utc_time = use_utc_time
        self.overrides = overrides

    def __repr__(self):
        fmtargs = dict(clz=self.__class__.__name__,
                       sids=','.join(self.sids),
                       fields=','.join(self.fields),
                       overrides=','.join(['%s=%s' % (k, v) for k, v in self.overrides.items()]))
        return '<{clz}([{sids}], [{fields}], overrides={overrides})'.format(**fmtargs)

    def new_response(self):
        self.response = ReferenceDataResponse(self)

    def get_bbg_request(self, svc, session):
        # create the bloomberg request object
        request = svc.createRequest('ReferenceDataRequest')
        [request.append('securities', sec) for sec in self.sids]
        [request.append('fields', fld) for fld in self.fields]
        self.set_flag(request, self.return_formatted_value, 'returnFormattedValue')
        self.set_flag(request, self.use_utc_time, 'useUTCTime')
        Request.apply_overrides(request, self.overrides)
        return request

    def on_security_node(self, node):
        sid = XmlHelper.get_child_value(node, 'security')
        farr = node.getElement('fieldData')
        fdata = XmlHelper.get_child_values(farr, self.fields)
        assert len(fdata) == len(self.fields), 'field length must match data length'
        self.response.on_security_data(sid, dict(zip(self.fields, fdata)))
        ferrors = XmlHelper.get_field_errors(node)
        ferrors and self.field_errors.extend(ferrors)

    def on_event(self, evt, is_final):
        for msg in XmlHelper.message_iter(evt):
            for node, error in XmlHelper.security_iter(msg.getElement('securityData')):
                if error:
                    self.security_errors.append(error)
                else:
                    self.on_security_node(node)
