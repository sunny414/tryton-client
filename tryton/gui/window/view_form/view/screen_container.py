#This file is part of Tryton.  The COPYRIGHT file at the top level of
#this repository contains the full copyright notices and license terms.
import gtk
import gettext
import operator
import gobject
import collections

import tryton.common as common
from tryton.common.domain_parser import quote
from tryton.common.placeholder_entry import PlaceholderEntry
from tryton.translate import date_format
from tryton.config import TRYTON_ICON
from tryton.pyson import PYSONDecoder

_ = gettext.gettext


class Dates(gtk.HBox):

    def __init__(self, format_):
        super(Dates, self).__init__()
        self.from_ = common.date_widget.DateEntry(format_)
        self.pack_start(self.from_, expand=True, fill=True)
        self.pack_start(gtk.Label(_('..')), expand=False, fill=False)
        self.to = common.date_widget.DateEntry(format_)
        self.pack_start(self.to, expand=True, fill=True)

    def get_value(self):
        from_ = self.from_.get_text()
        to = self.to.get_text()
        if from_ and to:
            if from_ != to:
                return '%s..%s' % (quote(from_), quote(to))
            else:
                return quote(from_)
        elif from_:
            return '>=%s' % quote(from_)
        elif to:
            return '<%s' % quote(to)


class Selection(gtk.ScrolledWindow):

    def __init__(self, selections):
        super(Selection, self).__init__()
        self.treeview = gtk.TreeView()
        model = gtk.ListStore(gobject.TYPE_STRING)
        for selection in selections:
            model.append((selection,))
        self.treeview.set_model(model)

        column = gtk.TreeViewColumn()
        cell = gtk.CellRendererText()
        column.pack_start(cell)
        column.add_attribute(cell, 'text', 0)
        self.treeview.append_column(column)
        self.treeview.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.treeview.set_headers_visible(False)
        self.add(self.treeview)
        self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

    def get_value(self):
        values = []
        model, paths = self.treeview.get_selection().get_selected_rows()
        for path in paths:
            iter_ = model.get_iter(path)
            values.append(model.get_value(iter_, 0))
        return ';'.join(quote(v) for v in values)


class ScreenContainer(object):

    def __init__(self, tab_domain):
        self.viewport = gtk.Viewport()
        self.viewport.set_shadow_type(gtk.SHADOW_NONE)
        self.vbox = gtk.VBox(spacing=3)
        self.alternate_viewport = gtk.Viewport()
        self.alternate_viewport.set_shadow_type(gtk.SHADOW_NONE)
        self.alternate_view = False
        self.search_window = None
        self.search_table = None
        self.last_search_text = ''
        self.tab_domain = tab_domain or []

        tooltips = common.Tooltips()

        self.filter_vbox = gtk.VBox(spacing=0)
        self.filter_vbox.set_border_width(0)
        hbox = gtk.HBox(homogeneous=False, spacing=0)
        #self.filter_button = gtk.ToggleButton()
        #self.filter_button.set_use_underline(True)
        #self.filter_button.set_label(_('F_ilters'))
        #self.filter_button.set_relief(gtk.RELIEF_NONE)
        #self.filter_button.set_alignment(0.0, 0.5)
        #self.filter_button.connect('toggled', self.search_box)
        #hbox.pack_start(self.filter_button, expand=False, fill=False)

       # self.search_entry = PlaceholderEntry()
       # self.search_entry.set_placeholder_text(_('Search'))
       # self.search_entry.set_alignment(0.0)
        self.completion = gtk.EntryCompletion()
        self.completion.set_model(gtk.ListStore(str))
        self.completion.set_text_column(0)
        self.completion.props.inline_completion = True
        if hasattr(self.completion.props, 'inline_selection'):
            self.completion.props.inline_selection = True
        if hasattr(self.completion.props, 'popup_set_width'):
            self.completion.props.popup_set_width = False
        self.completion.connect('match-selected', self.match_selected)
       # self.search_entry.connect('activate', self.activate)
       # self.search_entry.set_completion(self.completion)
       # self.search_entry.connect('key-press-event', self.key_press)
       # self.search_entry.connect('focus-in-event', self.focus_in)
       # self.search_entry.connect('icon-press', self.icon_press)

       # hbox.pack_start(self.search_entry, expand=True, fill=True)

        def popup(widget):
            menu = widget._menu
            for child in menu.children():
                menu.remove(child)
            if not widget.props.active:
                menu.popdown()
                return

            def menu_position(menu):
                x, y = widget.window.get_origin()
                widget_allocation = widget.get_allocation()
                return (
                    widget_allocation.x + x,
                    widget_allocation.y + widget_allocation.height + y,
                    False
                )

            for id_, name, domain in common.VIEW_SEARCH[
                    self.screen.model_name]:
                menuitem = gtk.MenuItem(name)
                menuitem.connect('activate', self.bookmark_activate, domain)
                menu.add(menuitem)

            menu.show_all()
            menu.popup(None, None, menu_position, 0, 0)

        def deactivate(menuitem, togglebutton):
            togglebutton.props.active = False

       # but_bookmark = gtk.ToggleButton()
        #self.but_bookmark = but_bookmark
       # tooltips.set_tip(but_bookmark, _('Show bookmarks of filters'))
       # img_bookmark = gtk.Image()
       # img_bookmark.set_from_stock('tryton-bookmark',
       #     gtk.ICON_SIZE_SMALL_TOOLBAR)
       # img_bookmark.set_alignment(0.5, 0.5)
       # but_bookmark.add(img_bookmark)
       # but_bookmark.set_relief(gtk.RELIEF_NONE)
        menu = gtk.Menu()
        menu.set_property('reserve-toggle-size', False)
       # menu.connect('deactivate', deactivate, but_bookmark)
       # but_bookmark._menu = menu
       # but_bookmark.connect('toggled', popup)
       # hbox.pack_start(but_bookmark, expand=False, fill=False)

       # but_prev = gtk.Button()
       # self.but_prev = but_prev
       # tooltips.set_tip(but_prev, _('Previous'))
       # but_prev.connect('clicked', self.search_prev)
        img_prev = gtk.Image()
        img_prev.set_from_stock('tryton-go-previous',
                gtk.ICON_SIZE_SMALL_TOOLBAR)
        img_prev.set_alignment(0.5, 0.5)
       # but_prev.add(img_prev)
       # but_prev.set_relief(gtk.RELIEF_NONE)
       # hbox.pack_start(but_prev, expand=False, fill=False)

       # but_next = gtk.Button()
       # self.but_next = but_next
       # tooltips.set_tip(but_next, _('Next'))
       # but_next.connect('clicked', self.search_next)
        img_next = gtk.Image()
        img_next.set_from_stock('tryton-go-next',
                gtk.ICON_SIZE_SMALL_TOOLBAR)
        img_next.set_alignment(0.5, 0.5)
       # but_next.add(img_next)
       # but_next.set_relief(gtk.RELIEF_NONE)
       # hbox.pack_start(but_next, expand=False, fill=False)

        hbox.show_all()
       # hbox.set_focus_chain([self.search_entry])
        self.filter_vbox.pack_start(hbox, expand=False, fill=False)

        hseparator = gtk.HSeparator()
        hseparator.show()
        self.filter_vbox.pack_start(hseparator, expand=False, fill=False)

        if self.tab_domain:
            self.notebook = gtk.Notebook()
            self.notebook.props.homogeneous = True
            self.notebook.set_scrollable(True)
            for name, domain in self.tab_domain:
                label = gtk.Label('_' + name)
                label.set_use_underline(True)
                self.notebook.append_page(gtk.VBox(), label)
            self.filter_vbox.pack_start(self.notebook, expand=True, fill=True)
            self.notebook.show_all()
            # Set the current page before connecting to switch-page to not
            # trigger the search a second times.
            self.notebook.set_current_page(0)
            self.notebook.get_nth_page(0).pack_end(self.viewport)
            self.notebook.connect('switch-page', self.switch_page)
            self.notebook.connect_after('switch-page', self.switch_page_after)
            filter_expand = True
        else:
            self.notebook = None
            self.vbox.pack_end(self.viewport)
            filter_expand = False

        self.vbox.pack_start(self.filter_vbox, expand=filter_expand, fill=True)

       # self.but_next.set_sensitive(False)
       # self.but_prev.set_sensitive(False)

        tooltips.enable()

    def widget_get(self):
        return self.vbox

    def set_screen(self, screen):
        self.screen = screen
        #self.but_bookmark.set_sensitive(
        #    bool(common.VIEW_SEARCH[screen.model_name]))
        self.bookmark_match()

    def show_filter(self):
        if self.filter_vbox:
            self.filter_vbox.show()
        if self.notebook:
            self.notebook.set_show_tabs(True)
            if self.viewport in self.vbox.get_children():
                self.vbox.remove(self.viewport)
                self.notebook.get_nth_page(self.notebook.get_current_page()
                    ).pack_end(self.viewport)

    def hide_filter(self):
        if self.filter_vbox:
            self.filter_vbox.hide()
        #if self.filter_button and self.filter_button.get_active():
         #   self.filter_button.set_active(False)
          #  self.filter_button.toggled()
        if self.notebook:
            self.notebook.set_show_tabs(False)
            if self.viewport not in self.vbox.get_children():
                self.notebook.get_nth_page(self.notebook.get_current_page()
                    ).remove(self.viewport)
                self.vbox.pack_end(self.viewport)

    def set(self, widget):
        if self.alternate_view:
            if self.alternate_viewport.get_child():
                self.alternate_viewport.remove(
                        self.alternate_viewport.get_child())
            if widget == self.viewport.get_child():
                self.viewport.remove(self.viewport.get_child())
            self.alternate_viewport.add(widget)
            self.alternate_viewport.show_all()
            return
        if self.viewport.get_child():
            self.viewport.remove(self.viewport.get_child())
        self.viewport.add(widget)
        self.viewport.show_all()

    def update(self):
        res = self.screen.search_complete(self.get_text())
        model = self.completion.get_model()
        model.clear()
        for r in res:
            model.append([r.strip()])

    def clear(self, widget=None):
       # self.search_entry.set_text('')
        self.bookmark_match()

    def get_text(self):
        return None

    def set_text(self, value):
     #   self.search_entry.set_text(value)
        self.bookmark_match()

    def bookmark_activate(self, menuitem, domain):
        self.set_text(self.screen.domain_parser.string(domain))
        self.do_search()

    def bookmark_match(self):
        current_text = self.get_text()
        current_domain = self.screen.domain_parser.parse(current_text)
      #  self.search_entry.set_icon_activatable(gtk.ENTRY_ICON_SECONDARY,
       #     bool(current_text))
      #  self.search_entry.set_icon_sensitive(gtk.ENTRY_ICON_SECONDARY,
       #     bool(current_text))
       # icon_stock = self.search_entry.get_icon_stock(gtk.ENTRY_ICON_SECONDARY)
        for id_, name, domain in common.VIEW_SEARCH[self.screen.model_name]:
            text = self.screen.domain_parser.string(domain)
            domain = self.screen.domain_parser.parse(text.decode('utf-8'))
            if (text == current_text
                    or domain == current_domain):
               # if icon_stock != 'tryton-star':
                #    self.search_entry.set_icon_from_stock(
                 #       gtk.ENTRY_ICON_SECONDARY, 'tryton-star')
               # self.search_entry.set_icon_tooltip_text(
                #    gtk.ENTRY_ICON_SECONDARY, _('Remove this bookmark'))
                return id_
       # if icon_stock != 'tryton-unstar':
       #     self.search_entry.set_icon_from_stock(gtk.ENTRY_ICON_SECONDARY,
       #         'tryton-unstar')
       # if current_text:
       #     self.search_entry.set_icon_tooltip_text(gtk.ENTRY_ICON_SECONDARY,
       #         _('Bookmark this filter'))
       # else:
       #     self.search_entry.set_icon_tooltip_text(gtk.ENTRY_ICON_SECONDARY,
       #         None)

    def search_next(self, widget=None):
        self.screen.search_next(self.get_text())

    def search_prev(self, widget=None):
        self.screen.search_prev(self.get_text())

    def switch_page(self, notebook, page, page_num):
        current_page = notebook.get_nth_page(notebook.get_current_page())
        current_page.remove(self.viewport)

        new_page = notebook.get_nth_page(page_num)
        new_page.pack_end(self.viewport)

    def switch_page_after(self, notebook, page, page_num):
        self.do_search()
        notebook.grab_focus()

    def get_tab_domain(self):
        if not self.notebook:
            return []
        idx = self.notebook.get_current_page()
        if idx < 0:
            return []
        return self.tab_domain[idx][1]

    def match_selected(self, completion, model, iter):
        def callback():
            self.update()
           # self.search_entry.emit('changed')
        gobject.idle_add(callback)

   # def activate(self, widget):
    #    if not self.search_entry.get_selection_bounds():
     #       self.do_search(widget)

    def do_search(self, widget=None):
        self.screen.search_filter(self.get_text())

   # def set_cursor(self, new=False, reset_view=True):
    #    if self.filter_vbox:
     #       self.search_entry.grab_focus()

    def key_press(self, widget, event):
        gobject.idle_add(self.update)
        gobject.idle_add(self.bookmark_match)

    def icon_press(self, widget, icon_pos, event):
        if icon_pos == 1:
            icon_stock = self.search_entry.get_icon_stock(icon_pos)
            model_name = self.screen.model_name
            if icon_stock == 'tryton-unstar':
                text = self.get_text()
                if not text:
                    return
                name = common.ask(_('Bookmark Name:'))
                if not name:
                    return
                domain = self.screen.domain_parser.parse(text)
                common.VIEW_SEARCH.add(model_name, name, domain)
                self.set_text(self.screen.domain_parser.string(domain))
            elif icon_stock == 'tryton-star':
                id_ = self.bookmark_match()
                common.VIEW_SEARCH.remove(model_name, id_)
            # Refresh icon and bookmark button
            self.bookmark_match()
           # self.but_bookmark.set_sensitive(
           #     bool(common.VIEW_SEARCH[model_name]))

    def focus_in(self, widget, event):
        self.update()
      #  self.search_entry.emit('changed')

    def search_box(self, button):
        def key_press(window, event):
            if event.keyval == gtk.keysyms.Escape:
                button.set_active(False)
                window.hide()

        def search():
            button.set_active(False)
            self.search_window.hide()
            text = ''
            for label, entry in self.search_table.fields:
                if isinstance(entry, gtk.ComboBox):
                    value = quote(entry.get_active_text())
                elif isinstance(entry, (Dates, Selection)):
                    value = entry.get_value()
                else:
                    value = quote(entry.get_text())
                if value:
                    text += label + ' ' + value + ' '
            self.set_text(text)
            self.last_search_text = self.get_text()
            self.do_search()

        def date_activate(entry):
            entry._focus_out(entry, None)
            search()

        if not self.search_window:
            self.search_window = gtk.Window()
            self.search_window.set_transient_for(button.get_toplevel())
            self.search_window.set_type_hint(
                gtk.gdk.WINDOW_TYPE_HINT_POPUP_MENU)
            self.search_window.set_destroy_with_parent(True)
            self.search_window.set_title('Tryton')
            self.search_window.set_icon(TRYTON_ICON)
            self.search_window.set_decorated(False)
            if hasattr(self.search_window, 'set_deletable'):
                self.search_window.set_deletable(False)
            self.search_window.connect('key-press-event', key_press)
            vbox = gtk.VBox()
            fields = [f for f in self.screen.domain_parser.fields.itervalues()
                if f.get('searchable', True)]
            if (not hasattr(collections, 'OrderedDict')
                    or not isinstance(self.screen.domain_parser.fields,
                        collections.OrderedDict)):
                fields.sort(key=operator.itemgetter('string'))
            self.search_table = gtk.Table(rows=len(fields), columns=2)
            self.search_table.set_homogeneous(False)
            self.search_table.set_border_width(5)
            self.search_table.set_row_spacings(2)
            self.search_table.set_col_spacings(2)

            # Fill table with fields
            self.search_table.fields = []
            for i, field in enumerate(fields):
                label = gtk.Label(field['string'])
                label.set_alignment(0.0, 0.5)
                self.search_table.attach(label, 0, 1, i, i + 1, yoptions=False)
                yoptions = False
                if field['type'] == 'boolean':
                    if hasattr(gtk, 'ComboBoxText'):
                        entry = gtk.ComboBoxText()
                    else:
                        entry = gtk.combo_box_new_text()
                    entry.append_text('')
                    selections = (_('True'), _('False'))
                    for selection in selections:
                        entry.append_text(selection)
                elif field['type'] == 'selection':
                    selections = tuple(x[1] for x in field['selection'])
                    entry = Selection(selections)
                    yoptions = gtk.FILL | gtk.EXPAND
                elif field['type'] in ('date', 'datetime', 'time'):
                    if field['type'] == 'date':
                        format_ = date_format()
                    elif field['type'] in ('datetime', 'time'):
                        format_ = PYSONDecoder({}).decode(field['format'])
                        if field['type'] == 'datetime':
                            format_ = date_format() + ' ' + format_
                    entry = Dates(format_)
                    entry.from_.connect('activate', date_activate)
                    entry.to.connect('activate', date_activate)
                else:
                    entry = gtk.Entry()
                    entry.connect('activate', lambda *a: search())
                self.search_table.attach(entry, 1, 2, i, i + 1,
                    yoptions=yoptions)
                self.search_table.fields.append((field['string'] + ':', entry))

            scrolled = gtk.ScrolledWindow()
            scrolled.add_with_viewport(self.search_table)
            scrolled.set_shadow_type(gtk.SHADOW_NONE)
            vbox.pack_start(scrolled, expand=True, fill=True)
            find_button = gtk.Button(_('Find'))
            find_button.connect('clicked', lambda *a: search())
            find_img = gtk.Image()
            find_img.set_from_stock('tryton-find', gtk.ICON_SIZE_SMALL_TOOLBAR)
            find_button.set_image(find_img)
            hbuttonbox = gtk.HButtonBox()
            hbuttonbox.set_spacing(5)
            hbuttonbox.pack_start(find_button)
            hbuttonbox.set_layout(gtk.BUTTONBOX_END)
            vbox.pack_start(hbuttonbox, expand=False, fill=True)
            self.search_window.add(vbox)
            vbox.show_all()

            # Disable scrolling:
            scrolled.set_policy(gtk.POLICY_NEVER, gtk.POLICY_NEVER)
            # See what changed:
            new_size = self.search_window.size_request()
            # Reenable scrolling:
            scrolled.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
            self.search_window.set_default_size(*new_size)

        parent = button.get_toplevel()
        button_x, button_y = button.translate_coordinates(parent,
            *parent.window.get_origin())
        button_allocation = button.get_allocation()

        # Resize the window to not be out of the screen
        width, height = self.search_window.get_default_size()
        screen = self.search_window.get_screen()
        screen_width = screen.get_width()
        screen_height = screen.get_height()
        delta_width = screen_width - (button_x + width)
        delta_height = screen_height - (button_y + button_allocation.height
            + height)
        if delta_width < 0:
            width += delta_width
        if delta_height < 0:
            height += delta_height
        self.search_window.resize(width, height)

        # Move the window under the button
        self.search_window.move(button_x,
            button_y + button_allocation.height)

        from tryton.gui.main import Main
        page = Main.get_main().get_page()
        if button.get_active():
            if page and self.search_window not in page.dialogs:
                page.dialogs.append(self.search_window)
            self.search_window.show()

            if self.last_search_text.strip() != self.get_text().strip():
                for label, entry in self.search_table.fields:
                    if isinstance(entry, gtk.ComboBox):
                        entry.set_active(-1)
                    elif isinstance(entry, Dates):
                        entry.from_.set_text('')
                        entry.to.set_text('')
                    elif isinstance(entry, Selection):
                        entry.treeview.get_selection().unselect_all()
                    else:
                        entry.set_text('')
                if self.search_table.fields:
                    self.search_table.fields[0][1].grab_focus()

        else:
            self.search_window.hide()
            if page and self.search_window in page.dialogs:
                page.dialogs.remove(self.search_window)
