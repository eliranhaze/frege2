from django import template
register = template.Library()

@register.filter
def index(List, i):
    if not List or i >= len(List):
        return [] 
    return List[int(i)]

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
