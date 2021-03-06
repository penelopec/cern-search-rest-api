# -*- coding: utf-8 -*-
#
# This file is part of CERN Search.
# Copyright (C) 2019 CERN.
#
# Citadel Search is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Unit tests fixtures."""
from io import BytesIO

import pytest
from cern_search_rest_api.modules.cernsearch.api import CernSearchRecord
from flask_login import AnonymousUserMixin, UserMixin
from invenio_app.factory import create_app as create_ui_api
from invenio_files_rest.models import Bucket, ObjectVersion
from invenio_files_rest.signals import file_uploaded


@pytest.fixture(scope='module')
def create_app():
    """Application factory fixture."""
    return create_ui_api


@pytest.fixture()
def anonymous_user():
    """Anonymous user (not logged in)."""

    class User(AnonymousUserMixin):

        def __init__(self):
            super().__init__()

    return User()


@pytest.fixture()
def authenticated_user():
    """Authenticate user (logged in)."""

    class User(UserMixin):

        def __init__(self):
            super().__init__()

    return User()


@pytest.fixture(scope='function')
def private_access_record():
    """Private access record."""
    return {
        '_access': {
            'read': ['read-perm'],
            'update': ['update-perm'],
            'delete': ['delete-perm'],
            'owner': ['owner-perm']
        }
    }


@pytest.fixture(scope='function')
def public_access_record():
    """Public access record."""
    return {
        '_access': {
            'update': ['update-perm'],
            'delete': ['delete-perm'],
            'owner': ['owner-perm']
        }
    }


@pytest.fixture()
def bucket(db, location):
    """File system location."""
    b1 = Bucket.create()
    b1.id = '00000000-0000-0000-0000-000000000000'
    db.session.commit()

    yield b1

    b1.remove()
    db.session.commit()


@pytest.fixture()
def object_version(db, bucket):
    """Multipart object."""
    content = b'some content'
    obj = ObjectVersion.create(
        bucket,
        'test.pdf',
        stream=BytesIO(content),
        size=len(content)
    )
    db.session.commit()

    yield obj

    ObjectVersion.delete(bucket, obj.key)
    db.session.commit()


@pytest.fixture()
def record_with_file(db, location, es_clear):
    """File system location."""
    record = CernSearchRecord.create({'title': 'test'}, with_bucket=True)
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    db.session.commit()

    yield record

    record.delete(force=True)
    db.session.commit()


@pytest.fixture()
def record_with_file_processed(db, location, es_clear):
    """File system location."""
    record = CernSearchRecord.create({
        '_data': {
            'title': 'test',
        },
        "$schema": "https://0.0.0.0/schemas/test/file_v0.0.4.json"
    }, with_bucket=True)
    record.files['hello.txt'] = BytesIO(b'Hello world!')
    db.session.commit()

    record = CernSearchRecord.get_record(record.id)

    # mimic file uploaded flow
    file_uploaded.send(record.files['hello.txt'].obj)

    yield record

    record.delete(force=True)
    db.session.commit()
