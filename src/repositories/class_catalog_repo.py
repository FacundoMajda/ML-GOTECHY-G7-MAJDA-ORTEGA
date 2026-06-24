# src/repositories/class_catalog_repo.py
from src.repositories.db import execute_query


class ObjectClassCatalogRepository:
    """Repository for object_class_catalog — 80 COCO classes seeded.

    Read-only: classes are populated by migration 003, no UI to mutate them
    (we keep the catalog stable so the COCO class_id ↔ name mapping is
    reliable across deployments).
    """

    def list_all(self, only_active: bool = True) -> list[dict]:
        where = "WHERE is_active = TRUE" if only_active else ""
        rows = execute_query(
            f"""
            SELECT id, name, category, is_active
            FROM object_class_catalog
            {where}
            ORDER BY category, name
            """,
            fetch="all",
        )
        return [
            {"id": row[0], "name": row[1], "category": row[2], "is_active": row[3]}
            for row in rows
        ]

    def list_by_category(self, category: str) -> list[dict]:
        rows = execute_query(
            """
            SELECT id, name, category, is_active
            FROM object_class_catalog
            WHERE category = %s AND is_active = TRUE
            ORDER BY name
            """,
            (category,),
            fetch="all",
        )
        return [
            {"id": row[0], "name": row[1], "category": row[2], "is_active": row[3]}
            for row in rows
        ]

    def get(self, class_id: int) -> dict | None:
        rows = execute_query(
            "SELECT id, name, category, is_active FROM object_class_catalog WHERE id = %s",
            (class_id,),
            fetch="all",
        )
        if not rows:
            return None
        row = rows[0]
        return {"id": row[0], "name": row[1], "category": row[2], "is_active": row[3]}

    def list_grouped_by_category(self) -> dict[str, list[dict]]:
        """Returns {category: [{id, name}, ...]} for UI rendering."""
        rows = execute_query(
            """
            SELECT id, name, category
            FROM object_class_catalog
            WHERE is_active = TRUE
            ORDER BY category, name
            """,
            fetch="all",
        )
        out: dict[str, list[dict]] = {}
        for row in rows:
            cat = row[2]
            out.setdefault(cat, []).append({"id": row[0], "name": row[1]})
        return out

    def get_id_for_name(self, name: str) -> int | None:
        """Resolve COCO name -> class_id (used by alert_rule & ROI evaluation)."""
        rows = execute_query(
            "SELECT id FROM object_class_catalog WHERE name = %s AND is_active = TRUE",
            (name,),
            fetch="all",
        )
        return rows[0][0] if rows else None
