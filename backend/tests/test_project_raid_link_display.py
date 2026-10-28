"""Public DOCiD reads return the stored RAiD link for each project."""

import pytest

from app import db
from app.models import PublicationProjects, Publications, ResourceTypes, UserAccount

DOCID = "20.500.14351/raidlinktest"
RAID_LINK = "https://raid.org/10.26259/0e59e9a5"


def _seed_publication_with_raid_project():
    owner = UserAccount(
        user_name="raid-owner",
        full_name="Raid Owner",
        email="raid-owner@example.test",
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
        document_title="RAiD link test",
        document_description="fixture",
        resource_type_id=resource_type.id,
    )
    db.session.add(publication)
    db.session.flush()
    db.session.add(PublicationProjects(
        publication_id=publication.id,
        title="Prepayment meters project",
        description="fixture",
        raid_id="10.26259/0e59e9a5",
        identifier=RAID_LINK,
        identifier_type="raid",
    ))
    db.session.commit()
    return publication.id


@pytest.mark.parametrize("url_for", [
    lambda publication_id: f"/api/v1/publications/docid?docid={DOCID}",
    lambda publication_id: f"/api/v1/publications/get-publication/{publication_id}",
    lambda publication_id: f"/api/v1/publications/{DOCID}",
    lambda publication_id: f"/doi/{DOCID}",
], ids=["docid", "get-publication", "docid-path", "doi"])
def test_public_reads_return_project_raid_link(client, url_for):
    publication_id = _seed_publication_with_raid_project()

    response = client.get(url_for(publication_id))

    assert response.status_code == 200
    project = response.get_json()["publication_projects"][0]
    assert project["identifier"] == RAID_LINK
    assert project["identifier_type"] == "raid"
