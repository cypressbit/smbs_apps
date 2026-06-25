from django.test import TestCase

from smbs_apps.smbs_cities_light.models import Country, State, City


class CountryTest(TestCase):
    def test_create_country(self):
        country = Country(name='United States', code='us')
        country.clean()
        country.save()
        self.assertEqual(country.name, 'United States')
        self.assertEqual(country.code, 'US')

    def test_clean_uppercases_code(self):
        country = Country(name='Mexico', code='mx')
        country.clean()
        self.assertEqual(country.code, 'MX')

    def test_clean_generates_slug(self):
        country = Country(name='United Kingdom', code='gb')
        country.clean()
        self.assertEqual(country.slug, 'united-kingdom')

    def test_str_is_name(self):
        country = Country(name='Canada', code='CA')
        self.assertEqual(str(country), 'Canada')

    def test_code_unique(self):
        Country.objects.create(name='France', code='FR', slug='france')
        with self.assertRaises(Exception):
            Country.objects.create(name='France2', code='FR', slug='france2')


class StateTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='United States', code='US', slug='united-states'
        )

    def test_create_state(self):
        state = State(country=self.country, name='California')
        state.clean()
        state.save()
        self.assertEqual(state.name, 'California')
        self.assertEqual(state.slug, 'california')

    def test_clean_generates_slug(self):
        state = State(country=self.country, name='New York')
        state.clean()
        self.assertEqual(state.slug, 'new-york')

    def test_str_is_name(self):
        state = State(country=self.country, name='Texas')
        self.assertEqual(str(state), 'Texas')

    def test_states_relation(self):
        State.objects.create(country=self.country, name='Ohio', slug='ohio')
        State.objects.create(country=self.country, name='Idaho', slug='idaho')
        self.assertEqual(self.country.states().count(), 2)


class CityTest(TestCase):
    def setUp(self):
        self.country = Country.objects.create(
            name='United States', code='US', slug='united-states'
        )
        self.state = State.objects.create(
            country=self.country, name='California', slug='california'
        )

    def test_create_city(self):
        city = City(state=self.state, name='Los Angeles')
        city.clean()
        city.save()
        self.assertEqual(city.name, 'Los Angeles')
        self.assertEqual(city.slug, 'los-angeles')

    def test_str_includes_state(self):
        city = City.objects.create(
            state=self.state, name='San Francisco', slug='san-francisco'
        )
        self.assertIn('San Francisco', str(city))
        self.assertIn('California', str(city))

    def test_location_returns_coords(self):
        city = City.objects.create(
            state=self.state,
            name='San Diego',
            slug='san-diego',
            latitude='32.7157',
            longitude='-117.1611',
        )
        lat, lon = city.location()
        self.assertIsNotNone(lat)
        self.assertIsNotNone(lon)

    def test_get_or_create_slug_creates_if_missing(self):
        city = City.objects.create(
            state=self.state, name='Oakland', slug=''
        )
        slug = city.get_or_create_slug()
        self.assertEqual(slug, 'oakland')
