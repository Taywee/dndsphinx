from sphinx.domains import Domain
from sphinx.roles import XRefRole
from sphinx.util.docutils import SphinxDirective
from docutils.parsers.rst import directives
from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.utils import new_document
from collections import OrderedDict
import re
import string

id_trans_table = str.maketrans(' ' + string.ascii_uppercase, '-' + string.ascii_lowercase) 
keep_set = frozenset(string.ascii_lowercase + string.digits + '-')

def to_id(text):
    '''Convert input text into an alphanumeric-only string'''
    return ''.join(c for c in text.translate(id_trans_table) if c in keep_set)

def parse_rst(text: str) -> nodes.document:
    parser = Parser()
    components = (Parser,)
    settings = OptionParser(components=components).get_default_values()
    document = new_document('<rst-doc>', settings=settings)
    parser.parse(text, document)
    return document

def table_from_dict(d):
    '''Return a horizontal table from a dictionary'''

    table = nodes.table()
    tgroup = nodes.tgroup()
    head_row = nodes.row()
    body_row = nodes.row()
    for key, value in d.items():
        colspec = nodes.colspec(colwidth=max((len(key), len(value))))
        tgroup += colspec

        head_entry = nodes.entry()
        head_entry += nodes.paragraph(text=key)
        body_entry = nodes.entry()
        body_entry += nodes.paragraph(text=value)
        head_row += head_entry
        body_row += body_entry
    tbody = nodes.tbody()
    thead = nodes.thead()
    thead += head_row
    tbody += body_row
    tgroup += thead
    tgroup += tbody
    table += tgroup
    return table

dice_averages = {
    4: 2.5,
    6: 3.5,
    8: 4.5,
    10: 5.5,
    12: 6.5,
    20: 10.5,
    100: 50.5,
}

die_re = re.compile('^(\d+)?[dD](\d+)$')

class Die:
    def __init__(self, count, sides):
        self.count = count
        self.sides = sides

    def __str__(self):
        return f'{self.count}d{self.sides}'

    def avg(self):
        return dice_averages[self.sides] * self.count


def parse_die(value):
    '''parse each individual die into either a tuple of two numbers or a number'''

    match = die_re.match(value)
    if match is None:
        return int(value)
    else:
        count = match.group(1)
        if count is None:
            count = 1
        return Die(count=int(count), sides=int(match.group(2)))

def parse_dice(value):
    '''Change an input dice spec of any number of dice and bonuses into a spec
    containing these dice and bonuses plus their adjusted value.'''

    dice = [parse_die(die.strip()) for die in value.strip().split('+')]

    total = 0

    for die in dice:
        if isinstance(die, Die):
            total += die.avg()
        else:
            total += die
    dice_summary = ' + '.join(str(die) for die in dice)
    return f'{int(total)} ({dice_summary})'

def parse_stat(value):
    '''Parse a stat value into a value/modifier.'''
    value = int(value.strip())
    modifier = (value - 10) // 2
    return f'{value} ({modifier:+})'

class MonsterDirective(SphinxDirective):
    has_content = True

    option_spec = {
        'name': directives.unchanged_required,
        'meta': directives.unchanged,
        'ac': directives.unchanged_required,
        'hp': parse_dice,
        'speed': directives.unchanged_required,
        'str': parse_stat,
        'dex': parse_stat,
        'con': parse_stat,
        'int': parse_stat,
        'wis': parse_stat,
        'cha': parse_stat,
    }

    def run(self):
        attributes = OrderedDict()
        attributes['Armor Class'] = self.options['ac']
        attributes['Hit Points'] = self.options['hp']
        attributes['Speed'] = self.options['speed']
        stats = OrderedDict(
            STR=self.options['str'],
            DEX=self.options['dex'],
            CON=self.options['con'],
            INT=self.options['int'],
            WIS=self.options['wis'],
            CHA=self.options['cha'],
        )
        
        section = nodes.section(text=self.options['name'])
        section['ids'] = ['monster-' + to_id(self.options['name'])]
        title = nodes.title(text=self.options['name'])
        section += title
        if 'meta' in self.options:
            metapara = nodes.paragraph()
            meta = nodes.emphasis(text=self.options['meta'])
            metapara += meta
            section += metapara

        section += table_from_dict(attributes)
        section += table_from_dict(stats)

        self.state.nested_parse(self.content, self.content_offset, section)
        return [section]

class DndDomain(Domain):
    name = 'dnd'
    label = 'Dungeons and Dragons'

    roles = {
        'reref': XRefRole(),
    }

    directives = {
        'monster': MonsterDirective,
    }
