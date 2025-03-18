let searchMap;
let searchMarker;

document.addEventListener("DOMContentLoaded", function () {
  // Initialize search map
  searchMap = L.map("search-map").setView([40.69441, -73.98653], 13);
  L.tileLayer("https://tile.openstreetmap.bzh/ca/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors",
  }).addTo(searchMap);

  // Add click event to map
  searchMap.on("click", onMapClick);

  // Set up search functionality
  setupSearch();

  // Load existing search location if any
  const searchLat = document.getElementById("search-lat").value;
  const searchLng = document.getElementById("search-lng").value;
  if (searchLat && searchLng) {
    const latlng = L.latLng(searchLat, searchLng);
    placeMarker(latlng);
    searchMap.setView(latlng, 15);
  }
});

function onMapClick(e) {
  placeMarker(e.latlng);
  updateCoordinates(e.latlng.lat, e.latlng.lng);
}

function placeMarker(latlng) {
  if (searchMarker) {
    searchMap.removeLayer(searchMarker);
  }
  searchMarker = L.marker(latlng).addTo(searchMap);
}

function updateCoordinates(lat, lng) {
  document.getElementById("search-lat").value = lat;
  document.getElementById("search-lng").value = lng;
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
        const latlng = L.latLng(location.lat, location.lon);

        searchMap.setView(latlng, 15);
        placeMarker(latlng);
        updateCoordinates(location.lat, location.lon);
      }
    })
    .catch((error) => console.error("Error:", error));
}
