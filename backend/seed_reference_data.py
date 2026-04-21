from app import create_app, db
from app.models import (
    AccountTypes,
    ResourceTypes,
    FunderTypes,
    PublicationTypes,
    PublicationIdentifierTypes,
    creatorsIdentifiers,
    CreatorsRoles,
)


def _upsert(model, field_name, values):
    for value in values:
        exists = model.query.filter(getattr(model, field_name) == value).first()
        if not exists:
            db.session.add(model(**{field_name: value}))


def _upsert_creator_roles():
    roles = [
        ("Author", "Author"),
        ("CoAuthor", "Co-Author"),
        ("Editor", "Editor"),
        ("PrincipalInvestigator", "Principal Investigator"),
    ]
    for role_id, role_name in roles:
        exists = CreatorsRoles.query.filter_by(role_id=role_id).first()
        if not exists:
            db.session.add(CreatorsRoles(role_id=role_id, role_name=role_name))


def seed_reference_data():
    _upsert(AccountTypes, "account_type_name", ["Individual", "Institutional"])
    _upsert(
        ResourceTypes,
        "resource_type",
        ["Article", "Dataset", "Software", "Image", "Video", "Other"],
    )
    _upsert(FunderTypes, "funder_type_name", ["Government", "Private", "Institutional"])
    _upsert(
        PublicationTypes,
        "publication_type_name",
        ["Main File", "Supplementary", "Preprint", "Versioned Update"],
    )
    _upsert(
        PublicationIdentifierTypes,
        "identifier_type_name",
        ["DOI", "CSTR", "Handle", "ARK"],
    )
    _upsert(creatorsIdentifiers, "identifier_name", ["ORCID", "ISNI", "VIAF"])
    _upsert_creator_roles()
    db.session.commit()
    print("Reference seed complete.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_reference_data()
