let searchMap;
let searchMarker;
let mapInitialized = false;

document.addEventListener("DOMContentLoaded", function () {
  // Set up toggle map button
  const toggleMapBtn = document.getElementById("toggle-map");
  const mapContainer = document.getElementById("search-map-container");

  toggleMapBtn.addEventListener("click", function () {
    if (mapContainer.style.display === "none") {
      mapContainer.style.display = "block";
      if (!mapInitialized) {
        initializeMap();
      }
      // Trigger a resize event to fix map rendering
      setTimeout(() => {
        searchMap.invalidateSize();
      }, 100);
    } else {
      mapContainer.style.display = "none";
    }
  });

  // Set up search functionality
  setupSearch();

  // Load existing search location if any
  const searchLat = document.getElementById("search-lat").value;
  const searchLng = document.getElementById("search-lng").value;
  if (searchLat && searchLng) {
    // Show map if we have coordinates
    mapContainer.style.display = "block";
    initializeMap();
    const latlng = L.latLng(searchLat, searchLng);
    placeMarker(latlng);
    searchMap.setView(latlng, 15);

    // Show coordinates
    updateCoordinates(parseFloat(searchLat), parseFloat(searchLng));
  }
});

function initializeMap() {
  // Initialize search map
  searchMap = L.map("search-map").setView([40.69441, -73.98653], 13);
  L.tileLayer("https://tile.openstreetmap.bzh/ca/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors",
  }).addTo(searchMap);

  // Add click event to map
  searchMap.on("click", onMapClick);

  mapInitialized = true;
}

function onMapClick(e) {
  placeMarker(e.latlng);
  updateCoordinates(e.latlng.lat, e.latlng.lng);

  // Reverse geocode to get location name
  fetch(
    `https://nominatim.openstreetmap.org/reverse?format=json&lat=${e.latlng.lat}&lon=${e.latlng.lng}`
  )
    .then((response) => response.json())
    .then((data) => {
      console.log("hiiii", data);
      if (data.display_name) {
        document.getElementById("location-search").value = data.display_name;
      }
    })
    .catch((error) => console.error("Error:", error));
}

function placeMarker(latlng) {
  if (searchMarker) {
    searchMap.removeLayer(searchMarker);
  }
  // Make marker draggable and add drag event
  searchMarker = L.marker(latlng, { draggable: true }).addTo(searchMap);

  // Update coordinates when marker is dragged
  searchMarker.on("dragend", function (event) {
    const marker = event.target;
    const position = marker.getLatLng();
    updateCoordinates(position.lat, position.lng);

    // Reverse geocode to get location name
    fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${position.lat}&lon=${position.lng}`
    )
      .then((response) => response.json())
      .then((data) => {
        console.log("hiiii", data);
        if (data.display_name) {
          document.getElementById("location-search").value = data.display_name;
        }
      })
      .catch((error) => console.error("Error:", error));

    // Optional: Update map view to center on new position
    searchMap.setView(position, searchMap.getZoom());
  });
}

function updateCoordinates(lat, lng) {
  document.getElementById("search-lat").value = lat;
  document.getElementById("search-lng").value = lng;

  // Update coordinate display
  document.getElementById("coordinates-display").style.display = "block";
  document.getElementById("lat-display").textContent = lat.toFixed(6);
  document.getElementById("lng-display").textContent = lng.toFixed(6);
}

function setupSearch() {
  const searchInput = document.getElementById("location-search");
  const searchButton = document.getElementById("search-location");

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
  const mapContainer = document.getElementById("search-map-container");
  const query = searchInput.value;

  if (!query) return;

  fetch(
    `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
      query
    )}`
  )
    .then((response) => response.json())
    .then((data) => {
      if (data.length > 0) {
        const location = data[0];
        const lat = parseFloat(location.lat);
        const lon = parseFloat(location.lon);
        const latlng = L.latLng(lat, lon);

        // Show map when location is found
        mapContainer.style.display = "block";
        if (!mapInitialized) {
          initializeMap();
        }

        searchMap.setView(latlng, 15);
        placeMarker(latlng);

        // Update the coordinate spans
        document.getElementById("coordinates-display").style.display = "block";
        document.getElementById("lat-display").textContent = lat.toFixed(6);
        document.getElementById("lng-display").textContent = lon.toFixed(6);

        // Update hidden inputs
        document.getElementById("search-lat").value = lat;
        document.getElementById("search-lng").value = lon;

        // Fix map rendering
        setTimeout(() => {
          searchMap.invalidateSize();
        }, 100);
      }
    })
    .catch((error) => console.error("Error:", error));
}
