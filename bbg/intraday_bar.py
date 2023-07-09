import pandas as pd

from bbg.request import Request
from bbg.utils import XmlHelper


class IntradayBarResponse(object):

    def __init__(self, request):
        self.request = request
        self.bars = []  # array of dicts

    def as_frame(self):
        return pd.DataFrame.from_records(self.bars)


class IntradayBarRequest(Request):

    def __init__(self, sid, start=None, end=None, event='TRADE', interval=None, gap_fill_initial_bar=None,
                 return_eids=None, adjustment_normal=None, adjustment_abnormal=None, adjustment_split=None,
                 adjustment_follow_dpdf=None):
        """
        Parameters
        ----------
        event: [TRADE, BID, ASK, BID_BEST, ASK_BEST, BEST_BID, BEST_ASK]
        interval: int, between 1 and 1440 in minutes. If omitted, defaults to 1 minute
        gap_fill_initial_bar: bool
                            If True, bar contains previous values if not ticks during the interval
        """
        Request.__init__(self, '//blp/refdata')
        self.sid = sid
        self.event = event
        self.interval = interval
        self.gap_fill_initial_bar = gap_fill_initial_bar
        self.return_eids = return_eids
        self.adjustment_normal = adjustment_normal
        self.adjustment_abnormal = adjustment_abnormal
        self.adjustment_split = adjustment_split
        self.adjustment_follow_DPDF = adjustment_follow_dpdf
        self.end = end = pd.to_datetime(end) if end else pd.to_datetime('now')
        self.start = pd.to_datetime(start) if start else end + pd.DateOffset(hours=-1)

    def __repr__(self):
        fmtargs = dict(clz=self.__class__.__name__,
                       sid=self.sid,
                       event=self.event,
                       start=self.start,
                       end=self.end,
                       interval=self.interval)
        return '<{clz}({sid}, {event}, start={start}, end={end}), interval={interval}'.format(**fmtargs)

    def new_response(self):
        self.response = IntradayBarResponse(self)

    def get_bbg_request(self, svc, session):
        # create the bloomberg request object
        request = svc.createRequest('IntradayBarRequest')
        request.set('security', self.sid)
        request.set('eventType', self.event)
        request.set('startDateTime', self.start)
        request.set('endDateTime', self.end)
        request.set('interval', self.interval or 1)
        self.set_flag(request, self.gap_fill_initial_bar, 'gapFillInitialBar')
        self.set_flag(request, self.return_eids, 'returnEids')
        self.set_flag(request, self.adjustment_normal, 'adjustmentNormal')
        self.set_flag(request, self.adjustment_abnormal, 'adjustmentAbnormal')
        self.set_flag(request, self.adjustment_split, 'adjustmentSplit')
        self.set_flag(request, self.adjustment_follow_DPDF, 'adjustmentFollowDPDF')
        return request

    def on_bar_data(self, bars):
        """Process the incoming tick data array"""
        for tick in XmlHelper.node_iter(bars):
            names = [str(tick.getElement(_).name()) for _ in range(tick.numElements())]
            barmap = {n: XmlHelper.get_child_value(tick, n) for n in names}
            self.response.bars.append(barmap)

    def on_event(self, evt, is_final):
        for msg in XmlHelper.message_iter(evt):
            data = msg.getElement('barData')
            # tickData will have 0 to 1 tickData[] elements
            if data.hasElement('barTickData'):
                self.on_bar_data(data.getElement('barTickData'))
