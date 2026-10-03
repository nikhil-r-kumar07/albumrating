from django import template

register = template.Library()

@register.filter
def star_states(rating):
    # For drawing 5 stars: each is 'on', 'half' or 'off'. 3.5 -> on, on, on, half, off.
    if rating is None:
        return []
    states = []
    for star in range(1, 6):
        if rating >= star:
            states.append('on')
        elif rating >= star - 0.5:
            states.append('half')
        else:
            states.append('off')
    return states

@register.filter
def rating_text(rating):
    # 3.0 -> "3", 3.5 -> "3.5"
    return ('%.1f' % rating).rstrip('0').rstrip('.')

@register.simple_tag
def half_star_values():
    # The picker's choices after 0: ('0.5', '0-5', 'left'), ('1', '1', 'right'), ... ('5', '5', 'right')
    values = []
    for half in range(1, 11):
        value = ('%.1f' % (half / 2)).rstrip('0').rstrip('.')
        values.append((value, value.replace('.', '-'), 'left' if half % 2 else 'right'))
    return values

@register.filter
def track_length(ms):
    # 261000 -> "4:21"
    if not ms:
        return ''
    seconds = round(ms / 1000)
    return '%d:%02d' % (seconds // 60, seconds % 60)

@register.filter
def total_length(ms):
    # Album running time: 2843000 -> "47 min", 4500000 -> "1 hr 15 min"
    if not ms:
        return ''
    minutes = round(ms / 60000)
    if minutes < 60:
        return '%d min' % minutes
    return '%d hr %d min' % (minutes // 60, minutes % 60)
