import re


def extract_first(selector_list, default=None):
    for x in selector_list:
        return x.extract()
    else:
        return default


def clean_text(self, text):
    text = text.replace("\n", " ").replace("\t", " ").replace("\r", " ")
    text = re.sub("&nbsp;", " ", text).strip()

    return re.sub(r'\s+', ' ', text)


def clean_list(self, list_a):
    list_all = []
    for l in list_a:
        l = clean_text(self, l)
        list_all.append(l)
    return list_all
