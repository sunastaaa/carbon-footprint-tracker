import requests

CITIES_COORDS = {
    'moscow': {'name': 'Москва', 'lat': 55.75, 'lon': 37.62},
    'spb': {'name': 'Санкт-Петербург', 'lat': 59.93, 'lon': 30.32},
    'ekb': {'name': 'Екатеринбург', 'lat': 56.84, 'lon': 60.60},
    'novosibirsk': {'name': 'Новосибирск', 'lat': 55.03, 'lon': 82.92},
    'kazan': {'name': 'Казань', 'lat': 55.79, 'lon': 49.11},
    'krasnodar': {'name': 'Краснодар', 'lat': 45.04, 'lon': 38.98},
    'samara': {'name': 'Самара', 'lat': 53.20, 'lon': 50.15},
    'rostov': {'name': 'Ростов-на-Дону', 'lat': 47.23, 'lon': 39.72},
    'ufa': {'name': 'Уфа', 'lat': 54.74, 'lon': 55.97},
    'chelyabinsk': {'name': 'Челябинск', 'lat': 55.16, 'lon': 61.40},
}


def get_weather_correction(city_key):
    if city_key not in CITIES_COORDS:
        return {
            'correction': 1.0,
            'temperature': None,
            'weather_description': 'Город не найден',
            'success': False
        }

    city = CITIES_COORDS[city_key]

    try:
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": city['lat'],
            "longitude": city['lon'],
            "current_weather": True
        }

        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        current = data.get('current_weather', {})
        temperature = current.get('temperature', 0)
        weather_code = current.get('weathercode', 0)

        correction = 1.0
        reasons = []

        # Холодно (< 0°C) - расход топлива выше на 15%
        if temperature < 0:
            correction += 0.15
            reasons.append(f"мороз {temperature}°C")

        # Осадки (коды 51-67 дождь, 71-77 снег)
        if 51 <= weather_code <= 77:
            correction += 0.10
            reasons.append("осадки")

        # Сильный ветер (> 20 м/с)
        windspeed = current.get('windspeed', 0)
        if windspeed > 20:
            correction += 0.05
            reasons.append(f"ветер {windspeed} м/с")

        # Описание погоды по коду WMO
        weather_desc = get_weather_description(weather_code)

        return {
            'correction': round(correction, 2),
            'temperature': temperature,
            'weather_description': weather_desc,
            'reasons': ', '.join(reasons) if reasons else 'норма',
            'success': True
        }

    except requests.RequestException as e:
        # Если API недоступен - возвращаем базовый коэффициент
        return {
            'correction': 1.0,
            'temperature': None,
            'weather_description': f'Ошибка API: {str(e)}',
            'success': False
        }


def get_weather_description(code):
    codes = {
        0: 'Ясно',
        1: 'Преим. ясно',
        2: 'Переменная облачность',
        3: 'Пасмурно',
        45: 'Туман',
        48: 'Изморозь',
        51: 'Лёгкая морось',
        53: 'Морось',
        55: 'Сильная морось',
        61: 'Небольшой дождь',
        63: 'Дождь',
        65: 'Сильный дождь',
        71: 'Небольшой снег',
        73: 'Снег',
        75: 'Сильный снег',
        77: 'Снежные зёрна',
        80: 'Ливень',
        81: 'Сильный ливень',
        82: 'Очень сильный ливень',
        95: 'Гроза',
        96: 'Гроза с градом',
    }
    return codes.get(code, 'Неизвестно')


def get_cities_choices():
    return [(key, data['name']) for key, data in CITIES_COORDS.items()]