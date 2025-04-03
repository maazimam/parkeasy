let searchMap;
let searchMarker;
let mapInitialized = false;

console.log("location_search.js loaded");

document.addEventListener("DOMContentLoaded", function () {
  // Set up toggle map button
  const toggleMapBtn = document.getElementById("toggle-map");
  const mapContainer = document.getElementById("search-map-container");

  toggleMapBtn.addEventListener("click", function () {
    const isMapHidden = mapContainer.style.display === "none";

    // Update button text/style based on state
    if (isMapHidden) {
      mapContainer.style.display = "block";
      toggleMapBtn.classList.remove("btn-outline-secondary");
      toggleMapBtn.classList.add("btn-secondary");

      // Initialize map if needed
      if (!mapInitialized) {
        initializeMap();
      }
      // Fix map rendering
      setTimeout(() => {
        searchMap.invalidateSize();
      }, 100);
    } else {
      mapContainer.style.display = "none";
      toggleMapBtn.classList.remove("btn-secondary");
      toggleMapBtn.classList.add("btn-outline-secondary");
    }
  });

  // Set up search functionality
  setupSearch();

  // Check URL parameters first, then fallback to hidden inputs
  const urlParams = new URLSearchParams(window.location.search);
  const searchLat =
    urlParams.get("lat") || document.getElementById("search-lat").value;
  const searchLng =
    urlParams.get("lng") || document.getElementById("search-lng").value;

  // Only initialize map if we have coordinates
  if (searchLat && searchLng) {
    // Initialize map but keep it hidden
    initializeMap();
    const latlng = L.latLng(searchLat, searchLng);
    placeMarker(latlng);
    searchMap.setView(latlng, 15);

    // Show coordinates
    updateCoordinates(parseFloat(searchLat), parseFloat(searchLng));

    // Get location name for the coordinates
    fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${searchLat}&lon=${searchLng}`
    )
      .then((response) => response.json())
      .then((data) => {
        if (data.display_name) {
          document.getElementById("location-search").value = data.display_name;
        }
      })
      .catch((error) => console.error("Error:", error));
  }
  console.log("searkdkdk");

  // Simple radius toggle functionality
  const enableRadiusCheckbox = document.getElementById("enable-radius");
  console.log("enableRadiusCheckbox", enableRadiusCheckbox);
  const radiusInputGroup = document.getElementById("radius-input-group");
  console.log("radiusInputGroup", radiusInputGroup);
  const radiusInput = document.getElementById("radius-input");
  console.log("radiusInput", radiusInput);
  const radiusHint = document.getElementById("radius-hint");
  console.log("radiusHint", radiusHint);

  if (enableRadiusCheckbox && radiusInputGroup && radiusInput && radiusHint) {
    console.log("hiiii");
    // Initialize state based on checkbox
    if (enableRadiusCheckbox.checked) {
      radiusInputGroup.style.display = "flex";
      radiusHint.style.display = "none";
    } else {
      radiusInputGroup.style.display = "none";
      radiusHint.style.display = "block";
    }

    // Toggle radius input visibility
    enableRadiusCheckbox.addEventListener("change", function () {
      if (this.checked) {
        radiusInputGroup.style.display = "flex";
        radiusHint.style.display = "none";
        radiusInput.focus();
      } else {
        radiusInputGroup.style.display = "none";
        radiusHint.style.display = "block";
        radiusInput.value = ""; // Clear the radius value when disabled
      }
    });
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
