"""
Created on Feb 18, 2017

@author: valsr <valsr@valsr.com>
"""
import os
from kivy.logger import Logger

from com.valsr.psb.ui.window.base import WindowBase


class WrongWindowBaseException(Exception):
    """Wrong class base exception"""

    def __init__(self, window_class):
        super().__init__(
            "%s does not derive from com.valsr.psb.ui.window.WindowBase" % window_class)


class WindowManager(object):
    """Window Manager class - manages window's life cycle. Only a single window manager exists in the application."""

    _root_window = None
    _windows = []
    """Root window of the application - also the first window to be created"""

    def __init__(self):
        """Constructor"""
        raise RuntimeError("Do not instantiate WindowManager")

    @staticmethod
    def create_window(window_class, parent, create_opts=None, **args):
        """Create window to be managed by the window manager - call this to create a window object that can be shown to
        the end user

        Args:
            window_class: Class of the window to create
            parent: Parent widget of this window
            create_opts: Create options for window, currently the following are recognized:
                draggable, windowed, size_hint, title
            **args: Arguments to pass to the init method of the window

        Returns:
            Created window
        """
        window = window_class(**args)
        if not isinstance(window, WindowBase):
            raise WrongWindowBaseException(window_class)

        # call on pre-create
        window.on_pre_create()

        if 'draggable' in create_opts:
            window.draggable = create_opts['draggable']

        if 'windowed' in create_opts:
            window.windowed = create_opts['windowed']

        if 'size_hint' in create_opts:
            window.size_hint = create_opts['size_hint']

        if 'title' in create_opts:
            window.title = create_opts['title']

        # call create
        window.create()

        # root?
        if not WindowManager.root_window():
            from kivy.core.window import Window
            Window.add_widget(window)

        # attach to parent
        if not parent and WindowManager._root_window is not window:
            parent = WindowManager._root_window

        if parent:
            window._parent = parent

        WindowManager._windows.append((window.id, window))

        return window

    @staticmethod
    def root_window():
        """Obtain the root window/widget

        Returns:
            WindowBase or Widget
        """
        if not WindowManager._root_window:
            # find it
            from kivy.core.window import Window
            if Window.children:
                WindowManager._root_window = Window.children[0]

        return WindowManager._root_window

    @staticmethod
    def open_window(window_id):
        """Open window by given window_id. This will attach the window to its parent making it visible.

        Args:
            window_id: Window identifier
        """
        window = WindowManager.window(window_id)

        if window:
            if WindowManager.is_visible(window_id):
                Logger.warning("Window %s is already opened", window_id)
                return

            if window.parent_window():
                window.parent_window().add_widget(window)

            window._open()

    @staticmethod
    def close_window(window_id, force=False):
        """Close window by given window_id. This will detach the window from the parent in effect hiding the window.
        Note that the window will not be closed if on_dismiss returns True (handled) unless force is True

        Args:
            window_id: Window identifier
            force: If on_dismiss returns True
        """
        window = WindowManager.window(window_id)

        if window:
            if not WindowManager.is_visible(window_id):
                Logger.warning("Window %s is already hidden", window_id)
                return

            if window._dismiss() and not force:
                return

            if window.parent_window():
                window.parent_window().remove_widget(window)
                window.parent_window().unbind(on_resize=window._align_center)
                window._parent = None

    @staticmethod
    def destroy_window(window_id):
        """Destroy window by given window_id. This will close and delete the object

        Args:
            window_id: Window identifier
        """
        window = WindowManager.window(window_id)

        if window:
            WindowManager.close_window(window_id)

            # remove from list
            WindowManager._windows = [value for value in WindowManager._windows if value[0] is not window_id]
            window.on_destroy()

            del window

    @staticmethod
    def window(window_id):
        """Get window object by given window_id.

        Args:
            window_id: Window identifier

        Returns:
            Window object or none
        """
        for t in WindowManager._windows:
            if t[0] == window_id:
                return t[1]

        return None

    @staticmethod
    def is_visible(window_id):
        """Check if window is visible. In essence, this method searches if the parent (if defined) has the window of the
        given window_id as one of its children.

        Args:
            window_id: Window identifier

        Returns:
            Boolean
        """
        window = WindowManager.window(window_id)

        if window:
            if window.parent_window():
                return window in window.parent_window().children

        return False

    @staticmethod
    def _closest_smallest_size(size):
        """Calculate the closest smallest (<=) size for a UI image

        Args:
            size: Starting size of image

        Returns:
            int: One of 256, 128, 64, 32, 24, 22, 16
        """
        sizes = [256, 128, 64, 32, 24, 22, 16]
        for s in sizes:
            if s <= size:
                return s

        return 16

    @staticmethod
    def theme_image_file(name='image', size=24, theme='white'):
        """Obtain (most appropriate) theme image file by iteratively lowering the size or returning a known (image not
        found) image.

        Args:
            name: Image name
            size: Starting image size
            theme: Theme style

        Returns:
            String: Relative image path
            None: if no image is found
        """
        # locate the image
        original_name = name
        original_size = size
        found = False
        file = ""
        while not found:
            size = WindowManager._closest_smallest_size(size)
            file = "ui/fontawesome/%s/png/%d/%s.png" % (theme, size, name)

            if os.path.exists(file):
                found = True
                break
            elif size == 16:
                if name == 'image':
                    file = None
                    Logger.warning('Unable to find image resource: %s', original_name)
                    break

                name = 'image'
                size = original_size
            else:
                size -= 1

        return file
