// NYC map bounds and configuration
const NYC_BOUNDS = {
  min_lat: 40.477399, // Southernmost point of NYC
  max_lat: 40.917577, // Northernmost point of NYC
  min_lng: -74.25909, // Westernmost point of NYC
  max_lng: -73.700272, // Easternmost point of NYC
};

// Create a Leaflet bounds object from the NYC bounds
const NYC_LEAFLET_BOUNDS = [
  [NYC_BOUNDS.min_lat, NYC_BOUNDS.min_lng], // Southwest corner
  [NYC_BOUNDS.max_lat, NYC_BOUNDS.max_lng], // Northeast corner
];

// NYC center coordinates (approximate)
const NYC_CENTER = [40.7128, -74.006];

// Function to initialize a map with NYC bounds
function initializeNYCMap(mapElementId, options = {}) {
  // Create the map with NYC center
  const map = L.map(mapElementId, {
    center: options.center || NYC_CENTER,
    zoom: options.zoom || 11,
    maxBounds: NYC_LEAFLET_BOUNDS,
    minZoom: options.minZoom || 10,
    ...options,
  });

  // Add the tile layer
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
  }).addTo(map);

  // Set max bounds with padding to prevent scrolling too far outside NYC
  map.setMaxBounds(map.getBounds().pad(0.1));

  return map;
}
