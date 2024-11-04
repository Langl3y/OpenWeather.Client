class BoundingBox:
    def __init__(self, lat_top: float, lat_bottom: float, lon_left: float, lon_right: float):
        """
        Forming the bounding box using limiting coordinates
        :param lat_top: Maximum latitude (north)
        :param lat_bottom: Minimum latitude (south)
        :param lon_left: Minimum longitude (west)
        :param lon_right: Maximum longitude (east)
        """
        self.lat_min = lat_bottom
        self.lat_max = lat_top
        self.lon_min = lon_left
        self.lon_max = lon_right

    def get_bounding_box(self):
        return {
            'lat_min': self.lat_min,
            'lon_min': self.lon_min,
            'lat_max': self.lat_max,
            'lon_max': self.lon_max
        }
