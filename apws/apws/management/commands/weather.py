import time
from typing import Optional, Tuple

from django.core.management.base import BaseCommand


class ReadException(Exception):
    pass

class Dht11Sensor:
    """DHT11 temperature and humidity sensor reader for Raspberry Pi."""

    DEFAULT_PIN = 4

    def __init__(self, pin: int = DEFAULT_PIN):
        """
        Initialize DHT11 sensor.

        Args:
            pin: GPIO pin number (default: 4)
        """
        self.pin = pin
        self._adafruit_dht = None
        self._sensor = None

        try:
            import adafruit_dht

            self._adafruit_dht = adafruit_dht
            self._sensor = adafruit_dht.DHT11(pin)
        except ImportError:
            pass

    def is_available(self) -> bool:
        """Check if GPIO/sensor library is available."""
        return self._sensor is not None

    def read(self, retries: int = 3, delay: float = 2.0) -> Optional[Tuple[float, float]]:
        """
        Read temperature and humidity from DHT11 sensor.

        Args:
            retries: Number of retry attempts on failure (default: 3)
            delay: Delay between retries in seconds (default: 2.0)

        Returns:
            Tuple of (temperature, humidity)

        Raises:
            ReadException: If sensor read fails
        """
        if not self.is_available():
            return None

        try:
            for attempt in range(retries):
                try:
                    temperature = self._sensor.temperature
                    humidity = self._sensor.humidity

                    if temperature is not None and humidity is not None:
                        return temperature, humidity
                except RuntimeError:
                    pass

                if attempt < retries - 1:
                    time.sleep(delay)

            raise ReadException("Failed to retrieve temperature and humidity")
        finally:
            self._sensor.exit()


class Command(BaseCommand):
    help = "Read DHT11 sensor temperature and humidity (weather command)"

    def add_arguments(self, parser):
        parser.add_argument(
            "--pin",
            type=int,
            default=4,
            help="GPIO pin number (default: 4)",
        )

    def handle(self, *args, **options):
        pin = options["pin"]

        sensor = Dht11Sensor(pin=pin)

        if not sensor.is_available():
            self.stdout.write(
                self.style.ERROR(
                    "GPIO/DHT11 library not available. "
                    "This command requires a Raspberry Pi with GPIO access. "
                )
            )
            return

        try:
            temperature, humidity = sensor.read()

            self.stdout.write(
                self.style.SUCCESS(
                    f"Temperature: {temperature:.1f}°C, Humidity: {humidity:.1f}%"
                )
            )
        except ReadException:
            self.stdout.write(
                self.style.ERROR("Failed to read from DHT11 sensor")
            )
