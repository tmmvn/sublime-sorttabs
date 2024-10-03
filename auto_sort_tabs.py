import sublime, sublime_plugin
import time
import os
from operator import itemgetter
from itertools import groupby


class AutoSortTabsListener(sublime_plugin.EventListener):
	def on_load(self, view):
		if not self._run_sort(view):
			view.settings().set('sorttabs_tosort', True)

	def on_post_save(self, view):
		self._run_sort(view)

	def on_activated(self, view):
		view.settings().set('sorttabs_lastactivated', time.time())
		if view.settings().get('sorttabs_tosort'):
			if self._run_sort(view):
				view.settings().erase('sorttabs_tosort')

	def _run_sort(self, view):
		if view.window() and view.window().get_view_index(view)[1] != -1:
			view.window().run_command("sort_tabs")
			return True
		return False


class SortTabsCommand(sublime_plugin.WindowCommand):
	sorting_indexes = (1, 2)

	def run(self, sort=True, close=False):
		# save active view to restore it later
		self.current_view = self.window.active_view()
		list_views = []
		# init, fill, and sort list_views
		self.init_file_views(list_views)
		self.fill_list_views(list_views)
		self.sort_list_views(list_views)
		message = ''
		if sort:
			self.sort_views(list_views)
			message = '%s' % (self.description(), )
		if close is not False:
			closed_view = self.close_views(list_views, close)
			message = 'Closed %i view(s) using %s' % (closed_view, self.description())
		if message:
			sublime.status_message(message)
		# restore active view
		self.window.focus_view(self.current_view)

	def init_file_views(self, list_views):
		for view in self.window.views():
			group, _ = self.window.get_view_index(view)
			list_views.append([view, group])

	def fill_list_views(self, list_views):
		for item in list_views:
			filename = os.path.basename(item[0].file_name() if item[0].file_name() else '')
			item.append(filename.lower())

	def sort_list_views(self, list_views):
		# sort list_views using sorting_indexes
		list_views.sort(key=itemgetter(*self.sorting_indexes))

	def sort_views(self, list_views):
		# sort views according to list_views
		for group, groupviews in groupby(list_views, itemgetter(1)):
			for index, view in enumerate(v[0] for v in groupviews):
				# remove flag for auto sorting
				view.settings().erase('sorttabs_tosort')
				if self.window.get_view_index(view) != (group, index):
					self.window.set_view_index(view, group, index)

	def close_views(self, list_views, close):
		if close < 0:
			# close is a percent of opened views
			close = int(len(list_views) / 100.0 * abs(close))
		close = close if close else 1
		closed = 0
		for view in (v[0] for v in list_views[-close:]):
			if view.id() != self.current_view.id() and not view.is_dirty() and not view.is_scratch():
				self.window.focus_view(view)
				self.window.run_command('close_file')
				closed += 1
		return closed

	def description(self, *args):
		# use class __doc__ for description
		return self.__doc__
