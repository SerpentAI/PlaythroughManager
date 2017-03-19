

class ProductMixin:

    def as_minimal_json(self):
        json_representation = dict()

        json_representation["uuid"] = str(self.uuid)
        json_representation["type"] = self.type
        json_representation["name"] = self.name

        return json_representation

    def as_json(self):
        json_representation = dict()

        json_representation["uuid"] = str(self.uuid)
        json_representation["type"] = self.type
        json_representation["name"] = self.name
        json_representation["external_id"] = self.external_id
        json_representation["description"] = self.description
        json_representation["release_date"] = self.release_date.isoformat() if self.release_date else None
        json_representation["is_free_to_play"] = self.is_free_to_play
        json_representation["is_visible"] = self.is_visible
        json_representation["review_label"] = self.review_label
        json_representation["review_total"] = self.review_total
        json_representation["review_positive"] = self.review_positive
        json_representation["review_negative"] = self.review_negative
        json_representation["platform_uuid"] = str(self.platform.uuid) if self.platform else None
        json_representation["platform"] = self.platform.name if self.platform else None

        json_representation["developers"] = [{"uuid": str(d.uuid), "name": d.name} for d in self.developers]
        json_representation["publishers"] = [{"uuid": str(p.uuid), "name": p.name} for p in self.publishers]
        json_representation["product_tags"] = [{"uuid": str(pt.uuid), "label": pt.label} for pt in self.product_tags]
        json_representation["product_genres"] = [{"uuid": str(pg.uuid), "name": pg.name, "external_id": pg.external_id} for pg in self.product_genres]
        json_representation["product_categories"] = [{"uuid": str(pc.uuid), "name": pc.name, "external_id": pc.external_id} for pc in self.product_categories]
        json_representation["product_achievements"] = [{"uuid": str(pa.uuid), "name": pa.name, "description": pa.description, "external_id": pa.external_id} for pa in self.product_achievements]
        json_representation["product_images"] = [{"uuid": str(pi.uuid), "type": pi.type, "url": pi.url} for pi in self.product_images]
        json_representation["product_providers"] = [{"uuid": str(pp.uuid), "name": pp.name, "url": pp.url} for pp in self.product_providers]

        json_representation["children"] = [c.as_minimal_json() for c in self.children]
        json_representation["parent"] = self.parent.as_minimal_json() if self.parent else None

        json_representation["created_at"] = self.created_at.isoformat() if self.created_at else None
        json_representation["updated_at"] = self.updated_at.isoformat() if self.updated_at else None

        return json_representation