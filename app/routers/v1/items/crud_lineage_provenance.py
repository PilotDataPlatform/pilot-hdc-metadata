# Copyright (C) 2022-Present Indoc Systems
#
# Licensed under the GNU AFFERO GENERAL PUBLIC LICENSE,
# Version 3.0 (the "License") available at https://www.gnu.org/licenses/agpl-3.0.en.html.
# You may not use this file except in compliance with the License.

from operator import or_
from typing import List
from uuid import UUID

from fastapi_sqlalchemy import db
from sqlalchemy_utils import Ltree

from app.models.models_items import ContainerType
from app.models.models_items import ItemStatus
from app.models.models_items import ItemType
from app.models.models_lineage_provenance import TransformationType
from app.models.sql_lineage import LineageModel
from app.models.sql_provenance import ProvenanceModel
from app.routers.router_exceptions import EntityNotFoundException


def get_lineage_by_item_id(item_id: UUID) -> List[LineageModel]:
    lineage_query = db.session.query(LineageModel).filter(
        or_(LineageModel.consumes.any(item_id), LineageModel.produces.any(item_id))
    )
    lineage_query_results = lineage_query.all()
    if not lineage_query_results:
        raise EntityNotFoundException()
    item_lineage = []
    for transformation in lineage_query_results:
        item_lineage.append(transformation)
    return item_lineage


def get_provenance_snapshots_by_item_id(item_id: UUID) -> List[ProvenanceModel]:
    provenance_query = (
        db.session.query(ProvenanceModel)
        .filter(ProvenanceModel.item_id == item_id)
        .order_by(ProvenanceModel.snapshot_time)
    )
    provenance_query_results = provenance_query.all()
    if not provenance_query_results:
        raise EntityNotFoundException()
    provenance_snapshots = []
    for snapshot in provenance_query_results:
        provenance_snapshots.append(snapshot)
    return provenance_snapshots


def get_lineage_provenance_by_item_id(item_id: UUID) -> dict:
    lineage_provenance_query = (
        db.session.query(LineageModel, ProvenanceModel)
        .join(ProvenanceModel)
        .filter(or_(LineageModel.consumes.any(item_id), LineageModel.produces.any(item_id)))
    )
    lineage_provenance_query_results = lineage_provenance_query.all()
    if not lineage_provenance_query_results:
        raise EntityNotFoundException()

    response = {'lineage': {}, 'provenance': {}}
    for lineage_provenance_result in lineage_provenance_query_results:
        lineage = lineage_provenance_result[0]
        provenance = lineage_provenance_result[1]
        response['lineage'][str(lineage.id)] = {
            'tfrm_type': str(lineage.tfrm_type),
            'consumes': [str(item_id) for item_id in lineage.consumes] if lineage.consumes else None,
            'produces': [str(item_id) for item_id in lineage.produces] if lineage.produces else None,
        }
        provenance_response = provenance.to_dict()
        provenance_response.pop('item_id')
        response['provenance'][str(provenance.item_id)] = provenance_response
    return response


def create_lineage(consumes: List[UUID], produces: List[UUID], tfrm_type: TransformationType) -> UUID:
    lineage_model_data = {'consumes': consumes, 'produces': produces, 'tfrm_type': tfrm_type}
    lineage = LineageModel(**lineage_model_data)
    db.session.add(lineage)
    db.session.commit()
    db.session.refresh(lineage)
    return lineage.id


def create_provenance(
    lineage_id: UUID,
    item_id: UUID,
    parent: UUID,
    parent_path: Ltree,
    status: ItemStatus,
    type_: ItemType,
    zone: int,
    name: str,
    size: int,
    owner: str,
    container_code: str,
    container_type: ContainerType,
) -> None:
    if type_ == ItemType.FILE:
        provenance_model_data = {
            'lineage_id': lineage_id,
            'item_id': item_id,
            'parent': parent if parent else None,
            'parent_path': parent_path,
            'status': status,
            'type_': type_,
            'zone': zone,
            'name': name,
            'size': size,
            'owner': owner,
            'container_code': container_code,
            'container_type': container_type,
        }
        provenance = ProvenanceModel(**provenance_model_data)
        db.session.add(provenance)
        db.session.commit()
        db.session.refresh(provenance)
