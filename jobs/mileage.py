import json, sys, os, datetime, pytz, calendar

import googlemaps

# add system directory to pull in app & models

sys.path.append(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))

from config import GMAP_API_KEY as gmap_key
from app import db, models

def build_mileage_obj(appts):
  temp_obj = {}

  for appt in appts:
    temp_obj[appt.therapist.id] = temp_obj.get(appt.therapist.id, {})
    temp_obj[appt.therapist.id][appt.start_datetime.strftime('%Y-%m-%d')] = temp_obj[appt.therapist.id].get(appt.start_datetime.strftime('%Y-%m-%d'),{'ids': [], 'locations': []})
    temp_obj[appt.therapist.id][appt.start_datetime.strftime('%Y-%m-%d')]['locations'].append(appt.location)
    temp_obj[appt.therapist.id][appt.start_datetime.strftime('%Y-%m-%d')]['ids'].append(appt.id)

  return temp_obj


def add_mileage(start_date, end_date):

  """Takes therapist object and two date times to find appts between them and add the traveled mileage.  Starts and ends at company address."""

  gmaps = googlemaps.Client(key=gmap_key)

  start_date = start_date.replace(hour=00, minute=00, second=00)
  end_date = end_date.replace(hour=23, minute=59, second=59)

  appts = models.ClientAppt.query.filter(models.ClientAppt.start_datetime >= start_date, models.ClientAppt.start_datetime <= end_date, models.ClientAppt.cancelled == 0).order_by(models.ClientAppt.start_datetime).all()

  mileage_temp_obj = build_mileage_obj(appts)

  insert_mileage_obj = {}

  for therapist_id in mileage_temp_obj:
    therapist = models.Therapist.query.get(therapist_id)
    company_address = therapist.user.company.address + ' ' + therapist.user.company.city + ', ' + therapist.user.company.state + ' ' + therapist.user.company.zipcode
    therapist_appts = mileage_temp_obj[therapist_id]

    for day in therapist_appts:
      day_appts = therapist_appts[day]
      locations = [company_address] + day_appts['locations']
      ids = day_appts['ids'] + [0]
      if None in locations:
        continue
      appts_count = len(locations)


      matrix = distance_matrix = gmaps.distance_matrix(locations, locations)

      for i, row in enumerate(matrix['rows']):
        appt_id = ids[i]
        if appt_id == 0:
          appt_id = ids[i-1]

        insert_mileage_obj[appt_id] = insert_mileage_obj.get(appt_id, 0) + round(row['elements'][(i+1)%appts_count]['distance']['value'] * .000621371)

  insert_list = [{'id': i, 'mileage': insert_mileage_obj[i]} for i in insert_mileage_obj]

  print(insert_list)
  db.session.bulk_update_mappings(models.ClientAppt, insert_list)
  db.session.commit()
  print('finished')




end = datetime.datetime.now()
start = end - datetime.timedelta(days=7)

add_mileage(start,end)
