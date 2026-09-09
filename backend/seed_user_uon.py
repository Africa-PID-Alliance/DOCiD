#!/usr/bin/env python3
"""
Idempotent local seed for the University of Nairobi institutional account.

The UoN Excel importer (scripts/import_uon_excel.py) refuses to run unless
journals@uonbi.ac.ke resolves to a real user_account, so that harvested
publications are never silently attributed to the legacy user_id=1. That
account exists in production; this seed recreates it locally so the import can
be tested end to end.

Production already has this account, so this is normally only needed when
standing up a fresh local or demo database. The password is read from the
UON_SEED_PASSWORD environment variable and is never stored in this file.

Usage:
    cd backend && UON_SEED_PASSWORD='...' python seed_user_uon.py
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from werkzeug.security import generate_password_hash  # noqa: E402

from app import create_app, db  # noqa: E402
from app.models import AccountCategories, AccountTypes, UserAccount  # noqa: E402

UON_EMAIL = 'journals@uonbi.ac.ke'

# Never hardcode the account password: this file is tracked in git. Supply it at
# run time, e.g. UON_SEED_PASSWORD='...' python backend/seed_user_uon.py
UON_SEED_PASSWORD_ENV_VAR = 'UON_SEED_PASSWORD'

UON_ACCOUNT = dict(
    user_name='uonbi',
    full_name='University of Nairobi',
    email=UON_EMAIL,
    type='email',
    affiliation='University of Nairobi',
    role='user',
    country='Kenya',
    city='Nairobi',
    ror_id='https://ror.org/02y9nww90',
    first_time=0,
)


def main():
    seed_password = os.environ.get(UON_SEED_PASSWORD_ENV_VAR)
    if not seed_password:
        raise SystemExit(
            f'{UON_SEED_PASSWORD_ENV_VAR} is not set. Re-run with the account '
            f"password supplied at run time, e.g. {UON_SEED_PASSWORD_ENV_VAR}='...' "
            'python seed_user_uon.py'
        )

    app = create_app()
    with app.app_context():
        institutional_type = AccountTypes.query.filter_by(
            account_type_name='Institutional'
        ).first()
        standard_category = AccountCategories.query.filter_by(
            category_name='Standard'
        ).first()

        existing_user = UserAccount.query.filter(
            db.func.lower(UserAccount.email) == UON_EMAIL.lower()
        ).first()

        if existing_user:
            for field_name, value in UON_ACCOUNT.items():
                setattr(existing_user, field_name, value)
            user = existing_user
            action = 'Updated'
        else:
            user = UserAccount(**UON_ACCOUNT)
            db.session.add(user)
            action = 'Created'

        user.password = generate_password_hash(seed_password)
        if institutional_type:
            user.account_type_id = institutional_type.id
        if standard_category:
            user.account_category_id = standard_category.id

        db.session.commit()
        print(f'{action} user_id={user.user_id} email={user.email} '
              f'account_type_id={user.account_type_id} '
              f'account_category_id={user.account_category_id}')


if __name__ == '__main__':
    main()
