from app import create_app, db
from datetime import datetime

from app.models import  ResourceTypes,CreatorsRoles,creatorsIdentifiers,FunderTypes,PublicationIdentifierTypes,PublicationTypes,DocIdLookup,UserAccount
from sqlalchemy import inspect, text
from werkzeug.security import check_password_hash, generate_password_hash

def truncate_and_reset_table(model_class):
    """
    Truncates a table and optionally resets its sequence using SQLAlchemy.

    Args:
        model_class (sqlalchemy.orm.declarative_base.Model): The model class representing the table to truncate.

    Raises:
        sqlalchemy.exc.ArgumentError: If the model class is invalid.
    """

    if not model_class:
        raise ValueError("Invalid model class provided")

    session = db.session

    table_name = model_class.__tablename__  # Extract table name from model class

    # Explicitly declare truncate statement as text
    session.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))

    inspector = inspect(db.engine)
    sequences = inspector.get_sequence_names()
    sequence_name = f"{table_name}_id_seq"  # Assuming sequence name convention

    if sequence_name in sequences:
        # Explicitly declare sequence reset as text
        session.execute(text(f"ALTER SEQUENCE {sequence_name} RESTART WITH 1"))

    session.commit()
    
def seed():
    app = create_app()
    with app.app_context():
        try:
            # Seed data for new user
            hashed_password = generate_password_hash('demo@PASS123')

            # Deletes all existing records in user accounts table
            truncate_and_reset_table(UserAccount)

            new_user = UserAccount(
                social_id="",
                user_name="demo",
                full_name="Demo User",
                email='demo@africapidalliance.org',
                type="email",  # Default to "email"
                picture="https://placehold.co/100x100@2x.png",
                timestamp=datetime.utcnow(),
                affiliation="UON",
                role="user",  # Default to "user" if not provided
                first_time=1,
                orcid_id="1234-4566-12",
                ror_id="",
                country="KE",
                city="Nairobi",
                linkedin_profile_link="https://linkedin.com/p/tcc-africa",
                facebook_profile_link="https://facebook.com/p/tcc-africa",
                x_profile_link="https://x.com/p/tcc-africa",
                instagram_profile_link="https://instagram.com/p/tcc-africa",
                github_profile_link="https://github.com/p/tcc-africa",
                location="",
                date_joined=datetime.utcnow(),
                password=hashed_password
            )

            # Add and commit new user
            db.session.add(new_user)
            db.session.commit()

            print("User data seeded successfully!")

        except Exception as e:
            print(f"Seeding UserAccount failed: {e}")
            db.session.rollback()

         # ResourceTypes

        resource_types_data = [
            {'resource_type': 'Indigeneous Knowledge'},
            {'resource_type': 'Patent'},
            {'resource_type': 'Cultural Heritage'},
            {'resource_type': 'Project'},
            {'resource_type': 'Funder'},
            {'resource_type': 'DMP (Data Management Plan)'},
        ]

        try:

         truncate_and_reset_table(ResourceTypes)

         for data in resource_types_data:
          resource_type = ResourceTypes(**data)
          db.session.add(resource_type)
          db.session.commit()

          print("ResourceTypes data seeded successfully!")

        except Exception as e:
            print(f"Seeding ResourceTypes failed : {e}")

         # CreatorsRoles
                 
        creators_roles_data = [
		  {
		    "role_id": "1",
		    "role_name": "Innovator"
		  },
		  {
		    "role_id": "2",
		    "role_name": "Director"
		  },
		  {
		    "role_id": "3",
		    "role_name": "Researcher"
		  },
		  {
		    "role_id": "4",
		    "role_name": "Principal Investigator"
		  },
		  {
		    "role_id": "5",
		    "role_name": "Librarian"
		  },
		  {
		    "role_id": "6",
		    "role_name": "Vice Chancellor"
		  },
		  {
		    "role_id": "7",
		    "role_name": "Deputy Vice Chancellor"
		  },
		  {
		    "role_id": "8",
		    "role_name": "Author"
		  },
		  {
		    "role_id": "9",
		    "role_name": "Contributor"
		  }
		]

        try:

         #Deletes all existing records
         truncate_and_reset_table(CreatorsRoles)

         for data in creators_roles_data:
          resource_type = CreatorsRoles(**data)
          db.session.add(resource_type)
          db.session.commit()

          print("CreatorsRoles data seeded successfully!")

        except Exception as e:
            print(f"Seeding CreatorsRoles failed {e}")

       # creatorsIdentifiers

        creators_identifiers_data = [
            {'identifier_name': 'Open Alex'}
        ]

        try:

         #Deletes all existing records
         truncate_and_reset_table(creatorsIdentifiers)

         for data in creators_identifiers_data:
          identifier_name = creatorsIdentifiers(**data)
          db.session.add(identifier_name)
          db.session.commit()

          print("creatorsIdentifiers data seeded successfully!")

        except Exception as e:
          print(f'seeding creatorsIdentifiers failed: {e}')

       # FunderTypes

        funder_types_data = [
            {'funder_type_name': 'Grantor'},
            {'funder_type_name': 'Investor'},
            {'funder_type_name': 'Corporation'},
        ]

        try:

         #Deletes all existing records
         truncate_and_reset_table(FunderTypes)

         for data in funder_types_data:
          funder_type = FunderTypes(**data)
          db.session.add(funder_type)
          db.session.commit()

          print("FunderTypes data seeded successfully!")

        except Exception as e:
          print(f'seeding FunderTypes failed: {e}')

        # PublicationIdentifierTypes

        identifier_types_data = [
            {'identifier_type_name': 'DOI'},
            {'identifier_type_name': 'Data Cite'},
            {'identifier_type_name': 'Crossref'},
            {'identifier_type_name': 'CRST'}, 
            # {'identifier_type_name': 'ORCID'},//for creators
            # {'identifier_type_name': 'RAiD'}, //for projects
        ]

        try:

         #Deletes all existing records
         truncate_and_reset_table(PublicationIdentifierTypes)

         for data in identifier_types_data:
          identifier_type = PublicationIdentifierTypes(**data)
          db.session.add(identifier_type)
          db.session.commit()
          print("PublicationIdentifierTypes data seeded successfully!")

        except Exception as e:
          print(f'seeding PublicationIdentifierTypes failed: {e}')

        # PublicationTypes

        publication_types_data = [
            {'publication_type_name': 'Article'},
            {'publication_type_name': 'Book Chapter'},
            {'publication_type_name': 'Chapter'},
            {'publication_type_name': 'Proceeding'},
            {'publication_type_name': 'Monograph'},
            {'publication_type_name': 'Preprint'},
            {'publication_type_name': 'Edited Book'},
            {'publication_type_name': 'Seminar'},
            {'publication_type_name': 'Research Chapter'},
            {'publication_type_name': 'Review Article'},
            {'publication_type_name': 'Book Review'},
            {'publication_type_name': 'Conference Abstract'},
            {'publication_type_name': 'Letter To Editor'},
            {'publication_type_name': 'Editorial'},
            {'publication_type_name': 'Other Book Content'},
            {'publication_type_name': 'Correction Erratum'},
        ]

        try:

         #Deletes all existing records
         truncate_and_reset_table(PublicationTypes)

         for data in publication_types_data:
          publication_type = PublicationTypes(**data)
          db.session.add(publication_type)
          db.session.commit()
          print("PublicationTypes data seeded successfully!")

        except Exception as e:
          print(f'seeding PublicationTypes failed: {e}')

        print('Database seeded!')


def generate_pids():
    # Generate the series of numbers from 1 to 100
    series = range(1, 101)

    # Create a list to hold the records to be added to the session
    records = []

    # Iterate over the series and create instances of the model for each record
    for n in series:
        name = f"DOCID PID {n:04d}"
        description = "DOCID Sample DOI"
        pid = f"20.{n:04d}/{n:04d}"
        pid_reserved = False
        pid_reserved_date = datetime.utcnow()
        # pid_reserved_by = 1
        pid_assigned = False
        pid_assigned_date = datetime.utcnow()
        # pid_assigned_by = 1
        # docid_doi = None
        # Create an instance of the model with the field values
        record = DocIdLookup(
            name=name,
            description=description,
            pid=pid,
            pid_reserved=pid_reserved,
            pid_reserved_date=pid_reserved_date,
            # pid_reserved_by=pid_reserved_by,
            pid_assigned=pid_assigned,
            pid_assigned_date=pid_assigned_date,
            # pid_assigned_by=pid_assigned_by,
            # docid_doi=docid_doi
        )
        records.append(record)
    existing_records = [
        record.pid
        for record in db.session.query(DocIdLookup)
        .filter(DocIdLookup.pid.in_(record.pid for record in records))
        .all()
    ]
    records_to_insert = [
        record for record in records if record.pid not in existing_records
    ]

    try:
     # Add all records to the session
     db.session.add_all(records_to_insert)

     # Commit the changes to the database
     db.session.commit()
     db.session.close()
     print('PIDs genearted')

    except Exception as e:
     print(f"seeing DOCID failed: {e}")

if __name__ == '__main__':
    seed()
    generate_pids()
