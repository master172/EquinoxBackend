import PortalConnector
import faker

from faker import Faker
import random
from PortalConnector import (
    create_event, create_institution_registration, create_individual_registration,
    Event, RegistrationRequest, IndividualDelegate, InstitutionDelegate,
    participant, participant_institution, Team_institution
)
from fastapi import HTTPException

faker = Faker()

from faker import Faker
import random
from PortalConnector import (
    create_event, create_institution_registration, create_individual_registration,
    Event, RegistrationRequest, IndividualDelegate, InstitutionDelegate,
    participant, participant_institution, Team_institution
)
from fastapi import HTTPException

faker = Faker()

def create_sample_registrations(num_individual: int = 2, num_institution: int = 2, clubs: list[str] = None, events: list[str] = None) -> None:
    """
    Create sample registration data for individual and institution delegates.
    
    Args:
        num_individual (int): Number of individual registrations to create.
        num_institution (int): Number of institution registrations to create.
        clubs (list[str]): List of club names to use. If None, generate random club names.
        events (list[str]): List of event names to use. If None, generate random event names.
    """
    # Default clubs and events if not provided
    clubs = clubs or [faker.company() + " Club" for _ in range(2)]
    events = events or [faker.word().capitalize() + " Fest" for _ in range(3)]

    # Create sample events in Firestore if they don't exist
    for club in clubs:
        for event_name in events:
            event = Event(
                club_name=club,
                event_name=event_name,
                description=faker.sentence(),
                rules=[faker.sentence() for _ in range(3)],
                num_teams=random.randint(1, 5),
                num_participants=random.randint(1, 10),
                timings=faker.time(),
                venue=faker.address(),
                event_type=random.choice(["Competition", "Workshop", "Seminar"]),
                contact_no=faker.phone_number(),
                fees=random.randint(0, 1000)
            )
            try:
                create_event(event)
                print(f"Created event {event_name} for club {club}")
            except Exception as e:
                print(f"Failed to create event {event_name}: {str(e)}")

    # Create individual registrations
    for _ in range(num_individual):
        club = random.choice(clubs)
        event_name = random.choice(events)
        num_participants = random.randint(1, 3)
        participants = [
            participant(
                name=faker.name(),
                phone_no=faker.phone_number(),
                email_id=faker.email()
            ) for _ in range(num_participants)
        ]
        registration = IndividualDelegate(
            team_name=faker.word().capitalize() + " Team",
            participants=participants
        )
        request = RegistrationRequest(
            club_name=club,
            event_name=event_name,
            type="individual"
        )
        try:
            create_individual_registration(request, registration)
            print(f"Created individual registration for {event_name} in {club}")
        except Exception as e:
            print(f"Failed to create individual registration: {str(e)}")

    # Create institution registrations
    for _ in range(num_institution):
        club = random.choice(clubs)
        event_name = random.choice(events)
        num_teams = random.randint(1, 2)
        teams = []
        used_reg_nos = set()  # Track reg_no within this registration
        for _ in range(num_teams):
            num_participants = random.randint(1, 3)
            participants = []
            for _ in range(num_participants):
                reg_no = f"REG{10}"
                #while reg_no in used_reg_nos:  # Ensure unique reg_no within this registration
                #    reg_no = f"REG{faker.unique.random_int(min=1000, max=9999)}"
                used_reg_nos.add(reg_no)
                participants.append(
                    participant_institution(
                        name=faker.name(),
                        reg_no=reg_no,
                        phone_no=faker.phone_number(),
                        email_id=faker.email()
                    )
                )
            # Explicitly create Team_institution object
            team = Team_institution(participants=participants)
            teams.append(team)
        registration = InstitutionDelegate(
            institution_name=faker.company() + " University",
            delegate_head=faker.name(),
            delegate_phone_no=faker.phone_number(),
            delegate_email_id=faker.email(),
            teams=teams
        )
        request = RegistrationRequest(
            club_name=club,
            event_name=event_name,
            type="institution"
        )
        try:
            create_institution_registration(request, registration)
            print(f"Created institution registration for {event_name} in {club}")
        except HTTPException as e:
            print(f"Failed to create institution registration: {str(e.detail)}")
        except Exception as e:
            print(f"Failed to create institution registration: {str(e)}")

def main():
    try:
        create_sample_registrations(
            num_individual=3,  # Create 3 individual registrations
            num_institution=2,  # Create 2 institution registrations
            clubs=["Computer Science Association"],
            events=["max Showdown"]
        )
        print("Sample data creation completed successfully.")
    except Exception as e:
        print(f"Error creating sample data: {str(e)}")

if __name__ == "__main__":
    main()