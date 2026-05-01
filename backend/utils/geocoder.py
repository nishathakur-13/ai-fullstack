from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError


geolocator = Nominatim(
    user_agent="ai_complaint_system"
)


def get_coordinates(location_text):

    try:

        if not location_text or not str(location_text).strip():

            print("\n❌ EMPTY LOCATION\n")

            return {
                "latitude": None,
                "longitude": None
            }

        location_text = location_text.strip()

        print("\n========================")
        print("📍 GEOCODING START")
        print("========================")

        queries = [

            # exact
            location_text,

            # india
            f"{location_text}, India",

            # uttarakhand
            f"{location_text}, Uttarakhand, India",

            # haldwani region
            f"{location_text}, Haldwani, Uttarakhand, India"
        ]

        for query in queries:

            try:

                print(f"\n🔎 TRYING: {query}")

                location = geolocator.geocode(
                    query,
                    timeout=10
                )

                if location:

                    print("\n✅ LOCATION FOUND")
                    print(f"LAT: {location.latitude}")
                    print(f"LON: {location.longitude}")

                    return {

                        "latitude": float(location.latitude),

                        "longitude": float(location.longitude)
                    }

                else:

                    print("❌ No result")

            except (
                GeocoderTimedOut,
                GeocoderServiceError
            ) as e:

                print(f"\n⚠️ Geocoder error: {e}")

                continue

        print("\n🚨 ALL GEOCODING ATTEMPTS FAILED")

        # IMPORTANT:
        # DO NOT RETURN FAKE COORDS
        return {

            "latitude": None,

            "longitude": None
        }

    except Exception as e:

        print("\n❌ GEOCODER FATAL ERROR")
        print(str(e))

        return {

            "latitude": None,

            "longitude": None
        }
