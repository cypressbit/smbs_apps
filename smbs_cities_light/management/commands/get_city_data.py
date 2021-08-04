import urllib
import csv
import zipfile
import json

from django.core.management.base import BaseCommand, CommandError

from smbs_cities_light.models import Country, State, City


UNUSED_CITY_CODES = ['PPLQ', 'PPLW', 'PPLX', 'PPLH']


class Command(BaseCommand):

    COUNTRY_CODES_URL = 'https://datahub.io/core/country-list/r/data.json'
    GEONAMES_DUMP_URL = 'http://download.geonames.org/export/dump/{}.zip'

    help = 'Gets city data  and populates the DB'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('countries', nargs='+', type=str)
        # Named (optional) arguments
        parser.add_argument(
            '--population-size',
            dest='population',
            help='Minimum population size',
            type=int,
        )

    def handle(self, *args, **options):
        for country_code in options['countries']:
            country = self.get_or_create_country(country_code)
            dump_url = self.GEONAMES_DUMP_URL.format(country.code)
            file_name, headers = urllib.request.urlretrieve(dump_url)

            zip_ref = zipfile.ZipFile(file_name, 'r')
            zip_ref.extractall('/tmp/dump_{}'.format(country.code))
            zip_ref.close()

            text_file = '/tmp/dump_{}/{}.txt'.format(country.code, country.code)

            state_dict = self.get_states(country, text_file)

            self.create_cities(state_dict, text_file, options.get('population'))

    def get_or_create_country(self, short_code):
        country = Country.objects.filter(code=short_code.upper()).first()

        if not country:
            file_name, headers = urllib.request.urlretrieve(self.COUNTRY_CODES_URL)
            with open(file_name) as f:
                country_list = json.loads(f.read())

            try:
                country_dict = [i for i in country_list if i.get('Code') == short_code.upper()][0]
                country = Country(name=country_dict.get('Name'), code=country_dict.get('Code'))
                country.save()
            except IndexError:
                raise CommandError('Failed to create country instance "{}"'.format(short_code))

        return country

    def get_states(self, country, text_file):
        state_dict = {}

        with open(text_file) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            for row in reader:
                feature_class = row[6]
                feature_code = row[7]

                if feature_class == 'A' and feature_code == 'ADM1':
                    name = row[1]
                    admin1 = row[10]
                    state = State.objects.filter(country=country, name=name).first()
                    if not state:
                        state = State(country=country, name=name)
                        state.save()
                    state_dict[admin1] = state

        return state_dict

    def create_cities(self, state_dict, text_file, population_size=None):
        with open(text_file) as csvfile:
            reader = csv.reader(csvfile, delimiter='\t')
            for row in reader:
                feature_class = row[6]
                feature_code = row[7]

                if feature_class == 'P' and feature_code not in UNUSED_CITY_CODES:
                    name = row[1]
                    latitude = row[4]
                    longitude = row[5]
                    admin1 = row[10]
                    population = row[14]
                    timezone = row[18]

                    if population_size and int(population) < population_size:
                        continue

                    state = state_dict.get(admin1)
                    if not state:
                        continue

                    city = City.objects.filter(state=state, name=name).first()
                    if not city:
                        city = City(state=state, name=name)

                    city.latitude = latitude
                    city.longitude = longitude
                    city.population = population
                    city.timezone = timezone
                    city.save()



