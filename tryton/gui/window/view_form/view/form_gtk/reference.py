#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import gtk
import gettext

from many2one import Many2One
from .selection import PopdownMixin
from tryton.common.selection import SelectionMixin

_ = gettext.gettext


class Reference(Many2One, SelectionMixin, PopdownMixin):

    def __init__(self, field_name, model_name, attrs=None):
        super(Reference, self).__init__(field_name, model_name, attrs=attrs)

        self.widget_combo = gtk.ComboBoxEntry()
        child = self.widget_combo.get_child()
        child.set_editable(False)
        child.connect('changed', self.sig_changed_combo)
        self.widget.pack_start(self.widget_combo, expand=False, fill=True)

        self.widget.pack_start(gtk.Label('-'), expand=False, fill=False)

        self.init_selection()
        self.set_popdown(self.selection, self.widget_combo)

        self.widget.set_focus_chain([self.widget_combo, self.wid_text])

    def grab_focus(self):
        return self.widget_combo.grab_focus()

    def get_model(self):
        child = self.widget_combo.get_child()
        res = child.get_text()
        return self._selection.get(res, False)

    def _readonly_set(self, value):
        super(Reference, self)._readonly_set(value)
        if not value:
            self.widget.set_focus_chain([self.widget_combo, self.wid_text])

    def _set_button_sensitive(self):
        super(Reference, self)._set_button_sensitive()
        self.widget_combo.set_sensitive(not self._readonly)

    @property
    def modified(self):
        if self.record and self.field:
            try:
                model, name = self.field.get_client(self.record)
            except (ValueError, TypeError):
                model, name = '', ''
            return (model != self.get_model()
                or name != self.wid_text.get_text())
        return False

    def has_target(self, value):
        if value is None:
            return False
        model, value = value.split(',')
        if not value:
            value = None
        else:
            try:
                value = int(value)
            except ValueError:
                value = None
        result = model == self.get_model() and value >= 0
        return result

    def value_from_id(self, id_, str_=None):
        if str_ is None:
            str_ = ''
        return self.get_model(), (id_, str_)

    @staticmethod
    def id_from_value(value):
        _, value = value.split(',')
        return int(value)

    def sig_changed_combo(self, *args):
        if not self.changed:
            return
        self.wid_text.set_text('')
        self.wid_text.set_position(0)
        self.field.set_client(self.record, (self.get_model(), (-1, '')))

    def set_value(self, record, field):
        if not self.get_model():
            value = self.wid_text.get_text()
            if not value:
                field.set_client(record, None)
            else:
                field.set_client(record, ('', value))
                return
        else:
            try:
                model, name = field.get_client(record)
            except (ValueError, TypeError):
                model, name = '', ''
            if (model != self.get_model()
                    or name != self.wid_text.get_text()):
                field.set_client(record, None)
                self.wid_text.set_text('')

    def set_text(self, value):
        if value:
            model, value = value
        else:
            model, value = None, None
        super(Reference, self).set_text(value)
        child = self.widget_combo.get_child()
        reverse_selection = dict((v, k)
            for k, v in self._selection.iteritems())
        if model:
            child.set_text(reverse_selection[model])
            child.set_position(len(reverse_selection[model]))
        else:
            child.set_text('')
            child.set_position(0)

    def display(self, record, field):
        self.update_selection(record, field)
        self.set_popdown(self.selection, self.widget_combo)
        super(Reference, self).display(record, field)
