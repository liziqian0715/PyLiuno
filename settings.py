# PyLiuno runtime settings (simple i18n switch)
LANGUAGE = 'en'  # 'en' or 'zh'

def set_language(lang: str):
    global LANGUAGE
    if lang not in ('en', 'zh'):
        raise ValueError('Unsupported language')
    LANGUAGE = lang
