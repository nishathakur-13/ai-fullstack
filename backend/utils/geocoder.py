from geopy.geocoders import Nominatim


geolocator = Nominatim(
    user_agent="ai_complaint_system"
)


def get_coordinates(location_text):

    try:

        # -----------------------------------
        # First Attempt
        # -----------------------------------

        enhanced_query = (
            f"{location_text}, "
            f"Uttarakhand, India"
        )

        print("\nGEOCODING QUERY:")
        print(enhanced_query)

        location = geolocator.geocode(
            enhanced_query
        )

        # -----------------------------------
        # Success
        # -----------------------------------

        if location:

            return {

                "latitude":
                location.latitude,

                "longitude":
                location.longitude
            }

        # -----------------------------------
        # Fallback to Haldwani Center
        # -----------------------------------

        print(
            "\nFALLBACK TO HALDWANI"
        )

        fallback = geolocator.geocode(
            "Haldwani, Uttarakhand, India"
        )

        if fallback:

            return {

                "latitude":
                fallback.latitude,

                "longitude":
                fallback.longitude
            }

        return {

            "latitude": None,

            "longitude": None
        }

    except Exception as e:

        print("\nGEOCODER ERROR:")
        print(str(e))

        return {

            "latitude": None,

            "longitude": None
        }