from collections import defaultdict

import pandas as pd

from bbg.request import Request
from bbg.utils import XmlHelper


class HistoricalDataResponse(object):

    def __init__(self, request):
        self.request = request
        self.response_map = {}

    def on_security_complete(self, sid, frame):
        self.response_map[sid] = frame

    def as_panel(self):
        return pd.Panel(self.response_map)

    def as_map(self):
        return self.response_map

    def as_frame(self):
        """ :return: Multi-Index DataFrame """
        sids, frames = self.response_map.keys(), self.response_map.values()
        frame = pd.concat(frames, keys=sids, axis=1)
        return frame


class HistoricalDataRequest(Request):
    """A class which manages the creation of the Bloomberg HistoricalDataRequest and
    the processing of the associated Response.

    Parameters
    ----------
    sids: bbg security identifier(s)
    fields: bbg field name(s)
    start: (optional) date, date string , or None. If None, defaults to 1 year ago.
    end: (optional) date, date string, or None. If None, defaults to today.
    period: (optional) periodicity of data [DAILY, WEEKLY, MONTHLY, QUARTERLY, SEMI-ANNUAL, YEARLY]
    ignore_security_error: If True, ignore exceptions caused by invalid sids
    ignore_field_error: If True, ignore exceptions caused by invalid fields
    period_adjustment: (ACTUAL, CALENDAR, FISCAL)
                        Set the frequency and calendar type of the output
    currency: ISO Code
              Amends the value from local to desired currency
    override_option: (OVERRIDE_OPTION_CLOSE | OVERRIDE_OPTION_GPA)
    pricing_option: (PRICING_OPTION_PRICE | PRICING_OPTION_YIELD)
    non_trading_day_fill_option: (NON_TRADING_WEEKDAYS | ALL_CALENDAR_DAYS | ACTIVE_DAYS_ONLY)
    non_trading_day_fill_method: (PREVIOUS_VALUE | NIL_VALUE)
    calendar_code_override: 2 letter county iso code
    """

    def __init__(self, sids, fields, start=None, end=None, period=None, ignore_security_error=0,
                 ignore_field_error=0, period_adjustment=None, currency=None, override_option=None,
                 pricing_option=None, non_trading_day_fill_option=None, non_trading_day_fill_method=None,
                 max_data_points=None, adjustment_normal=None, adjustment_abnormal=None, adjustment_split=None,
                 adjustment_follow_DPDF=None, calendar_code_override=None, **overrides):

        Request.__init__(self, '//blp/refdata', ignore_security_error=ignore_security_error,
                         ignore_field_error=ignore_field_error)
        period = period or 'DAILY'
        assert period in ('DAILY', 'WEEKLY', 'MONTHLY', 'QUARTERLY', 'SEMI-ANNUAL', 'YEARLY')
        self.is_single_sid = is_single_sid = isinstance(sids, str)
        self.is_single_field = is_single_field = isinstance(fields, str)
        self.sids = is_single_sid and [sids] or list(sids)
        self.fields = is_single_field and [fields] or list(fields)
        self.end = end = pd.to_datetime(end) if end else pd.Timestamp.now()
        self.start = pd.to_datetime(start) if start else end + pd.DateOffset(years=-1)
        self.period = period
        self.period_adjustment = period_adjustment
        self.currency = currency
        self.override_option = override_option
        self.pricing_option = pricing_option
        self.non_trading_day_fill_option = non_trading_day_fill_option
        self.non_trading_day_fill_method = non_trading_day_fill_method
        self.max_data_points = max_data_points
        self.adjustment_normal = adjustment_normal
        self.adjustment_abnormal = adjustment_abnormal
        self.adjustment_split = adjustment_split
        self.adjustment_follow_DPDF = adjustment_follow_DPDF
        self.calendar_code_override = calendar_code_override
        self.overrides = overrides

    def __repr__(self):
        fmtargs = dict(clz=self.__class__.__name__,
                       symbols=','.join(self.sids),
                       fields=','.join(self.fields),
                       start=self.start.strftime('%Y-%m-%d'),
                       end=self.end.strftime('%Y-%m-%d'),
                       period=self.period,
                       )
        # TODO: add self.overrides if defined
        return '<{clz}([{symbols}], [{fields}], start={start}, end={end}, period={period}'.format(**fmtargs)

    def new_response(self):
        self.response = HistoricalDataResponse(self)

    def get_bbg_request(self, svc, session):
        # create the bloomberg request object
        request = svc.createRequest('HistoricalDataRequest')
        [request.append('securities', sec) for sec in self.sids]
        [request.append('fields', fld) for fld in self.fields]
        request.set('startDate', self.start.strftime('%Y%m%d'))
        request.set('endDate', self.end.strftime('%Y%m%d'))
        request.set('periodicitySelection', self.period)
        self.period_adjustment and request.set('periodicityAdjustment', self.period_adjustment)
        self.currency and request.set('currency', self.currency)
        self.override_option and request.set('overrideOption', self.override_option)
        self.pricing_option and request.set('pricingOption', self.pricing_option)
        self.non_trading_day_fill_option and request.set('nonTradingDayFillOption', self.non_trading_day_fill_option)
        self.non_trading_day_fill_method and request.set('nonTradingDayFillMethod', self.non_trading_day_fill_method)
        self.max_data_points and request.set('maxDataPoints', self.max_data_points)
        self.calendar_code_override and request.set('calendarCodeOverride', self.calendar_code_override)
        self.set_flag(request, self.adjustment_normal, 'adjustmentNormal')
        self.set_flag(request, self.adjustment_abnormal, 'adjustmentAbnormal')
        self.set_flag(request, self.adjustment_split, 'adjustmentSplit')
        self.set_flag(request, self.adjustment_follow_DPDF, 'adjustmentFollowDPDF')

        if hasattr(self, 'overrides') and self.overrides is not None:
            Request.apply_overrides(request, self.overrides)
        return request

    def on_security_data_node(self, node):
        """process a securityData node - FIXME: currently not handling relateDate node """
        sid = XmlHelper.get_child_value(node, 'security')
        farr = node.getElement('fieldData')
        dmap = defaultdict(list)
        for i in range(farr.numValues()):
            pt = farr.getValue(i)
            [dmap[f].append(XmlHelper.get_child_value(pt, f, allow_missing=1)) for f in ['date'] + self.fields]

        if not dmap:
            frame = pd.DataFrame(columns=self.fields)
        else:
            idx = dmap.pop('date')
            frame = pd.DataFrame(dmap, columns=self.fields, index=idx)
            frame.index.name = 'date'
        self.response.on_security_complete(sid, frame)

    def on_event(self, evt, is_final):
        for msg in XmlHelper.message_iter(evt):
            # Single security element in historical request
            node = msg.getElement('securityData')
            if node.hasElement('securityError'):
                sid = XmlHelper.get_child_value(node, 'security')
                self.security_errors.append(XmlHelper.as_security_error(node.getElement('securityError'), sid))
            else:
                self.on_security_data_node(node)
