import logging
from collections import defaultdict, namedtuple
from datetime import datetime

import blpapi
import numpy as np
import pandas as pd

from bbg.logger import LOGGER

SecurityErrorAttrs = ['security', 'source', 'code', 'category', 'message', 'subcategory']
SecurityError = namedtuple('SecurityError', SecurityErrorAttrs)
FieldErrorAttrs = ['security', 'field', 'source', 'code', 'category', 'message', 'subcategory']
FieldError = namedtuple('FieldError', FieldErrorAttrs)


class XmlHelper(object):

    @staticmethod
    def security_iter(node_arr):
        """
        provide a security data iterator by returning a tuple of (Element, SecurityError) which are mutually exclusive
        """
        assert node_arr.name() == 'securityData' and node_arr.isArray()
        for i in range(node_arr.numValues()):
            node = node_arr.getValue(i)
            err = XmlHelper.get_security_error(node)
            result = (None, err) if err else (node, None)
            yield result

    @staticmethod
    def node_iter(node_arr):
        assert node_arr.isArray()
        for i in range(node_arr.numValues()):
            yield node_arr.getValue(i)

    @staticmethod
    def message_iter(evt):
        """ provide a message iterator which checks for a response error prior to returning """
        for msg in evt:
            if LOGGER.isEnabledFor(logging.DEBUG):
                LOGGER.debug(msg.toString())
            if msg.asElement().hasElement('responseError'):
                raise Exception(msg.toString())
            yield msg

    @staticmethod
    def get_sequence_value(node):
        """Convert an element with DataType Sequence to a DataFrame.
        Note this may be a naive implementation as I assume that bulk data is always a table
        """
        assert node.datatype() == 15
        data = defaultdict(list)
        cols = []
        for i in range(node.numValues()):
            row = node.getValue(i)
            if i == 0:  # Get the ordered cols and assume they are constant
                cols = [str(row.getElement(_).name()) for _ in range(row.numElements())]

            for cidx in range(row.numElements()):
                col = row.getElement(cidx)
                data[str(col.name())].append(XmlHelper.as_value(col))
        return pd.DataFrame(data, columns=cols)

    @staticmethod
    def as_value(ele):
        """ convert the specified element as a python value """
        dtype = ele.datatype()
        # print '%s = %s' % (ele.name(), dtype)
        if dtype in (1, 2, 3, 4, 5, 6, 7, 9, 12):
            # BOOL, CHAR, BYTE, INT32, INT64, FLOAT32, FLOAT64, BYTEARRAY, DECIMAL)
            return ele.getValue()
        elif dtype == 8:  # String
            val = ele.getValue()
            """
            if val:
                # us centric :)
                val = val.encode('ascii', 'replace')
            """
            return str(val)
        elif dtype == 10:  # Date
            if ele.isNull():
                return pd.NaT
            else:
                v = ele.getValue()
                return datetime(year=v.year, month=v.month, day=v.day) if v else pd.NaT
        elif dtype == 11:  # Time
            if ele.isNull():
                return pd.NaT
            else:
                v = ele.getValue()
                now = pd.datetime.now()
                return datetime(year=now.year, month=now.month, day=now.day, hour=v.hour, minute=v.minute,
                                second=v.second).time() if v else np.nan
        elif dtype == 13:  # Datetime
            if ele.isNull():
                return pd.NaT
            else:
                v = ele.getValue()
                return v
        elif dtype == 14:  # Enumeration
            # raise NotImplementedError('ENUMERATION data type needs implemented')
            return str(ele.getValue())
        elif dtype == 16:  # Choice
            raise NotImplementedError('CHOICE data type needs implemented')
        elif dtype == 15:  # SEQUENCE
            return XmlHelper.get_sequence_value(ele)
        else:
            raise NotImplementedError('Unexpected data type %s. Check documentation' % dtype)

    @staticmethod
    def get_child_value(parent, name, allow_missing=0):
        """ return the value of the child element with name in the parent Element """
        if not parent.hasElement(name):
            if allow_missing:
                return np.nan
            else:
                raise Exception('failed to find child element %s in parent' % name)
        else:
            return XmlHelper.as_value(parent.getElement(name))

    @staticmethod
    def get_child_values(parent, names):
        """ return a list of values for the specified child fields. If field not in Element then replace with nan. """
        vals = []
        for name in names:
            if parent.hasElement(name):
                vals.append(XmlHelper.as_value(parent.getElement(name)))
            else:
                vals.append(np.nan)
        return vals

    @staticmethod
    def as_security_error(node, secid):
        """ convert the securityError element to a SecurityError """
        assert node.name() == 'securityError'
        src = XmlHelper.get_child_value(node, 'source')
        code = XmlHelper.get_child_value(node, 'code')
        cat = XmlHelper.get_child_value(node, 'category')
        msg = XmlHelper.get_child_value(node, 'message')
        subcat = XmlHelper.get_child_value(node, 'subcategory')
        return SecurityError(security=secid, source=src, code=code, category=cat, message=msg, subcategory=subcat)

    @staticmethod
    def as_field_error(node, secid):
        """ convert a fieldExceptions element to a FieldError or FieldError array """
        assert node.name() == 'fieldExceptions'
        if node.isArray():
            return [XmlHelper.as_field_error(node.getValue(_), secid) for _ in range(node.numValues())]
        else:
            fld = XmlHelper.get_child_value(node, 'fieldId')
            info = node.getElement('errorInfo')
            src = XmlHelper.get_child_value(info, 'source')
            code = XmlHelper.get_child_value(info, 'code')
            cat = XmlHelper.get_child_value(info, 'category')
            msg = XmlHelper.get_child_value(info, 'message')
            subcat = XmlHelper.get_child_value(info, 'subcategory')
            return FieldError(security=secid, field=fld, source=src, code=code, category=cat, message=msg,
                              subcategory=subcat)

    @staticmethod
    def get_security_error(node):
        """ return a SecurityError if the specified securityData element has one, else return None """
        assert node.name() == 'securityData' and not node.isArray()
        if node.hasElement('securityError'):
            secid = XmlHelper.get_child_value(node, 'security')
            err = XmlHelper.as_security_error(node.getElement('securityError'), secid)
            return err
        else:
            return None

    @staticmethod
    def get_field_errors(node):
        """ return a list of FieldErrors if the specified securityData element has field errors """
        assert node.name() == 'securityData' and not node.isArray()
        node_arr = node.getElement('fieldExceptions')
        if node_arr.numValues() > 0:
            secid = XmlHelper.get_child_value(node, 'security')
            errors = XmlHelper.as_field_error(node_arr, secid)
            return errors
        else:
            return None


def debug_event(evt):
    print('unhandled event: %s' % evt.EventType)
    if evt.EventType in [blpapi.Event.RESPONSE, blpapi.Event.PARTIAL_RESPONSE]:
        print('messages:')
        for msg in XmlHelper.message_iter(evt):
            print(msg.Print)
