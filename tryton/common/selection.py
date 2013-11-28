#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import operator

from tryton.common import RPCExecute, RPCException


class SelectionMixin(object):

    def __init__(self, *args, **kwargs):
        super(SelectionMixin, self).__init__(*args, **kwargs)
        self.selection = None
        self._last_domain = None
        self._values2selection = {}
        self._domain_cache = {}

    def init_selection(self, key=None):
        if key is None:
            key = tuple(sorted((k, None)
                    for k in self.attrs.get('selection_change_with') or []))
        selection = self.attrs.get('selection', [])[:]
        if (not isinstance(selection, (list, tuple))
                and key not in self._values2selection):
            try:
                if key:
                    selection = RPCExecute('model', self.model_name, selection,
                        dict(key))
                else:
                    selection = RPCExecute('model', self.model_name, selection)
            except RPCException:
                selection = []
            self._values2selection[key] = selection
        elif key in self._values2selection:
            selection = self._values2selection[key]
        if self.attrs.get('sort', True):
            selection.sort(key=operator.itemgetter(1))
        self.selection = selection[:]

    def update_selection(self, record, field):
        if not field:
            return

        if 'relation' not in self.attrs:
            change_with = self.attrs.get('selection_change_with') or []
            key = record._get_on_change_args(change_with).items()
            key.sort()
            self.init_selection(tuple(key))
        else:
            domain = field.domain_get(record)
            context = record[self.field_name].context_get(record)
            domain_cache_key = str(domain) + str(context)
            if domain_cache_key in self._domain_cache:
                self.selection = self._domain_cache[domain_cache_key]
                self._last_domain = (domain, context)
            if (domain, context) == self._last_domain:
                return

            try:
                result = RPCExecute('model', self.attrs['relation'],
                    'search_read', domain, 0, None, None, ['rec_name'],
                    context=context)
            except RPCException:
                result = False
            if isinstance(result, list):
                selection = [(x['id'], x['rec_name']) for x in result]
                selection.append((None, ''))
                self._last_domain = (domain, context)
                self._domain_cache[domain_cache_key] = selection
            else:
                selection = []
                self._last_domain = None
            self.selection = selection[:]
