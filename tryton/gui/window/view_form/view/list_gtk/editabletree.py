#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import gtk
import parser
import gettext
import gobject
from itertools import islice, cycle

from tryton.common import MODELACCESS
from tryton.common.date_widget import DateEntry

_ = gettext.gettext


class TreeView(gtk.TreeView):

    def __init__(self):
        super(TreeView, self).__init__()
        self.cells = {}

    def next_column(self, path, column=None, _sign=1):
        columns = self.get_columns()
        if column is None:
            column = columns[-1 * _sign]
        model = self.get_model()
        record = model.get_value(model.get_iter(path), 0)
        if _sign < 0:
            columns.reverse()
        current_idx = columns.index(column) + 1
        for column in islice(cycle(columns), current_idx,
                len(columns) + current_idx):
            if not column.name:
                continue
            field = record[column.name]
            field.state_set(record, states=('readonly', 'invisible'))
            invisible = field.get_state_attrs(record).get('invisible', False)
            readonly = field.get_state_attrs(record).get('readonly', False)
            if not (invisible or readonly):
                break
        return column

    def prev_column(self, path, column=None):
        return self.next_column(path, column=column, _sign=-1)


class EditableTreeView(TreeView):
    leaving_record_events = (gtk.keysyms.Up, gtk.keysyms.Down,
            gtk.keysyms.Return)
    leaving_events = leaving_record_events + (gtk.keysyms.Tab,
            gtk.keysyms.ISO_Left_Tab, gtk.keysyms.KP_Enter)

    def __init__(self, position):
        super(EditableTreeView, self).__init__()
        self.editable = position

    def on_quit_cell(self, current_record, fieldname, value, callback=None):
        field = current_record[fieldname]
        cell = self.cells[fieldname]

        # The value has not changed and is valid ... do nothing.
        if value == cell.get_textual_value(current_record) \
                and field.validate(current_record):
            if callback:
                callback()
            return

        try:
            cell.value_from_text(current_record, value, callback=callback)
        except parser.UnsettableColumn:
            return

    def on_open_remote(self, current_record, fieldname, create, value,
            entry=None, callback=None):
        cell = self.cells[fieldname]
        if value != cell.get_textual_value(current_record) or not value:
            changed = True
        else:
            changed = False
        try:
            cell.open_remote(current_record, create, changed, value,
                callback=callback)
        except NotImplementedError:
            pass

    def on_create_line(self):
        access = MODELACCESS[self.screen.model_name]
        model = self.get_model()
        if not access['create'] or (self.screen.size_limit is not None
                and (len(model) >= self.screen.size_limit >= 0)):
            return
        if self.editable == 'top':
            method = model.prepend
        else:
            method = model.append
        new_record = model.group.new()
        res = method(new_record)
        return res

    def set_cursor(self, path, focus_column=None, start_editing=False):
        self.grab_focus()
        if focus_column and (focus_column._type in ('boolean')):
            start_editing = False
        super(EditableTreeView, self).set_cursor(path, focus_column,
                start_editing)

    def set_value(self):
        path, column = self.get_cursor()
        model = self.get_model()
        if not path or not column or not column.name:
            return True
        record = model.get_value(model.get_iter(path), 0)
        field = record[column.name]
        if hasattr(field, 'editabletree_entry'):
            entry = field.editabletree_entry
            if isinstance(entry, gtk.Entry):
                txt = entry.get_text()
            else:
                txt = entry.get_active_text()
            self.on_quit_cell(record, column.name, txt)
        return True

    def on_keypressed(self, entry, event):
        path, column = self.get_cursor()
        model = self.get_model()
        record = model.get_value(model.get_iter(path), 0)

        leaving = False
        if event.keyval == gtk.keysyms.Right:
            if isinstance(entry, gtk.Entry):
                if entry.get_position() >= \
                        len(entry.get_text().decode('utf-8')) \
                        and not entry.get_selection_bounds():
                    leaving = True
            else:
                leaving = True
        elif event.keyval == gtk.keysyms.Left:
            if isinstance(entry, gtk.Entry):
                if entry.get_position() <= 0 \
                        and not entry.get_selection_bounds():
                    leaving = True
            else:
                leaving = True

        if event.keyval in self.leaving_events or leaving:
            if isinstance(entry, gtk.Entry):
                if isinstance(entry, DateEntry):
                    entry.date_get()
                txt = entry.get_text()
            else:
                txt = entry.get_active_text()
            keyval = event.keyval
            entry.handler_block(entry.editing_done_id)

            def callback():
                entry.handler_unblock(entry.editing_done_id)
                field = record[column.name]
                # Must wait the edited entry came back in valid state
                if field.validate(record):
                    if (keyval in (gtk.keysyms.Tab, gtk.keysyms.KP_Enter)
                            or (keyval == gtk.keysyms.Right and leaving)):
                        gobject.idle_add(self.set_cursor, path,
                            self.next_column(path, column), True)
                    elif (keyval == gtk.keysyms.ISO_Left_Tab
                            or (keyval == gtk.keysyms.Left and leaving)):
                        gobject.idle_add(self.set_cursor, path,
                            self.prev_column(path, column), True)
                    elif keyval in self.leaving_record_events:
                        fields = self.cells.keys()
                        if not record.validate(fields):
                            invalid_fields = record.invalid_fields
                            col = None
                            for col in self.get_columns():
                                if col.name in invalid_fields:
                                    break
                            gobject.idle_add(self.set_cursor, path, col, True)
                            return
                        if ((self.screen.pre_validate
                                    and not record.pre_validate())
                                or (not self.screen.parent
                                    and not record.save())):
                            gobject.idle_add(self.set_cursor, path, column,
                                True)
                            return
                        entry.handler_block(entry.editing_done_id)
                        if keyval == gtk.keysyms.Up:
                            self._key_up(path, model, column)
                        elif keyval == gtk.keysyms.Down:
                            self._key_down(path, model, column)
                        elif keyval == gtk.keysyms.Return:
                            if self.editable == 'top':
                                new_path = self._key_up(path, model)
                            else:
                                new_path = self._key_down(path, model)
                            gobject.idle_add(self.set_cursor, new_path,
                                self.next_column(new_path), True)
                        entry.handler_unblock(entry.editing_done_id)
                else:
                    gobject.idle_add(self.set_cursor, path, column, True)
            self.on_quit_cell(record, column.name, txt, callback=callback)
            return True
        elif event.keyval in (gtk.keysyms.F3, gtk.keysyms.F2):
            if isinstance(entry, gtk.Entry):
                value = entry.get_text()
            else:
                value = entry.get_active_text()
            entry.handler_block(entry.editing_done_id)

            def callback():
                cell = self.cells[column.name]
                value = cell.get_textual_value(record)
                if isinstance(entry, gtk.Entry):
                    entry.set_text(value)
                else:
                    entry.set_active_text(value)
                entry.handler_unblock(entry.editing_done_id)
            self.on_open_remote(record, column.name,
                create=(event.keyval == gtk.keysyms.F3), value=value,
                callback=callback)
        else:
            field = record[column.name]
            if isinstance(entry, gtk.Entry):
                entry.set_max_length(int(field.attrs.get('size', 0)))
            # store in the record the entry widget to get the value in
            # set_value
            field.editabletree_entry = entry

            def remove_widget(cell):
                if hasattr(field, 'editabletree_entry'):
                    del field.editabletree_entry
            entry.connect('remove-widget', remove_widget)
            record.modified_fields.setdefault(column.name)
            return False

        return True

    def _key_down(self, path, model, column=None):
        if path[0] == len(model) - 1 and self.editable == 'bottom':
            self.on_create_line()
        new_path = (path[0] + 1) % len(model)
        if not column:
            column = self.next_column(new_path)
        self.set_cursor(new_path, column, True)
        self.scroll_to_cell(new_path)
        return new_path

    def _key_up(self, path, model, column=None):
        if path[0] == 0 and self.editable == 'top':
            self.on_create_line()
            new_path = 0
        else:
            new_path = (path[0] - 1) % len(model)
        if not column:
            column = self.next_column(new_path)
        self.set_cursor(new_path, column, True)
        self.scroll_to_cell(new_path)
        return new_path

    def on_editing_done(self, entry):
        path, column = self.get_cursor()
        if not path:
            return True
        model = self.get_model()
        record = model.get_value(model.get_iter(path), 0)
        if isinstance(entry, gtk.Entry):
            if isinstance(entry, DateEntry):
                entry.date_get()
            self.on_quit_cell(record, column.name, entry.get_text())
        elif isinstance(entry, (gtk.ComboBoxEntry, gtk.ComboBox)):
            self.on_quit_cell(record, column.name, entry.get_active_text())
