"""National-ID creators carry their registry country on public DOCiD reads."""

from flask_jwt_extended import create_access_token

from app import db
from app.models import (
    NationalIdResearcher,
    PublicationCreators,
    Publications,
    ResourceTypes,
    UserAccount,
)
from app.routes.publications import _national_id_creator_countries

DOCID = "20.500.14351/nationalidcountrytest"
NATIONAL_ID_NUMBER = "12345678"


def _seed_publication(creators):
    owner = UserAccount(
        user_name="nid-owner",
        full_name="Nid Owner",
        email="nid-owner@example.test",
        type="email",
        role="user",
        password="unused",
    )
    resource_type = ResourceTypes(resource_type="dataset")
    db.session.add_all([owner, resource_type])
    db.session.flush()
    publication = Publications(
        user_id=owner.user_id,
        document_docid=DOCID,
        document_title="National ID country test",
        document_description="fixture",
        resource_type_id=resource_type.id,
    )
    db.session.add(publication)
    db.session.flush()
    for creator in creators:
        creator.publication_id = publication.id
        db.session.add(creator)
    db.session.commit()
    return owner.user_id, publication.id


def _national_id_creator(name="John Doe", identifier=NATIONAL_ID_NUMBER):
    return PublicationCreators(
        family_name=name,
        given_name="",
        identifier=identifier,
        identifier_type="national_id",
        role_id="creator",
    )


def _orcid_creator():
    return PublicationCreators(
        family_name="Owango",
        given_name="Joy",
        identifier="https://orcid.org/0000-0002-3910-2691",
        identifier_type="orcid",
        role_id="1",
    )


def _register(name="John Doe", number=NATIONAL_ID_NUMBER, country="Kenya"):
    db.session.add(NationalIdResearcher(name=name, national_id_number=number, country=country))
    db.session.commit()


def _creators_by_type(payload):
    return {creator["identifier_type"]: creator for creator in payload["publication_creators"]}


def test_anonymous_docid_read_returns_country_and_masked_id(client):
    _register()
    _seed_publication([_orcid_creator(), _national_id_creator()])

    response = client.get(f"/api/v1/publications/docid?docid={DOCID}")

    assert response.status_code == 200
    creators = _creators_by_type(response.get_json())
    assert creators["national_id"]["country"] == "Kenya"
    assert creators["national_id"]["identifier"] != NATIONAL_ID_NUMBER
    assert creators["national_id"]["identifier_masked"] is True
    assert creators["orcid"]["country"] is None


def test_owner_docid_read_returns_country_and_raw_id(client):
    _register()
    owner_id, _ = _seed_publication([_national_id_creator()])
    owner_headers = {"Authorization": f"Bearer {create_access_token(identity=str(owner_id))}"}

    response = client.get(f"/api/v1/publications/docid?docid={DOCID}", headers=owner_headers)

    creator = response.get_json()["publication_creators"][0]
    assert creator["identifier"] == NATIONAL_ID_NUMBER
    assert creator["country"] == "Kenya"


def test_number_in_one_country_resolves_even_after_name_edit(app):
    _register(name="Original Name")
    _seed_publication([_national_id_creator(name="Edited Name")])

    creator = PublicationCreators.query.one()
    assert _national_id_creator_countries([creator]) == {creator.id: "Kenya"}


def test_number_in_two_countries_is_narrowed_by_name(app):
    _register(name="Someone Else", country="Uganda")
    _register(name="john   DOE", country="Kenya")
    _seed_publication([_national_id_creator(name=" John Doe ")])

    creator = PublicationCreators.query.one()
    assert _national_id_creator_countries([creator]) == {creator.id: "Kenya"}


def test_number_and_name_in_two_countries_is_left_blank(app):
    _register(country="Kenya")
    _register(country="Uganda")
    _seed_publication([_national_id_creator()])

    assert _national_id_creator_countries(PublicationCreators.query.all()) == {}


def test_unregistered_number_has_no_country(app):
    _seed_publication([_national_id_creator()])

    assert _national_id_creator_countries(PublicationCreators.query.all()) == {}


def test_jsonld_omits_national_id_from_same_as(client):
    _register()
    _, publication_id = _seed_publication([_orcid_creator(), _national_id_creator()])

    response = client.get(f"/api/v1/publications/{publication_id}/jsonld")

    assert response.status_code == 200
    assert NATIONAL_ID_NUMBER not in response.get_data(as_text=True)
    assert "https://orcid.org/0000-0002-3910-2691" in response.get_data(as_text=True)
