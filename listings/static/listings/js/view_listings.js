// Modified view_listings.js for three-pane layout
console.log("Modified view_listings.js loaded");

// Helper function to generate star HTML - extract it so it can be used anywhere
function generateStarRating(rating) {
  let starsHtml = "";

  if (!rating) {
    // Show 5 empty stars if no rating
    for (let i = 0; i < 5; i++) {
      starsHtml += '<i class="far fa-star text-warning"></i>';
    }
  } else {
    // Full stars
    for (let i = 0; i < Math.floor(rating); i++) {
      starsHtml += '<i class="fas fa-star text-warning"></i>';
    }
    // Half star
    if (rating % 1 >= 0.5) {
      starsHtml += '<i class="fas fa-star-half-alt text-warning"></i>';
    }
    // Empty stars
    for (let i = Math.ceil(rating); i < 5; i++) {
      starsHtml += '<i class="far fa-star text-warning"></i>';
    }
  }

  return starsHtml;
}

// Global variables
let searchMap;
let searchMarker;
let mapInitialized = false;
let listingMarkers = []; // Keep track of all listing markers

// Map-related functions (outside DOMContentLoaded)
function initializeMap() {
  if (!mapInitialized) {
    // Always initialize the map in the map-view panel
    searchMap = initializeNYCMap("map-view");

    // Add click event to map
    searchMap.on("click", onMapClick);
    mapInitialized = true;
    
    // Add all listing markers immediately
    addListingMarkersToMap();
  }
}

function onMapClick(e) {
  // Only update if we're in search mode (not viewing listings)
  placeMarker(e.latlng);
  updateCoordinates(e.latlng.lat, e.latlng.lng);

  // Reverse geocode to get location name
  reverseGeocode(e.latlng.lat, e.latlng.lng, {
    onSuccess: (result) => {
      document.getElementById("location-search").value = result.displayName;
    },
  });
}

function placeMarker(latlng) {
  if (searchMarker) {
    searchMap.removeLayer(searchMarker);
  }
  
  // Create a special search marker that stands out from listing markers
  searchMarker = L.marker(latlng, { 
    draggable: true,
    icon: L.divIcon({
      className: 'search-marker-icon',
      html: '<div style="background-color: #ff3b30; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10]
    })
  }).addTo(searchMap);

  // Update coordinates when marker is dragged
  searchMarker.on("dragend", function (event) {
    const marker = event.target;
    const position = marker.getLatLng();
    updateCoordinates(position.lat, position.lng);

    // Reverse geocode to get location name
    reverseGeocode(position.lat, position.lng, {
      onSuccess: (result) => {
        document.getElementById("location-search").value = result.displayName;
        marker.bindPopup(result.displayName);
      },
    });

    // Draw search radius if enabled
    drawSearchRadius(position);
  });
  
  // Draw search radius if enabled
  drawSearchRadius(latlng);
}

// Add search radius visualization
let radiusCircle = null;
function drawSearchRadius(center) {
  // Remove existing radius circle if it exists
  if (radiusCircle) {
    searchMap.removeLayer(radiusCircle);
    radiusCircle = null;
  }
  
  // Check if radius filtering is enabled
  const enableRadiusCheckbox = document.getElementById("enable-radius");
  const radiusInput = document.getElementById("radius-input");
  
  if (enableRadiusCheckbox && enableRadiusCheckbox.checked && radiusInput && radiusInput.value) {
    const radiusKm = parseFloat(radiusInput.value);
    if (!isNaN(radiusKm) && radiusKm > 0) {
      // Convert km to meters for the circle radius
      const radiusMeters = radiusKm * 1000;
      
      // Create a circle with styling
      radiusCircle = L.circle(center, {
        radius: radiusMeters,
        color: '#007bff',
        fillColor: '#007bff',
        fillOpacity: 0.1,
        weight: 2,
        dashArray: '5, 5'
      }).addTo(searchMap);
      
      // Fit map to show the entire circle
      searchMap.fitBounds(radiusCircle.getBounds());
    }
  }
}

function updateCoordinates(lat, lng) {
  document.getElementById("search-lat").value = lat;
  document.getElementById("search-lng").value = lng;

  // Update coordinate display
  const coordDisplay = document.getElementById("coordinates-display");
  if (coordDisplay) {
    coordDisplay.style.display = "block";
    document.getElementById("lat-display").textContent = lat.toFixed(6);
    document.getElementById("lng-display").textContent = lng.toFixed(6);
  }
}