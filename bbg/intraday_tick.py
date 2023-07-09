import pandas as pd

from bbg.request import Request
from bbg.utils import XmlHelper


class IntradayTickResponse(object):

    def __init__(self, request):
        self.request = request
        self.ticks = []  # array of dicts

    def as_frame(self):
        """Return a data frame with no set index"""
        return pd.DataFrame.from_records(self.ticks)


class IntradayTickRequest(Request):

    def __init__(self, sid, start=None, end=None, events='TRADE', include_condition_codes=None,
                 include_non_plottable_events=None, include_exchange_codes=None, return_eids=None,
                 include_broker_codes=None, include_rsp_codes=None, include_bic_mic_codes=None):
        """
        Parameters
        ----------
        events: array containing any of (TRADE, BID, ASK, BID_BEST, ASK_BEST, MID_PRICE, AT_TRADE, BEST_BID, BEST_ASK)
        """
        Request.__init__(self, '//blp/refdata')
        self.sid = sid
        self.events = isinstance(events, str) and [events] or events
        self.include_condition_codes = include_condition_codes
        self.include_non_plottable_events = include_non_plottable_events
        self.include_exchange_codes = include_exchange_codes
        self.return_eids = return_eids
        self.include_broker_codes = include_broker_codes
        self.include_rsp_codes = include_rsp_codes
        self.include_bic_mic_codes = include_bic_mic_codes
        self.end = end = pd.to_datetime(end) if end else pd.to_datetime('now')
        self.start = pd.to_datetime(start) if start else end + pd.DateOffset(hours=-1)

    def __repr__(self):
        fmtargs = dict(clz=self.__class__.__name__,
                       sid=self.sid,
                       events=','.join(self.events),
                       start=self.start,
                       end=self.end)
        return '<{clz}({sid}, [{events}], start={start}, end={end})'.format(**fmtargs)

    def new_response(self):
        self.response = IntradayTickResponse(self)

    def get_bbg_request(self, svc, session):
        # create the bloomberg request object
        request = svc.createRequest('IntradayTickRequest')
        request.set('security', self.sid)
        [request.append('eventTypes', evt) for evt in self.events]
        request.set('startDateTime', self.start)
        request.set('endDateTime', self.end)
        self.set_flag(request, self.include_condition_codes, 'includeConditionCodes')
        self.set_flag(request, self.include_non_plottable_events, 'includeNonPlottableEvents')
        self.set_flag(request, self.include_exchange_codes, 'includeExchangeCodes')
        self.set_flag(request, self.return_eids, 'returnEids')
        self.set_flag(request, self.include_broker_codes, 'includeBrokerCodes')
        self.set_flag(request, self.include_rsp_codes, 'includeRpsCodes')
        self.set_flag(request, self.include_bic_mic_codes, 'includeBicMicCodes')
        return request

    def on_tick_data(self, ticks):
        """Process the incoming tick data array"""
        for tick in XmlHelper.node_iter(ticks):
            names = [str(tick.getElement(_).name()) for _ in range(tick.numElements())]
            tickmap = {n: XmlHelper.get_child_value(tick, n) for n in names}
            self.response.ticks.append(tickmap)

    def on_event(self, evt, is_final):
        for msg in XmlHelper.message_iter(evt):
            tdata = msg.getElement('tickData')
            # tickData will have 0 to 1 tickData[] elements
            if tdata.hasElement('tickData'):
                self.on_tick_data(tdata.getElement('tickData'))
