console.log("view_listings.js loaded");

document.addEventListener("DOMContentLoaded", function () {
  // View toggle functionality
  const listViewBtn = document.getElementById("list-view-btn");
  const mapViewBtn = document.getElementById("map-view-btn");
  const listView = document.getElementById("list-view");
  const mapView = document.getElementById("map-view");
  let map;

  function parseLocation(locationString) {
    try {
      const match = locationString.match(/\[([-\d.]+),\s*([-\d.]+)\]/);
      if (match) {
        return {
          lat: parseFloat(match[1]),
          lng: parseFloat(match[2]),
          address: locationString.split("[")[0].trim(),
          location_name: locationString.split("[")[0].trim(),
        };
      }
    } catch (error) {
      console.log("Error parsing location:", error);
    }
    return {
      lat: 40.69441, // Default to NYU tandon
      lng: -73.98653,
      address: locationString || "Location not specified",
    };
  }

  function initMap() {
    if (!map) {
      map = L.map("map-view").setView([40.69441, -73.98653], 13); // Default to NYU tandon
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "© OpenStreetMap contributors",
      }).addTo(map);

      // Add markers for all listings
      const listings = document.querySelectorAll(".card");
      const bounds = [];

      listings.forEach((listing) => {
        // Get all data from data attributes
        const location = parseLocation(listing.dataset.location);
        const locationName = listing.dataset.locationName;
        const title = listing.dataset.title;
        const price = listing.dataset.price;
        const rating = parseFloat(listing.dataset.rating) || 0;

        // Create marker
        const marker = L.marker([location.lat, location.lng]).addTo(map);
        bounds.push([location.lat, location.lng]);

        // Generate stars HTML
        function generateStars(rating) {
          let starsHtml = '<div class="rating-stars">';

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

          starsHtml += "</div>";
          return starsHtml;
        }

        // Create rating HTML
        const ratingHtml = rating
          ? `<br><strong>Rating:</strong> ${generateStars(
              rating
            )} (${rating.toFixed(1)})`
          : `<br><span class="text-muted">No reviews yet ${generateStars(
              0
            )}</span>`;

        // Create popup content
        const popupContent = `
          <strong>${title}</strong><br>
          ${locationName}<br>
          $${price}/hour
          ${ratingHtml}
        `;

        marker.bindPopup(popupContent);
      });

      // Fit map to show all markers if there are any
      if (bounds.length > 0) {
        map.fitBounds(bounds);
      }
    }
  }

  function showListView() {
    mapView.classList.remove("active-view");
    listView.classList.add("active-view");
    listViewBtn.classList.add("btn-primary");
    listViewBtn.classList.remove("btn-outline-primary");
    mapViewBtn.classList.add("btn-outline-primary");
    mapViewBtn.classList.remove("btn-primary");
  }

  function showMapView() {
    listView.classList.remove("active-view");
    mapView.classList.add("active-view");
    mapViewBtn.classList.add("btn-primary");
    mapViewBtn.classList.remove("btn-outline-primary");

    // change list view button style since we are switching to map viewfd
    listViewBtn.classList.remove("btn-primary");
    listViewBtn.classList.add("btn-outline-primary");
    // remove active from list view button
    listViewBtn.classList.remove("active");

    initMap();
    if (map) {
      map.invalidateSize(); // Ensures map renders correctly
    }
  }

  // Event Listeners
  listViewBtn.addEventListener("click", showListView);
  mapViewBtn.addEventListener("click", showMapView);

  // Initialize with list view
  showListView();
});
