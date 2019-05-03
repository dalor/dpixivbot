def result(type, media, **kwargs):
    kwargs['type'] = type
    kwargs['media'] = media
    return kwargs

def animation(media, **kwargs):
    return result('animation', media, **kwargs)

def photo(media, **kwargs):
    return result('photo', media, **kwargs)

def video(media, **kwargs):
    return result('video', media, **kwargs)
