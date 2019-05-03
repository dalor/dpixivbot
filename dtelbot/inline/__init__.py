def result(type, id, **kwargs):
    kwargs['type'] = type
    kwargs['id'] = id
    return kwargs

def article(id, title, input_message_content, **kwargs):
    return result('article', id, title=title, input_message_content=input_message_content, **kwargs)

def photo(id, photo_url, thumb_url, **kwargs):
    return result('photo', id, photo_url=photo_url, thumb_url=thumb_url, **kwargs)

def gif(id, gif_url, **kwargs):
    return result('gif', id, gif_url=gif_url, **kwargs)

def mpeg4gif(id, mpeg4_url, **kwargs):
    return result('mpeg4_gif', id, mpeg4_url=mpeg4_url, **kwargs)

def video(id, video_url, mime_type, thumb_url, title, **kwargs):
    return result('video', id, video_url=video_url, mime_type=mime_type, thumb_url=thumb_url, title=title, **kwargs)

def audio(id, audio_url, title, **kwargs):
    return result('audio', id, audio_url=audio_url, title=title, **kwargs)

def voice(id, voice_url, title, **kwargs):
    return result('voice', id, voice_url=voice_url, title=title, **kwargs)

def document(id, document_url, title, **kwargs):
    return result('document', id, document_url=document_url, title=title, **kwargs)