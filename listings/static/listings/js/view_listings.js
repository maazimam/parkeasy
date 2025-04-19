console.log("view_listings.js loaded");

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
let meterLayerGroup;

// Map-related functions (outside DOMContentLoaded)
function initializeMap() {
    if (!mapInitialized) {
        console.log("Initializing search map...");
        // Use our NYC-bounded map initialization instead of the original code
        searchMap = initializeNYCMap("map-view");
        currentMapView = searchMap; // Store map reference

        // Initialize layer groups
        listingLayerGroup = L.layerGroup().addTo(searchMap);
        garageLayerGroup = L.layerGroup(); // Don't add to map by default
        meterLayerGroup = L.layerGroup(); // Don't add to map by default

        // Add click event to map
        searchMap.on("click", onMapClick);

        // Add the legend to the search map
        searchMap.addControl(createMapLegend());

        // Initialize garages but don't add to map yet
        addGaragesDirectly(searchMap);

        // Initialize parking meters but don't add to map yet
        addParkingMeters(searchMap);

        mapInitialized = true;
    }
}

function setupLoadMoreButton() {
    const loadMoreBtn = document.getElementById("load-more-btn");
    if (loadMoreBtn) {
        loadMoreBtn.addEventListener("click", loadMoreListings);
    }
}

// Helper function to remove all load more buttons
function removeLoadMoreButtons() {
    // Remove button containers
    document.querySelectorAll(".text-center.my-4").forEach((container) => {
        if (container.querySelector("#load-more-btn")) {
            container.remove();
        }
    });

    // Remove any orphaned buttons
    document.querySelectorAll("#load-more-btn").forEach((button) => {
        const container =
            button.closest(".text-center.my-4") || button.parentElement;
        if (container) container.remove();
        else button.remove();
    });
}

// Simplified loadMoreListings function
function loadMoreListings() {
    const loadMoreBtn = this;
    const nextPage = loadMoreBtn.getAttribute("data-next-page");
    const listingsContainer = document.querySelector(".listings-container");

    // Show loading state
    loadMoreBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin me-2"></i>Loading...';
    loadMoreBtn.disabled = true;

    // Build URL with existing filters
    let url = new URL(window.location.href);
    url.searchParams.set("page", nextPage);
    url.searchParams.set("ajax", "1");

    fetch(url)
        .then((response) => response.text())
        .then((html) => {
            // Parse the HTML response
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, "text/html");

            // Remove any existing load more buttons
            document
                .querySelectorAll("#load-more-btn, .text-center.my-4")
                .forEach((el) => el.remove());

            // Add new listings to container
            const newListings = doc.querySelectorAll(".card");

            // Track new listings for map update
            const newListingData = [];

            newListings.forEach((listing) => {
                // Add listing to DOM
                const listingClone = listing.cloneNode(true);
                listingsContainer.appendChild(listingClone);

                // Collect data for map markers
                const lat = parseFloat(listing.dataset.lat);
                const lng = parseFloat(listing.dataset.lng);

                console.log("lat", lat);
                console.log("lng", lng);

                if (!isNaN(lat) && !isNaN(lng)) {
                    newListingData.push({
                        id: listing.dataset.id,
                        title: listing.dataset.title,
                        lat: lat,
                        lng: lng,
                        price: listing.dataset.price,
                        rating: parseFloat(listing.dataset.rating || 0),
                        locationName: listing.dataset.location || "",
                    });
                }
            });

            console.log("newListingData", newListingData);

            // Update map with new markers if map is initialized
            if (mapInitialized && newListingData.length > 0) {
                // Add new markers to the map
                newListingData.forEach((listing) => {
                    addListingMarker(listing);
                });
            }

            // Check if there are more listings
            const newLoadMoreBtn = doc.querySelector("#load-more-btn");

            if (newLoadMoreBtn) {
                // Create a new button container
                const buttonContainer = document.createElement("div");
                buttonContainer.className = "text-center my-4";

                // Clone the button from the response
                const buttonClone = newLoadMoreBtn.cloneNode(true);
                buttonClone.innerHTML = "Load More Listings";
                buttonClone.disabled = false;

                // Add the button to the container and the container to the page
                buttonContainer.appendChild(buttonClone);
                listingsContainer.appendChild(buttonContainer);

                // Add event listener to the new button
                buttonClone.addEventListener("click", loadMoreListings);
            } else {
                // No more listings to load
                const endMessage = document.createElement("div");
                endMessage.className = "text-center my-4";
                endMessage.innerHTML = "<p>No more listings to display</p>";
                listingsContainer.appendChild(endMessage);
            }
        })
        .catch((error) => {
            console.error("Error loading more listings:", error);

            // Create a retry button
            const retryContainer = document.createElement("div");
            retryContainer.className = "text-center my-4";

            const retryButton = document.createElement("button");
            retryButton.id = "load-more-btn";
            retryButton.className = "btn btn-primary";
            retryButton.setAttribute("data-next-page", nextPage);
            retryButton.textContent = "Try Again";
            retryButton.addEventListener("click", loadMoreListings);

            retryContainer.appendChild(retryButton);
            listingsContainer.appendChild(retryContainer);
        });
}

// Helper function to add a listing marker to the map
function addListingMarker(listing) {
    if (!mapInitialized) return;

    try {
        // Create the marker but add it to the layer group instead of the map
        const marker = L.marker([listing.lat, listing.lng], {
            zIndexOffset: 1000, // Higher z-index to appear above garage markers
        });

        listingLayerGroup.addLayer(marker);
        listingMarkers.push(marker);

        // Create popup content
        const ratingHtml = listing.rating ?
            `<div style="margin-bottom: 8px; display: flex; align-items: center;">
                <i class="fas fa-star" style="color: #f1c40f; margin-right: 8px;"></i>
                <span style="color: #34495e; font-size: 13px;">${listing.rating.toFixed(1)} (${generateStarRating(listing.rating)})</span>
              </div>` :
            `<div style="margin-bottom: 8px; display: flex; align-items: center;">
                <i class="fas fa-star" style="color: #bdc3c7; margin-right: 8px;"></i>
                <span style="color: #7f8c8d; font-size: 13px;">No reviews yet</span>
              </div>`;

        const popupContent = `
          <div class="listing-popup" style="padding: 8px; min-width: 200px;">
            <div style="margin-bottom: 12px;">
              <h4 style="margin: 0; color: #2c3e50; font-size: 16px;">${listing.title}</h4>
            </div>
            <div style="margin-bottom: 10px; display: flex; align-items: flex-start;">
              <i class="fas fa-map-marker-alt" style="color: #7f8c8d; margin-right: 8px; margin-top: 3px;"></i>
              <div style="color: #34495e; font-size: 13px;">${listing.locationName}</div>
            </div>
            <div style="margin-bottom: 8px; display: flex; align-items: center;">
              <i class="fas fa-tag" style="color: #7f8c8d; margin-right: 8px;"></i>
              <span style="color: #34495e; font-size: 13px;">$${Math.abs(listing.price).toFixed(2)}/hour</span>
            </div>
            ${ratingHtml}
          </div>
        `;

        marker.bindPopup(popupContent);
    } catch (error) {
        console.error("Error adding listing marker:", error);
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
    searchMarker.on("dragend", function(event) {
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

        // Optional: Update map view to center on new position
        searchMap.setView(position, searchMap.getZoom());

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


document.addEventListener("DOMContentLoaded", function() {
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
        filterHeader.addEventListener("click", function(e) {
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
        toggleFiltersBtn.addEventListener("click", function(e) {
            e.stopPropagation(); // Prevent double toggle from header click
            toggleFilterPanel();
        });
    }

    setupAdvancedFilters();
    setupRadiusToggle();
    setupDateSyncForSingleBooking();
    initializeDateRangeToggle();
    initializeEvChargerToggle();
    initializeRecurringPatternToggle();
    initializeMultipleDaysToggle();
    initializeMap();
    setMinDates();
    addListingsToMap();
    initializeLocationName();
    setupSearch();
    setupLoadMoreButton();
    initializePopover();
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
    window.addEventListener("resize", function() {
        if (searchMap) {
            searchMap.invalidateSize(true);
        }
    });

    // Handle advanced filters modal
    const applyAdvancedFiltersBtn = document.getElementById(
        "apply-advanced-filters"
    );
    if (applyAdvancedFiltersBtn) {
        applyAdvancedFiltersBtn.addEventListener("click", applyAdvancedFilters);
    }
});

function setupSearch() {
    const searchInput = document.getElementById("location-search");
    const searchButton = document.getElementById("search-location");

    if (!searchButton || !searchInput) return;

    searchButton.addEventListener("click", performSearch);
    searchInput.addEventListener("keypress", function(e) {
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