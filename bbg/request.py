class Request(object):

    def __init__(self, svc_name, ignore_security_error=0, ignore_field_error=0):
        self.field_errors = []
        self.security_errors = []
        self.ignore_security_error = ignore_security_error
        self.ignore_field_error = ignore_field_error
        self.svc_name = svc_name
        self.response = None

    def new_response(self):
        raise NotImplementedError('subclass must implement')

    @property
    def has_exception(self):
        if not self.ignore_security_error and len(self.security_errors) > 0:
            return True
        if not self.ignore_field_error and len(self.field_errors) > 0:
            return True

    def raise_exception(self):
        if not self.ignore_security_error and len(self.security_errors) > 0:
            msgs = ['(%s, %s, %s)' % (s.security, s.category, s.message) for s in self.security_errors]
            raise Exception('SecurityError: %s' % ','.join(msgs))
        if not self.ignore_field_error and len(self.field_errors) > 0:
            msgs = ['(%s, %s, %s, %s)' % (s.security, s.field, s.category, s.message) for s in self.field_errors]
            raise Exception('FieldError: %s' % ','.join(msgs))
        raise Exception('Programmer Error: No exception to raise')

    def get_bbg_request(self, svc, session):
        raise NotImplementedError()

    def on_event(self, evt, is_final):
        raise NotImplementedError()

    def on_admin_event(self, evt):
        pass

    @staticmethod
    def apply_overrides(request, overrides):
        if overrides:
            for k, v in overrides.items():
                o = request.getElement('overrides').appendElement()
                o.setElement('fieldId', k)
                o.setElement('value', v)

    @staticmethod
    def set_flag(request, val, fld):
        """If the specified val is not None, then set the specified field to its boolean value"""
        if val is not None:
            val = bool(val)
            request.set(fld, val)

    def set_response(self, response):
        """Set the response to handle and store the results """
        self.response = response
