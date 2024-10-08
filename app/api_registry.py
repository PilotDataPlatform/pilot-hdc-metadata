# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from fastapi import FastAPI

from .routers.v1.attribute_templates import api_attribute_templates
from .routers.v1.collections import api_collections
from .routers.v1.favourites import api_favourites
from .routers.v1.health import api_health
from .routers.v1.items import api_items
from .routers.v1.items import api_lineage_provenance


def api_registry(app: FastAPI):
    app.include_router(api_health.router, prefix='/v1', tags=['Health'])
    app.include_router(api_items.router, prefix='/v1/item', tags=['Items'])
    app.include_router(api_items.router_bulk, prefix='/v1/items', tags=['Items'])
    app.include_router(api_attribute_templates.router, prefix='/v1/template', tags=['Attribute templates'])
    app.include_router(api_collections.router, prefix='/v1/collection', tags=['Collections'])
    app.include_router(api_favourites.router, prefix='/v1/favourite', tags=['Favourites'])
    app.include_router(api_favourites.router_bulk, prefix='/v1/favourites', tags=['Favourites'])
    app.include_router(api_lineage_provenance.router, prefix='/v1/lineage', tags=['Lineage and provenance'])
