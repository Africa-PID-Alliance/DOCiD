from app import create_app, db
from app.models import (
    AccountTypes,
    AccountCategories,
    AccountCategoryResourceTypes,
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


def _upsert_account_categories():
    """
    Seed client categories and their is_restricted flag (idempotent — the generic
    _upsert only inserts and never updates, so is_restricted is handled explicitly),
    then map Publisher -> Manuscripts. Resilient when 'Manuscripts' is absent (some
    envs run the DataCite resource-type set), so it never fails the seed.
    """
    categories = [
        ("Publisher", True),
        ("Standard", False),
    ]
    for category_name, is_restricted in categories:
        existing = AccountCategories.query.filter_by(category_name=category_name).first()
        if existing:
            if existing.is_restricted != is_restricted:
                existing.is_restricted = is_restricted
        else:
            db.session.add(
                AccountCategories(category_name=category_name, is_restricted=is_restricted)
            )
    db.session.flush()  # ensure category ids exist before mapping

    publisher = AccountCategories.query.filter_by(category_name="Publisher").first()
    manuscripts = ResourceTypes.query.filter_by(resource_type="Manuscripts").first()
    if publisher and manuscripts:
        mapping_exists = AccountCategoryResourceTypes.query.filter_by(
            account_category_id=publisher.id, resource_type_id=manuscripts.id
        ).first()
        if not mapping_exists:
            db.session.add(
                AccountCategoryResourceTypes(
                    account_category_id=publisher.id,
                    resource_type_id=manuscripts.id,
                )
            )
    else:
        print(
            "Skipping Publisher->Manuscripts mapping: "
            "'Manuscripts' resource type not present in this environment."
        )


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
    _upsert_account_categories()
    db.session.commit()
    print("Reference seed complete.")


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        seed_reference_data()
