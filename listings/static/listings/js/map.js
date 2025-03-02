document.addEventListener("DOMContentLoaded", function () {
  console.log("map.js loaded");

  // Initialize the map
  let map = L.map("map").setView([43.6532, -79.3832], 13); // Default to Toronto

  // Add OpenStreetMap tiles
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "© OpenStreetMap contributors",
  }).addTo(map);

  // Initialize marker variable
  let marker;

  // Function to handle location selection
  function onMapClick(e) {
    // Remove existing marker if any
    if (marker) {
      map.removeLayer(marker);
    }

    // Add new marker
    marker = L.marker(e.latlng).addTo(map);

    // Reverse geocode the coordinates
    fetch(
      `https://nominatim.openstreetmap.org/reverse?format=json&lat=${e.latlng.lat}&lon=${e.latlng.lng}`
    )
      .then((response) => response.json())
      .then((data) => {
        const address = data.display_name;
        document.getElementById("id_location").value = address;
        marker.bindPopup(address).openPopup();
      })
      .catch((error) => console.error("Error:", error));
  }

  // Add click event to map
  map.on("click", onMapClick);

  // Search functionality
  const searchInput = document.getElementById("location-search");
  const searchButton = document.getElementById("search-location");

  function searchLocation() {
    const query = searchInput.value;

    fetch(
      `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
        query
      )}`
    )
      .then((response) => response.json())
      .then((data) => {
        if (data.length > 0) {
          const location = data[0];
          map.setView([location.lat, location.lon], 16);

          if (marker) {
            map.removeLayer(marker);
          }

          marker = L.marker([location.lat, location.lon]).addTo(map);
          document.getElementById("id_location").value = location.display_name;
          marker.bindPopup(location.display_name).openPopup();
        }
      })
      .catch((error) => console.error("Error:", error));
  }

  // Add event listeners
  searchButton.addEventListener("click", (e) => {
    e.preventDefault();
    searchLocation();
  });

  searchInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
      e.preventDefault();
      searchLocation();
    }
  });
});
console.log("map.js loaded");
console.log("mkdkkdkd");
