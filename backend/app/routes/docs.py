from flask import Blueprint, render_template
from app import db
from sqlalchemy.inspection import inspect

docs_bp = Blueprint("docs", __name__, url_prefix="/docs")

@docs_bp.route("/schema")
def schema_overview():
    models = {}

    skip_tables = {
        "user_password_resets",
        "user_registration_tokens",
        "user_accounts",
        "object_dataset_types"
    }

    for mapper in db.Model.registry.mappers:
        cls = mapper.class_
        table = cls.__tablename__

        if table in skip_tables:
            continue

        fields = []
        for column in inspect(cls).columns:
            fields.append({
                "name": column.name,
                "type": str(column.type),
                "nullable": column.nullable,
                "default": column.default,
                "primary_key": column.primary_key
            })

        models[cls.__name__] = {
            "table": table,
            "fields": fields
        }

    return render_template("schema_overview.html", models=models)
