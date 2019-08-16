from collections import OrderedDict, defaultdict
from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.parsers.rst import directives
from docutils.utils import new_document
from sphinx.domains import Domain
from sphinx.domains import Index
from sphinx.locale import _
from sphinx.roles import XRefRole
from sphinx.util.docutils import SphinxDirective
from sphinx.util.nodes import make_refnode
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
    required_arguments = 1
    final_argument_whitespace = True

    option_spec = {
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
        attributes[_('Armor Class')] = self.options['ac']
        attributes[_('Hit Points')] = self.options['hp']
        attributes[_('Speed')] = self.options['speed']
        stats = OrderedDict(
            STR=self.options['str'],
            DEX=self.options['dex'],
            CON=self.options['con'],
            INT=self.options['int'],
            WIS=self.options['wis'],
            CHA=self.options['cha'],
        )
        name = self.arguments[0]
        id = 'monster-' + to_id(name)
        
        section = nodes.section(text=name)
        section['ids'] = [id]
        title = nodes.title(text=name)
        section += title

        if 'meta' in self.options:
            metatext = self.options['meta']
            metapara = nodes.paragraph()
            meta = nodes.emphasis(text=metatext)
            metapara += meta
            section += metapara
        else:
            metatext = None

        section += table_from_dict(attributes)
        section += table_from_dict(stats)

        self.state.nested_parse(self.content, self.content_offset, section)

        # Handle indexes
        self.env.get_domain('dnd').add_monster(name, id, metatext)

        return [section]

class MonsterIndex(Index):
    name = 'monsterindex'
    localname = _('Monster Index')
    shortname = _('Monster')

    def generate(self, docnames=None):
        content = defaultdict(list)

        # sort the list of monsters in alphabetical order
        monsters = list(self.domain.data['monster'].values())
        monsters = sorted(monsters, key=lambda monster: monster['name'])

        # generate the expected output, shown below, from the above using the
        # first letter of the monster as a key to group thing
        #
        # name, subtype, docname, anchor, extra, qualifier, description
        #for name, dispname, typ, docname, anchor, _ in monsters:
        for monster in monsters:
            content[monster['name'][0].upper()].append(
                (monster['name'], 0, monster['doc'], monster['id'], monster['doc'], '', monster['meta']))

        # convert the dict to the sorted list of tuples expected
        content = sorted(content.items())

        return content, True

class DndDomain(Domain):
    name = 'dnd'
    label = _('Dungeons and Dragons')

    roles = {
        'monster': XRefRole(),
    }

    directives = {
        'monster': MonsterDirective,
    }

    indices = {
        MonsterIndex,
    }

    initial_data = {
        'monster': {},
    }

    def add_monster(self, name, id, meta=None):
        self.data['monster'][name] = {'name': name, 'id': id, 'doc': self.env.docname, 'meta': meta}

    def resolve_xref(self, env, fromdocname, builder, type, target, node, contnode):
        if target in self.data[type]:
            monster = self.data[type][target]
            return make_refnode(builder, fromdocname, monster['doc'], monster['id'], contnode, monster['id'])
        else:
            print(f'Could not match {type} {target}')
