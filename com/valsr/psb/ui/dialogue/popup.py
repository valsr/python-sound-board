"""
Created on Feb 1, 2017

@author: valsr <valsr@valsr.com>
"""
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.textinput import TextInput

from com.valsr.psb.ui.window.base import WindowCloseState


class PopupDialogue(Popup):
    """Popup dialogue base class"""

    def __init__(self, callback=None, size_hint=(0.5, 0.5), **kwargs):
        """Constructor

        Args:
            callback: dismiss callback
            size_hint: sizing hints tuple
        """
        super().__init__(size_hint=size_hint, **kwargs)
        self.selection = None
        self.dismissed = False
        self.bind(on_dismiss=self.on_dismiss)
        self.text = None
        self.cb = callback

    def _on_button(self, button):
        """Call to set selected button and dismiss the popup

        Args:
            button: Selected button identifier
        """
        self.selection = button
        self.dismiss()

    def _on_text_button(self, text, button):
        """Call to set selected button and text and then dismiss the popup

        Args:
            text: Text to set
            button: Selected button identifier
        """
        self.text = text
        self.selection = button
        self.dismiss()

    def on_dismiss(self, *args):
        """Handle popup dismissal"""
        self.dismissed = True
        if self.cb:
            self.cb(self)


def show_ok_popup(title='Title Message', message='Message', button='Ok', parent=None, **kwargs):
    """Show an simple one button popup

    Args:
        title: Popup title
        message: Message to display in the popup
        button: Label for the button
        parent: Parent window to attach the popup to
        kwargs: Named parameter to pass to the popup
    """
    p = PopupDialogue(title=title, attach_to=parent, **kwargs)
    top_box = BoxLayout(orientation='vertical')
    top_box.add_widget(Label(text=message))
    top_box.add_widget(Button(text=button, on_press=lambda x: p._on_button(WindowCloseState.OK), size_hint=(1, None),
                              height=35))
    p.content = top_box
    p.open()


def show_yes_no_popup(title='Title Message', message='Message', yes_button_label='Ok', no_button_label='No',
                      parent=None, **kwargs):
    """Show an yes/no button popup

    Args:
        title: Popup title
        message: Message to display in the popup
        yes_button_label: Label for the 'yes' button
        no_button_label: Label for the 'no' button
        parent: Parent window to attach the popup to
        kwargs: Named parameter to pass to the popup
    """
    p = PopupDialogue(title=title, attach_to=parent, **kwargs)
    top_box = BoxLayout(orientation='vertical')
    top_box.add_widget(Label(text=message))
    hbox = BoxLayout(orientation='horizontal')
    hbox.add_widget(Button(text=yes_button_label, on_press=lambda x: p._on_button(WindowCloseState.YES),
                           size_hint=(1, None), height=35))
    hbox.add_widget(Button(text=no_button_label, on_press=lambda x: p._on_button(WindowCloseState.NO),
                           size_hint=(1, None), height=35))
    top_box.add_widget(hbox)
    p.content = top_box
    p.open()


def show_text_input_popup(title='Title Message', message='Message', input_text='Enter value here',
                          yes_button_label='Proceed', no_button_label='Cancel', parent=None, **kwargs):
    """Show an yes/no button popup with a text input

    Args:
        title: Popup title
        message: Message to display in the popup
        input_text: Default input text
        yes_button_label: Label for the 'yes' button
        no_button_label: Label for the 'no' button
        parent: Parent window to attach the popup to
        kwargs: Named parameter to pass to the popup
    """
    p = PopupDialogue(title=title, attach_to=parent, **kwargs)
    top_box = BoxLayout(orientation='vertical')
    top_box.add_widget(Label(text=message))
    text_input = TextInput(text=input_text, multiline=False)
    top_box.add_widget(text_input)
    hbox = BoxLayout(orientation='horizontal')
    hbox.add_widget(Button(text=yes_button_label, on_press=lambda x: p._on_text_button(
        text_input.text, WindowCloseState.YES), size_hint=(1, None), height=35))
    hbox.add_widget(Button(text=no_button_label, on_press=lambda x: p._on_text_button(
        text_input.text, WindowCloseState.NO), size_hint=(1, None), height=35))
    top_box.add_widget(hbox)
    p.content = top_box
    p.open()
