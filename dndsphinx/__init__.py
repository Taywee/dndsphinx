from .domain import DndDomain
from .domain import MonsterIndex
from sphinx.locale import _

def register_index_as_label(app, document):
    labels = app.env.domaindata['std']['labels']
    labels['monsterindex'] = 'dnd-monsterindex', '', _('Monster Index')
    anonlabels = app.env.domaindata['std']['anonlabels']
    anonlabels['monsterindex'] = 'dnd-monsterindex', ''

def setup(app):
    app.add_domain(DndDomain)
    app.connect('doctree-read', register_index_as_label)
