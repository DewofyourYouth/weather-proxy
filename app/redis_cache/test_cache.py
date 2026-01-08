import pytest
import fakeredis
from app.redis_cache.cache import *

@pytest.fixture
def fake_redis():
    client = fakeredis.FakeRedis(decode_responses=True)
    client.flushall()
    return client

def test_normalize_city_name(fake_redis):
    assert normalize_city_name("New York") == "new_york"
    assert normalize_city_name("Tel Aviv") == "tel_aviv"
    assert normalize_city_name("Rio de Janeiro") == "rio_de_janeiro"

def test_save_city_to_cache(fake_redis):
    cache = CityCache(fake_redis)
    rio = "Rio de Janeiro"
    cache.save_city(rio, City(name="Rio de Janeiro", country_code="BR", latitude=-22.90642, longitude=-43.18223,))
    assert cache.get_city(rio) == City(name='Rio de Janeiro', country_code='BR', latitude=-22.90642, longitude=-43.18223)
