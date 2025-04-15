// Modified view_listings.js for three-pane layout
console.log("Modified view_listings.js loaded");

// Global variables
let searchMap;
let searchMarker;
let mapInitialized = false;
let listingMarkers = []; // Keep track of all listing markers
let garageMarkers = [];
let currentMapView = null;
let garageLayerGroup;
let listingLayerGroup;
let currentMap;

// Map-related functions (outside DOMContentLoaded)
function initializeMap() {
  if (!mapInitialized) {
    console.log("Initializing search map...");
    // Use our NYC-bounded map initialization instead of the original code
    searchMap = initializeNYCMap("map-view");
    currentMapView = searchMap; // Store map reference

    // Initialize layer groups
    listingLayerGroup = L.layerGroup().addTo(searchMap);
    garageLayerGroup = L.layerGroup().addTo(searchMap);

    // Add click event to map
    searchMap.on("click", onMapClick);

    // Add the legend to the search map
    searchMap.addControl(createMapLegend());

    // Add garage markers to the search map
    addGaragesDirectly(searchMap);

    mapInitialized = true;
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
      className: "search-marker-icon",
      html: '<div style="background-color: #ff3b30; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white;"></div>',
      iconSize: [20, 20],
      iconAnchor: [10, 10],
    }),
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

  if (
    enableRadiusCheckbox &&
    enableRadiusCheckbox.checked &&
    radiusInput &&
    radiusInput.value
  ) {
    const radiusKm = parseFloat(radiusInput.value);
    if (!isNaN(radiusKm) && radiusKm > 0) {
      // Convert km to meters for the circle radius
      const radiusMeters = radiusKm * 1000;

      // Create a circle with styling
      radiusCircle = L.circle(center, {
        radius: radiusMeters,
        color: "#007bff",
        fillColor: "#007bff",
        fillOpacity: 0.1,
        weight: 2,
        dashArray: "5, 5",
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

document.addEventListener("DOMContentLoaded", function () {
  // Initialize both views to be active simultaneously
  const listView = document.getElementById("list-view");
  const mapView = document.getElementById("map-view");

  if (listView) listView.classList.add("active-view");
  if (mapView) mapView.classList.add("active-view");

  // Filter panel expand/collapse functionality
  const filterHeader = document.querySelector(".filter-header");
  const toggleFiltersBtn = document.getElementById("toggle-filters");

  // Add click event to both header and toggle button
  if (filterHeader) {
    filterHeader.addEventListener("click", function (e) {
      // Prevent click if they clicked the toggle button directly
      if (
        e.target !== toggleFiltersBtn &&
        !toggleFiltersBtn.contains(e.target)
      ) {
        toggleFilterPanel();
      }
    });
  }

  if (toggleFiltersBtn) {
    toggleFiltersBtn.addEventListener("click", function (e) {
      e.stopPropagation(); // Prevent double toggle from header click
      toggleFilterPanel();
    });
  }

  setupAdvancedFilters();
  setupRadiusToggle();
  initializeDateRangeToggle();
  initializeEvChargerToggle();
  initializeRecurringPatternToggle(); // Initialize map directly since it's always visible
  initializeMap();
  setMinDates();
  addListingsToMap();
  initializeLocationName();
  setupSearch();

  // Force map resize immediately AND after a short delay
  setTimeout(() => {
    if (searchMap) {
      searchMap.invalidateSize(true);
    }

    // Fix any initial spacing issues with the layout
    const mainContent = document.getElementById("main-content");
    if (mainContent) {
      mainContent.style.position = "absolute";
      mainContent.style.top = "56px"; // Match navbar height
      mainContent.style.left = "0";
      mainContent.style.right = "0";
      mainContent.style.bottom = "0";
    }
  }, 100);

  // Add window resize handler to ensure map fills space correctly
  window.addEventListener("resize", function () {
    if (searchMap) {
      searchMap.invalidateSize(true);
    }
  });
});

function setupSearch() {
  const searchInput = document.getElementById("location-search");
  const searchButton = document.getElementById("search-location");

  if (!searchButton || !searchInput) return;

  searchButton.addEventListener("click", performSearch);
  searchInput.addEventListener("keypress", function (e) {
    if (e.key === "Enter") {
      e.preventDefault();
      performSearch();
    }
  });
}

function performSearch() {
  const searchInput = document.getElementById("location-search");
  const mapContainer = document.getElementById("map-view");
  const query = searchInput.value;
  console.log("query", query);

  if (!query) return;

  // Use the utility function
  searchLocation(query, {
    restrictToNYC: true,
    onSuccess: (result) => {
      console.log("result", result);
      const latlng = L.latLng(result.lat, result.lng);

      // Show map when location is found
      mapContainer.style.display = "block";
      if (!mapInitialized) {
        initializeMap();
      }

      searchMap.setView(latlng, 15);
      placeMarker(latlng);

      // Add the location name to the marker popup
      if (searchMarker) {
        searchMarker.bindPopup(result.displayName).openPopup();
      }

      // Update the coordinate spans
      document.getElementById("coordinates-display").style.display = "block";
      document.getElementById("lat-display").textContent =
        result.lat.toFixed(6);
      document.getElementById("lng-display").textContent =
        result.lng.toFixed(6);

      // Update hidden inputs
      document.getElementById("search-lat").value = result.lat;
      document.getElementById("search-lng").value = result.lng;

      // Fix map rendering
      setTimeout(() => {
        searchMap.invalidateSize();
      }, 100);
    },
  });
}

function addListingsToMap() {
  // Add markers for all listings (as in original code)
  const listings = document.querySelectorAll(".card");
  console.log("listings", listings);
  const bounds = [];

  console.log(`Found ${listings.length} listings to add to map`);

  // Ensure listingLayerGroup exists
  if (!listingLayerGroup) {
    listingLayerGroup = L.layerGroup().addTo(searchMap);
  } else {
    // Clear existing markers
    listingLayerGroup.clearLayers();
  }

  listings.forEach((listing) => {
    try {
      console.log("listing", listing);
      const location = parseLocation(listing.dataset.location);
      console.log("location", location);
      const locationName = listing.dataset.locationName;
      const title = listing.dataset.title;
      const price = listing.dataset.price;
      const rating = parseFloat(listing.dataset.rating) || 0;

      console.log(
        `Adding listing: ${title} at ${location.lat}, ${location.lng}`
      );

      // Create the marker but add it to the layer group instead of the map
      const marker = L.marker([location.lat, location.lng], {
        zIndexOffset: 1000, // Higher z-index to appear above garage markers
      });

      listingLayerGroup.addLayer(marker);
      bounds.push([location.lat, location.lng]);

      // Create popup content
      const ratingHtml = rating
        ? `<br><strong>Rating:</strong> ${generateStarRating(
            rating
          )} (${rating.toFixed(1)})`
        : `<br><span class="text-muted">No reviews yet ${generateStarRating(
            0
          )}</span>`;

      const popupContent = `
            <strong>${title}</strong><br>
            ${locationName}<br>
            $${price}/hour
            ${ratingHtml}
        `;

      marker.bindPopup(popupContent);
    } catch (error) {
      console.error("Error adding listing marker:", error);
    }
  });
}

function initializeLocationName() {
  // Initialize location name if coordinates exist
  const searchLat = document.getElementById("search-lat").value;
  const searchLng = document.getElementById("search-lng").value;

  if (searchLat && searchLng && searchLat !== "None" && searchLng !== "None") {
    // Show map container and update toggle button state
    const mapContainer = document.getElementById("search-map-container");
    const toggleMapBtn = document.getElementById("toggle-map");
    mapContainer.style.display = "block";
    toggleMapBtn.classList.remove("btn-outline-secondary");
    toggleMapBtn.classList.add("btn-secondary");

    // Ensure we have valid numbers
    const lat = parseFloat(searchLat);
    const lng = parseFloat(searchLng);

    if (!isNaN(lat) && !isNaN(lng)) {
      const latlng = L.latLng(lat, lng);

      // Place marker and center map
      placeMarker(latlng);
      searchMap.setView(latlng, 15);

      // Get location name for the coordinates
      reverseGeocode(lat, lng, {
        onSuccess: (result) => {
          document.getElementById("location-search").value = result.displayName;

          // Make sure the marker has a popup with the location name
          if (searchMarker) {
            searchMarker.bindPopup(result.displayName).openPopup();

            // Also set a default popup in case reverse geocoding fails
            searchMarker.setPopupContent(result.displayName);
          }
        },
        onError: () => {
          // If reverse geocoding fails, still show a popup with coordinates
          if (searchMarker) {
            const fallbackContent = `Location at ${lat.toFixed(
              6
            )}, ${lng.toFixed(6)}`;
            searchMarker.bindPopup(fallbackContent).openPopup();
          }
        },
      });

      // Fix map rendering
      setTimeout(() => {
        searchMap.invalidateSize();

        // Make sure marker is visible after map is properly rendered
        if (searchMarker) {
          searchMarker.openPopup();
        }
      }, 100);
    }
  }
}
