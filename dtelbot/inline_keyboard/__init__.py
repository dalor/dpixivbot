def markup(buttons):
    return {'inline_keyboard': buttons}

def button(text, **kwargs):
    kwargs['text'] = text
    return kwargs