def handleButton(action, widget=None):
    """
    Universal handler: executes the action passed.
    The menu decides which action to pass per button.
    """
    if action:
        action(widget)