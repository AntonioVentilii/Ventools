import blpapi
import numpy as np
import pandas as pd

from bbg.eqs import EQSRequest
from bbg.historical_data import HistoricalDataRequest
from bbg.intraday_bar import IntradayBarRequest
from bbg.intraday_tick import IntradayTickRequest
from bbg.logger import LOGGER, instance_logger
from bbg.reference_data import ReferenceDataRequest
from bbg.utils import XmlHelper


class Terminal(object):
    """Submits requests to the Bloomberg Terminal and dispatches the events back to the request
    object for processing.
    """

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.logger = instance_logger(repr(self), self)

    def __repr__(self):
        fmtargs = dict(clz=self.__class__.__name__, host=self.host, port=self.port)
        return '<{clz}({host}:{port})'.format(**fmtargs)

    def _create_session(self):
        opts = blpapi.SessionOptions()
        opts.setServerHost(self.host)
        opts.setServerPort(self.port)
        return blpapi.Session(opts)

    def check_session(self):
        opts = blpapi.SessionOptions()
        opts.setServerHost(self.host)
        opts.setServerPort(self.port)
        opts.setNumStartAttempts(1)
        session = blpapi.Session(opts)
        check = session.start()
        session.stop()
        return check

    def execute(self, request):
        session = self._create_session()
        if not session.start():
            raise Exception('failed to start session')

        try:
            self.logger.info('executing request: %s' % repr(request))
            if not session.openService(request.svc_name):
                raise Exception('failed to open service %s' % request.svc_name)

            svc = session.getService(request.svc_name)
            asbbg = request.get_bbg_request(svc, session)
            # setup response capture
            request.new_response()
            session.sendRequest(asbbg)
            while True:
                evt = session.nextEvent(500)
                if evt.eventType() == blpapi.Event.RESPONSE:
                    request.on_event(evt, is_final=True)
                    break
                elif evt.eventType() == blpapi.Event.PARTIAL_RESPONSE:
                    request.on_event(evt, is_final=False)
                else:
                    request.on_admin_event(evt)
            request.has_exception and request.raise_exception()
            return request.response
        finally:
            session.stop()

    def get_historical(self, sids, flds, start=None, end=None, period=None, ignore_security_error=0,
                       ignore_field_error=0, **overrides):
        req = HistoricalDataRequest(sids, flds, start=start, end=end, period=period,
                                    ignore_security_error=ignore_security_error,
                                    ignore_field_error=ignore_field_error,
                                    **overrides)
        return self.execute(req)

    def get_reference_data(self, sids, flds, ignore_security_error=0, ignore_field_error=0, **overrides):
        req = ReferenceDataRequest(sids, flds, ignore_security_error=ignore_security_error,
                                   ignore_field_error=ignore_field_error, **overrides)
        return self.execute(req)

    def get_intraday_tick(self, sid, events='TRADE', start=None, end=None, include_condition_codes=None,
                          include_nonplottable_events=None, include_exchange_codes=None, return_eids=None,
                          include_broker_codes=None, include_rsp_codes=None, include_bic_mic_codes=None):
        req = IntradayTickRequest(sid, start=start, end=end, events=events,
                                  include_condition_codes=include_condition_codes,
                                  include_non_plottable_events=include_nonplottable_events,
                                  include_exchange_codes=include_exchange_codes,
                                  return_eids=return_eids, include_broker_codes=include_broker_codes,
                                  include_rsp_codes=include_rsp_codes,
                                  include_bic_mic_codes=include_bic_mic_codes)
        return self.execute(req)

    def get_intraday_bar(self, sid, event='TRADE', start=None, end=None, interval=None, gap_fill_initial_bar=None,
                         return_eids=None, adjustment_normal=None, adjustment_abnormal=None, adjustment_split=None,
                         adjustment_follow_dpdf=None):
        req = IntradayBarRequest(sid, start=start, end=end, event=event, interval=interval,
                                 gap_fill_initial_bar=gap_fill_initial_bar,
                                 return_eids=return_eids, adjustment_normal=adjustment_normal,
                                 adjustment_split=adjustment_split,
                                 adjustment_abnormal=adjustment_abnormal, adjustment_follow_dpdf=adjustment_follow_dpdf)
        return self.execute(req)

    def get_screener(self, name, group='General', type_='GLOBAL', asof=None, language=None):
        req = EQSRequest(name, type_=type_, group=group, asof=asof, language=language)
        return self.execute(req)


class SyncSubscription(object):

    def __init__(self, tickers, fields, interval=None, host='localhost', port=8194):
        self.fields = isinstance(fields, str) and [fields] or fields
        self.tickers = isinstance(tickers, str) and [tickers] or tickers
        self.interval = interval
        self.host = host
        self.port = port
        self.session = None
        # build an empty frame
        n_rows, n_cols = len(self.tickers), len(self.fields)
        vals = np.repeat(np.nan, n_rows * n_cols).reshape((n_rows, n_cols))
        self.frame = pd.DataFrame(vals, columns=self.fields, index=self.tickers)

    def _init(self):
        # init session
        opts = blpapi.SessionOptions()
        opts.setServerHost(self.host)
        opts.setServerPort(self.port)
        self.session = session = blpapi.Session(opts)
        if not session.start():
            raise Exception('failed to start session')

        if not session.openService('//blp/mktdata'):
            raise Exception('failed to open service')

        # init subscriptions
        subs = blpapi.SubscriptionList()
        flds = ','.join(self.fields)
        istr = self.interval and 'interval=%.1f' % self.interval or ''
        for ticker in self.tickers:
            subs.add(ticker, flds, istr, blpapi.CorrelationId(ticker))
        session.subscribe(subs)

    @staticmethod
    def on_subscription_status(evt):
        for msg in XmlHelper.message_iter(evt):
            if msg.messageType() == 'SubscriptionFailure':
                sid = msg.correlationIds()[0].value()
                desc = msg.getElement('reason').getElementAsString('description')
                raise Exception('subscription failed sid=%s desc=%s' % (sid, desc))

    def on_subscription_data(self, evt):
        for msg in XmlHelper.message_iter(evt):
            sid = msg.correlationIds()[0].value()
            ridx = self.tickers.index(sid)
            for cidx, fld in enumerate(self.fields):
                if msg.hasElement(fld.upper()):
                    val = XmlHelper.get_child_value(msg, fld.upper())
                    self.frame.iloc[ridx, cidx] = val

    def check_for_updates(self, timeout=500):
        if self.session is None:
            self._init()
        evt = self.session.nextEvent(timeout)
        if evt.eventType() == blpapi.Event.SUBSCRIPTION_DATA:
            LOGGER.info('next(): subscription data')
            self.on_subscription_data(evt)
        elif evt.eventType() == blpapi.Event.SUBSCRIPTION_STATUS:
            LOGGER.info('next(): subscription status')
            self.on_subscription_status(evt)
            self.check_for_updates(timeout)
        elif evt.eventType() == blpapi.Event.TIMEOUT:
            pass
        else:
            LOGGER.info('next(): ignoring event %s' % evt.eventType())
            self.check_for_updates(timeout)


LocalTerminal = Terminal('localhost', 8194)
