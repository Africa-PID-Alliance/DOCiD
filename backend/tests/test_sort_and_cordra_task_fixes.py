"""Regressions: sort=title crashed two list endpoints; the Cordra task ran a missing script."""

import importlib
import os
import subprocess
import sys
import types
from unittest.mock import patch

from flask_jwt_extended import create_access_token

from app import db
from app.models import Publications, ResourceTypes, UserAccount


def _make_user(name):
    user = UserAccount(
        user_name=name,
        full_name=name.title(),
        email=f"{name}@example.test",
        type="email",
        role="user",
        password="unused",
    )
    db.session.add(user)
    db.session.commit()
    return user.user_id, {"Authorization": f"Bearer {create_access_token(identity=str(user.user_id))}"}


def _make_publication(owner_id, docid, title):
    resource_type = ResourceTypes.query.first()
    if resource_type is None:
        resource_type = ResourceTypes(resource_type="dataset")
        db.session.add(resource_type)
        db.session.flush()
    publication = Publications(
        user_id=owner_id,
        document_docid=docid,
        document_title=title,
        document_description="fixture",
        resource_type_id=resource_type.id,
    )
    db.session.add(publication)
    db.session.commit()
    return publication.id


def test_get_publications_sorts_by_title(client):
    owner_id, _ = _make_user("sort-title-list")
    for suffix, title in (("01", "Banana"), ("02", "apple"), ("03", "Cherry")):
        _make_publication(owner_id, f"20.500.14351/sorttitle{suffix}", title)

    for order in ("asc", "desc"):
        response = client.get(f"/api/v1/publications/get-publications?sort=title&order={order}")
        assert response.status_code == 200
        titles = [item["title"] for item in response.get_json()["data"]]
        assert titles == sorted(titles, reverse=(order == "desc"))


def test_user_profile_publications_sorts_by_title(client):
    owner_id, headers = _make_user("sort-title-profile")
    for suffix, title in (("01", "Beta"), ("02", "Alpha")):
        _make_publication(owner_id, f"20.500.14351/sortprof{suffix}", title)

    response = client.get(f"/api/v1/user-profile/{owner_id}/publications?sort=title&order=asc", headers=headers)
    assert response.status_code == 200
    assert [item["document_title"] for item in response.get_json()["publications"]] == ["Alpha", "Beta"]


def test_unknown_sort_field_is_still_a_400(client):
    assert client.get("/api/v1/publications/get-publications?sort=bogus").status_code == 400


def _import_tasks_with_stub_celery():
    """app.tasks needs Celery, which isn't installed; a stub lets the task body run."""
    stub = types.ModuleType("celery")

    class Celery:
        def __init__(self, *args, **kwargs):
            pass

        def task(self, function):
            return function

    stub.Celery = Celery
    with patch.dict(sys.modules, {"celery": stub}):
        sys.modules.pop("app.tasks", None)
        tasks = importlib.import_module("app.tasks")
    sys.modules.pop("app.tasks", None)
    return tasks


def test_cordra_task_runs_the_single_publication_push_script(app):
    tasks = _import_tasks_with_stub_celery()
    owner_id, _ = _make_user("cordra-task")
    publication_id = _make_publication(owner_id, "20.500.14351/cordratask01", "Task test")

    completed = subprocess.CompletedProcess(args=[], returncode=0, stdout="", stderr="")
    with patch("app.create_app", return_value=app), \
            patch.object(tasks.subprocess, "run", return_value=completed) as run:
        assert tasks.push_to_cordra_async(publication_id) is True

    command = run.call_args.args[0]
    working_directory = run.call_args.kwargs["cwd"]
    assert command[1:] == ["push_to_cordra.py", "--publication-id", str(publication_id)]
    assert os.path.isfile(os.path.join(working_directory, command[1]))
    db.session.expire_all()
    assert db.session.get(Publications, publication_id).cordra_status == "MINTED"
