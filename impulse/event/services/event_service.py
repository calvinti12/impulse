from datetime import timedelta

from django.utils import timezone

from impulse.event.lib.seatgeek_gateway import search_upcoming_events
from impulse.event.models import Event, EventPrice, VENDOR_TYPE_SEATGEEK, Venue
from impulse.utils import generate_external_id

__all__ = [
    'create_event',
    'create_event_price_for_event',
    'get_events_starting_in_next_twenty_four_hours',
    'find_or_create_upcoming_events_matching_query'
]


def create_event(vendor_id, vendor_type, title, datetime_start, datetime_start_local, price, url, venue):
    event = Event.objects.create(
        datetime_start=datetime_start,
        datetime_start_local=datetime_start_local,
        title=title,
        url=url,
        vendor_id=vendor_id,
        vendor_type=vendor_type,
        venue=venue
    )

    _update_event_with_external_id(event)

    if price:
        create_event_price_for_event(event, price)

    return event


def _update_event_with_external_id(event):
    event.external_id = generate_external_id(event.id)
    event.save()


def create_event_price_for_event(event, price):
    EventPrice.objects.create(
        event=event,
        price=price
    )


def get_events_starting_in_next_twenty_four_hours():
    now = timezone.now()
    twenty_four_hours_from_now = now + timedelta(days=1)

    return Event.objects.filter(
        datetime_start__range=(now, twenty_four_hours_from_now)
    )


def find_or_create_upcoming_events_matching_query(query):
    seatgeek_events = search_upcoming_events(query)

    return [_find_or_create_event(seatgeek_event) for seatgeek_event in seatgeek_events]


def _find_or_create_event(seatgeek_event):
    venue = find_or_create_venue(seatgeek_event.venue)

    try:
        event = Event.objects.get(
            vendor_id=seatgeek_event.id,
            vendor_type=VENDOR_TYPE_SEATGEEK
        )
    except Event.DoesNotExist:
        event = create_event(
            vendor_id=seatgeek_event.id,
            vendor_type=VENDOR_TYPE_SEATGEEK,
            title=seatgeek_event.title,
            datetime_start=seatgeek_event.datetime_utc,
            datetime_start_local=seatgeek_event.datetime_local,
            price=seatgeek_event.lowest_price,
            url=seatgeek_event.url,
            venue=venue
        )

    return event


def find_or_create_venue(seatgeek_venue):
    try:
        venue = Venue.objects.get(
            vendor_id=seatgeek_venue.id,
            vendor_type=VENDOR_TYPE_SEATGEEK
        )
    except Venue.DoesNotExist:
        venue = Venue.objects.create(
            name=seatgeek_venue.name,
            city=seatgeek_venue.city,
            state=seatgeek_venue.state,
            country=seatgeek_venue.country,
            vendor_id=seatgeek_venue.id,
            vendor_type=VENDOR_TYPE_SEATGEEK
        )

    return venue
