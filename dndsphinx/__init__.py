from .domain import DndDomain

def setup(app):
    app.add_domain(DndDomain)
