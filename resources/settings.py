from __future__ import annotations

import datetime
import json
import pytz

from typing import List, Any, Union, overload

from .models import League, Section, Category, Setting, SettingType
from .namespace import Namespace

@overload
def _set_parent(item: Category, parent: Section) -> Category:
    ...

@overload
def _set_parent(item: Setting, parent: Category) -> Setting:
    ...

def _set_parent(item: Union[Setting, Category], parent: Union[Category, Section]) -> Union[Setting, Category]:
    if isinstance(item, Category) and isinstance(parent, Section):
        item._parent = parent
    elif isinstance(item, Setting) and isinstance(parent, Category):
        item._parent = parent

    return item

async def theme_string(league: League, setting: Setting) -> str:
    return '`Select to View`'

async def role_string(league: League, setting: Setting) -> str:
    return ', '.join([x.mention for x in await league.get_roles(setting.value)])

async def channel_string(league: League, setting: Setting) -> str:
    return getattr(await league.get_channel(setting.value), 'mention', '')

async def bool_string(league: League, setting: Setting) -> str:
    if league.get_value_from_setting(setting):
        return '✔ `on`'
    return '✖ `off`'

async def number_string(league: League, setting: Setting) -> str:
    return f"`{league.get_value_from_setting(setting)}`"

async def day_string(league: League, setting: Setting) -> str:
    value = league.get_value_from_setting(setting)
    return f'`{value} days`' if value < 1 or value > 1 else f'`{value} day`'

async def ping_string(league: League, setting: Setting) -> str:
    ping, _  = league.get_value_from_setting(setting).split(':')

    if ping == '0':
        return '@everyone'
    elif ping == '1':
        return '@here'
    else:
        return ', '.join([x.mention for x in await league.get_roles(setting.value)])
    
async def option_string(league: League, setting: Setting) -> str:
    assert setting.options

    value = league.get_value_from_setting(setting)

    if isinstance(value, str):
        for i in range(len(setting.options)):
            if value == setting.options[i].value:
                value = i
                break

        return f"{setting.options[value].emoji} `{setting.options[value].name}`"
    return f"`{setting.options[value].name}`"

async def timezone_string(league: League, setting: Setting) -> str:
    tz = pytz.timezone(league.get_value_from_setting(setting))
    utcoffset = datetime.datetime.now(tz).utcoffset()
    zone = tz.zone

    assert utcoffset
    assert zone

    offset = utcoffset.total_seconds() / 3600

    return f"`{zone.split('/')[-1].replace('_', ' ')} ({offset:+.2f})`".replace('.', ':')

SETTINGTYPES = Namespace(
    theme = SettingType(name='theme', prefix = '&', database='themes', string=theme_string, view=None),
    role = SettingType(name='role', prefix='@', database='roles', string=role_string, view=None),
    channel = SettingType(name='channel', prefix="#", database="channels", string=channel_string, view=None),
    alert = SettingType(name='alert', prefix="!", database="alerts", string=bool_string, view=None),
    status = SettingType(name='status', prefix="%", database="statuses", string=bool_string, view=None),
    number = SettingType(name='number', prefix="1", database="settings", string=number_string, view=None),
    day = SettingType(name='day', prefix="D", database="settings", string=day_string, view=None),
    ping = SettingType(name='ping', prefix="@", database="pings", string=ping_string, view=None),

    option = SettingType(name='option', prefix="&", database="settings", string=option_string, view=None),
    timezone = SettingType(name='timezone', prefix="&", database="settings", string=timezone_string, view=None),
)

with open('resources/files/settings.json', 'rb') as f:
    DATA: List[Namespace[str, Any]] = [Namespace(x) for x in json.load(f)]

for section in DATA:
    for category in section['categories']:
        for setting in category['settings']:
            setting['type'] = SETTINGTYPES[setting['type']]

SECTIONS: List[Section] = [Section(**x) for x in DATA]
CATEGORIES: List[Category] = [_set_parent(x, y) for y in SECTIONS for x in y.categories]
SETTINGS: Namespace[str, Setting] = Namespace({x.value: _set_parent(x, y) for y in CATEGORIES for x in y.settings})

TIMEZONES = [
    "Pacific/Midway",      # UTC-11:00
    "Pacific/Honolulu",    # UTC-10:00
    "US/Aleutian",         # UTC-09:00
    "America/Anchorage",   # UTC-08:00
    "America/Los_Angeles", # UTC-07:00
    "America/Denver",      # UTC-06:00
    "America/Chicago",     # UTC-05:00
    "America/New_York",    # UTC-04:00
    "America/Sao_Paulo",   # UTC-03:00
    "Brazil/DeNoronha",    # UTC-02:00
    "Atlantic/Cape_Verde", # UTC-01:00
    "Greenwich",           # UTC±00:00
    "Europe/London",       # UTC+01:00
    "Europe/Berlin",       # UTC+02:00
    "Asia/Riyadh",         # UTC+03:00
    "Asia/Dubai",          # UTC+04:00
    "Asia/Karachi",        # UTC+05:00
    "Asia/Dhaka",          # UTC+06:00
    "Asia/Bangkok",        # UTC+07:00
    "Asia/Singapore",      # UTC+08:00
    "Asia/Tokyo",          # UTC+09:00
    "Australia/Sydney",    # UTC+10:00
    "Pacific/Guadalcanal", # UTC+11:00
    "Pacific/Auckland",    # UTC+12:00
    "Pacific/Tongatapu",   # UTC+13:00
]